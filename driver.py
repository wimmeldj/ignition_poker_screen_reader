import time
import cv2
import re
import numpy as np
import multiprocessing as mp

from config import *
DEBUG = CONFIG["DEBUG"]

if not DEBUG:
    from PIL import ImageGrab
    import win32gui

from classes.CashGameState import CashGameState
from classes.Player import Player


# TODO: improve grabScreens method.
def grab_screens() -> dict:
    table_id_p = re.compile(r" (\d*?)$")
    stake_p = re.compile(r"^\$(.*?)\/\$(.*?) ")
    if DEBUG:
        ret = {}
        for i, f in enumerate(Path("test_tables").glob("*")):
            img = cv2.imread(str(f))
            ret["$0.02/$0.05 " + str(i)] = img
        return ret

    else:
        toplist, winlist = [], []

        def enum_cb(hwnd, results):
            winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_cb, toplist)
        search_results = [(hwnd, title) for hwnd, title in winlist if '$0.02/$0.05' in title.lower() or
                          '$0.05/$0.10' in title.lower() or
                          '$0.10/$0.25' in title.lower() or
                          '$0.25/$0.50' in title.lower() or
                          '$0.50/$1.00' in title.lower() or
                          '$1.00/$2.00' in title.lower() or
                          '$2.50/$5.00' in title.lower() or
                          '$5.00/$10.00' in title.lower() or
                          '$10.00/$20.00' in title.lower()]
        ret = {}
        for result in search_results:
            hwnd = result[0]
            title = result[1]
            bbox = win32gui.GetWindowRect(hwnd)
            img = np.array(ImageGrab.grab(bbox))
            img = img[:, :, ::-1]  # rgb to bgr
            ret[str(title) + str(hwnd)] = img

        if len(ret) > 0:
            return ret
        else:
            return None


# returns the closure get_handedness() which parses a table image and returns the matched handedness
def hand_getter(path):
    templates = []
    for f in path.glob('*'):
        templates.append(cv2.imread(str(f), cv2.IMREAD_GRAYSCALE))

    def get_handedness(img_gray, img_rgb) -> int:
        for e, t in enumerate(templates):
            w,h = t.shape[::-1]
            res = cv2.matchTemplate(img_gray, t, cv2.TM_CCOEFF_NORMED)
            threshold = 0.98
            loc = np.where(res >= threshold)
            if loc[0].size != 0:
                if e in range(0,6):
                    return 6  # six-handed
                elif e in range(6,12):
                    return 9  # nine-handed
                elif e == 12:
                    return 2  # heads-up
                else:
                    return -1  # error

    return get_handedness


# uses tesseract for ocr. Expects an image, scaling factors, and a tesseract config string
def ocr(img, x_scale=1, y_scale=1, config="") -> str:
    if x_scale != 1 and y_scale != 1:
        img = cv2.resize(img, None, fx=x_scale, fy=y_scale)
    return pt.image_to_string(img, config=config)


# ocr but for multiprocessing. Adds a tuple of form (id, ocr_str) to queue
def para_ocr(queue, id, img, x_scale=1, y_scale=1, config=""):
    ocr_str = ocr(img=img, x_scale=x_scale, y_scale=y_scale, config=config)
    queue.put((id, ocr_str))


# TODO: Note, if this function is parallelized, we can't actually modify the g's players dict.
def populate_players(g: CashGameState):
    """
    For the given CashGameState, g, populates g's players dictionary with players keyed by their seat number.
    Also parses the stack sizes for each of these players and updates g's players dictionary.
    """
    money_p = re.compile("^\$(\d*?\.\d\d)$")
    x, y, w, h = 0, 0, 0, 0
    screen = g.current_screen
    hero_seat_num_img = None
    hero_seat_num = None
    # TODO: implement other handedness offsets
    # First find hero's seat number.
    if g.handedness == 6:
        x, y, w, h = 350, 472, 22, 18
        # crop current screen to hero's seat number
        hero_seat_num_img = screen[y:y+h, x:x+w]
        hero_seat_num = ocr(img=hero_seat_num_img, config="-psm 10 -c tessedit_char_whitelist=123456")
    elif g.handedness == 9:
        x, y, w, h = 0, 0, 0, 0
        hero_seat_num_img = screen[y:y + h, x:x + w]
        hero_seat_num = ocr(img=hero_seat_num_img, config="-psm 10 -c tessedit_char_whitelist=123456789")
    elif g.handedness == 2:
        x, y, w, h = 0, 0, 0, 0
        hero_seat_num_img = screen[y:y + h, x:x + w]
        hero_seat_num = ocr(img=hero_seat_num_img, config="-psm 10 -c tessedit_char_whitelist=12")
    else:
        raise RuntimeError

    if len(hero_seat_num) == 1:
        hero_seat_num = int(hero_seat_num)
    else:
        raise RuntimeError

    # add hero to g's players dict
    g.players[hero_seat_num] = Player(hero_seat_num, True)
    # add other players to dict
    for other_seat_num in [_ for _ in range(1, g.handedness + 1) if _ != hero_seat_num]:
        g.players[other_seat_num] = Player(other_seat_num, False)

    seat_nums = [_ for _ in range(1, g.handedness + 1)]
    offset = -1
    queue = mp.Queue()
    processes = []
    # parses the stack sizes for players in game_state g
    if g.handedness == 6:
        for _ in range(0, len(seat_nums)):
            seat_num = seat_nums[(hero_seat_num + offset) % 6]
            w, h = 101, 26
            if offset == -1:  # corresponds to position of hero
                x, y = 383, 469
            elif offset == 0:  # corresponds to position of player 1 left of hero
                x, y = 84, 393
            elif offset == 1:  # 2 left of hero ...
                x, y = 84, 213
            elif offset == 2:
                x, y = 343, 130
            elif offset == 3:
                x, y = 638, 213
            elif offset == 4:
                x, y = 638, 394  # ... 1 right of hero
            offset += 1
            stack_img = screen[y:y+h, x:x+w]

            try:
                if __name__ == "__main__":
                    # mp.set_start_method("spawn")  # sets multiprocessing's start method to behave as if on Windows
                    p = mp.Process(target=para_ocr, args=(queue, seat_num, stack_img, 10, 10,
                                                          "-psm 8 -c tessedit_char_whitelist=0123456789.$"))
                    processes.append(p)
                    p.start()
            except RuntimeError:
                pass

    # if __name__ == "__main__":
        for p in processes:
            p.join()
    queue.put(-1)  # sentinel to mark end

    for seat_num, stack in iter(queue.get, -1):
        matches = re.findall(money_p, stack)
        g.players[seat_num].set_stack(float(matches[0]))


def init(interval_time):
    """
    Called on startup. Responsible for initializing of game_state objects
    :param interval_time:
    :return:
    """
    screens = grab_screens()
    while screens is None:
        screens = grab_screens()
        time.sleep(interval_time)

    match_counts = {k: 0 for k in screens.keys()}
    handedness_comparisons = {k: -1 for k in screens.keys()}

    while True:
        if min(match_counts.values()) < 6:
            screens = grab_screens()

            for title, screen in screens.items():
                screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                handedness = get_handedness(screen_gray, screen)
                # we only compare if the comparison is not currently an error
                if handedness_comparisons[title] != -1:
                    if handedness_comparisons[title] == handedness:
                        match_counts[title] += 1
                    else:
                        match_counts[title] -= 3
                handedness_comparisons[title] = handedness
        else:
            table_id_p = re.compile(r" (\d*?)$")
            stake_p = re.compile(r"^\$(.*?)\/\$(.*?) ")

            # Add each GameState to game_states with key of table_id
            for title in screens.keys():
                table_id = re.findall(table_id_p, title)[0]
                sb, bb = re.findall(stake_p, title)[0]
                sb = float(sb)
                bb = float(bb)
                game_states[table_id] = CashGameState(handedness=handedness_comparisons[title], table_id=table_id,
                                                      bb_size=bb, sb_size=sb, current_screen=screens[title])

            for g in game_states.values():
                populate_players(g)
            break


get_handedness = hand_getter(CONFIG["TABLE_PATTERNS_PATH"])
game_states = {}
init(0.1)

if DEBUG:
    for g in game_states.values():
        print(f"STAKE: {g.bb_size}/{g.sb_size} HANDEDNESS: {g.handedness}")
        for p in g.players.values():
            print(f"SEAT: {p.seat_no} | IS HERO: {p.is_hero} | STACK: {p.stack}")




