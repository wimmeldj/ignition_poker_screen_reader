import multiprocessing as mp
import numpy as np
from functools import partial
import time

from config import *
from classes.CashGameState import CashGameState
from classes.Player import Player

if not DEBUG:
    from PIL import ImageGrab
    import win32gui


# TODO: improve grabScreens method. Make so we can get a screenshot of a particular table by hwnd
def grab_screens() -> dict:
    if DEBUG:
        ret = {}
        for i, f in enumerate(Path("test_tables").glob("*")):
            img = cv2.imread(str(f))
            ret["$0.00/$0.00 " + str(i)] = img
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


# TODO: Need more templates so that we can compare table at any state.
# TODO: Specifically, 6handed with button and spotlight, heads up with button, heads up with spotlight
# takes a table screenshot and returns its handedness
def get_handedness(img_gray) -> int:
    # need to compare largest templates first to avoid incorrect matching
    heads_up_crop = img_gray[410:410 + 28, 270:270 + 282]
    for t in HEADS_UP_TEMPLATES:
        if np.array_equal(t, heads_up_crop):
            return 2
    six_crop = heads_up_crop
    for t in SIX_HANDED_TEMPLATES:
        if np.array_equal(t, six_crop):
            return 6
    nine_crop = img_gray[410:410 + 29, 321:321 + 181]
    for t in NINE_HANDED_TEMPLATES:
        if np.array_equal(t, nine_crop):
            return 9
    return None


# uses tesseract for ocr. Parses an image to string
def ocr(img, x_scale=1, y_scale=1, config="") -> str:
    img = cv2.resize(img, None, fx=x_scale, fy=y_scale)
    return pt.image_to_string(img, config=config)


# ocr but for multiprocessing. Additionally expects a tuple of form (unique_id, img_to_process)
def para_ocr(x_scale=1, y_scale=1, config="", id_and_img=()) -> tuple:
    id, img = id_and_img
    img = cv2.resize(img, None, fx=x_scale, fy=y_scale, interpolation=cv2.INTER_CUBIC)
    ocr_str = pt.image_to_string(img, config=config)
    ret = (id, ocr_str)
    return ret


def populate_players(g):
    """
    For the given CashGameState, g, creates Player objects for each player found. For each player, sets seat_num,
    is_hero, and stack. These players are added to g's players dictionary.
    """
    screen = g.current_screen

    # First find hero's seat number.
    if g.handedness == 6:
        x, y, w, h = 350, 472, 22, 18
        # crop current screen to hero's seat number
        hero_seat_num_img = screen[y:y+h, x:x+w]
        hero_seat_num = ocr(img=hero_seat_num_img, config="-psm 10 -c tessedit_char_whitelist=123456")
    elif g.handedness == 9:
        x, y, w, h = 453, 472, 22, 18
        hero_seat_num_img = screen[y:y + h, x:x + w]
        hero_seat_num = ocr(img=hero_seat_num_img, config="-psm 10 -c tessedit_char_whitelist=123456789")
    elif g.handedness == 2:
        x, y, w, h = 349, 465, 22, 18
        hero_seat_num_img = screen[y:y + h, x:x + w]
        hero_seat_num = ocr(img=hero_seat_num_img, config="-psm 10 -c tessedit_char_whitelist=12")
    else:
        raise RuntimeError

    if len(hero_seat_num) == 1:
        hero_seat_num = int(hero_seat_num)
    else:
        raise RuntimeError

    # add hero to g's players dict
    g.players[hero_seat_num] = Player(seat_num=hero_seat_num, is_hero=True)
    # add other players to dict
    for other_seat_num in [_ for _ in range(1, g.handedness + 1) if _ != hero_seat_num]:
        g.players[other_seat_num] = Player(seat_num=other_seat_num, is_hero=False)

    seat_nums = [_ for _ in range(1, g.handedness + 1)]
    offset = -1
    seats_and_stack_imgs = []
    # parses the stack sizes for players in game_state g
    if g.handedness == 6:
        for _ in range(0, len(seat_nums)):
            seat_num = seat_nums[(hero_seat_num + offset) % g.handedness]
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
            stack_img = screen[y:y+h, x:x+w]
            seats_and_stack_imgs.append((seat_num, stack_img))
            offset += 1
    elif g.handedness == 9:
        for _ in range(0, len(seat_nums)):
            seat_num = seat_nums[(hero_seat_num + offset) % g.handedness]
            w, h = 101, 26
            if offset == -1:
                x, y = 341, 468
            elif offset == 0:
                x, y = 196, 455
            elif offset == 1:
                x, y = 71, 339
            elif offset == 2:
                x, y = 88, 198
            elif offset == 3:
                x, y = 265, 130
            elif offset == 4:
                x, y = 457, 130
            elif offset == 5:
                x, y = 637, 198
            elif offset == 6:
                x, y = 652, 339
            elif offset == 7:
                x, y = 530, 455
            stack_img = screen[y:y+h, x:x+w]
            seats_and_stack_imgs.append((seat_num, stack_img))
            offset += 1
    elif g.handedness == 2:
        for _ in range(0, len(seat_nums)):
            seat_num = seat_nums[(hero_seat_num + offset) % g.handedness]
            w, h = 101, 26
            if offset == -1:
                x, y = 384, 460
            elif offset == 0:
                x, y = 384, 140
            stack_img = screen[y:y+h, x:x+w]
            seats_and_stack_imgs.append((seat_num, stack_img))
            offset += 1

    # once we have all the stack images corresponding to a seat, we parallel process them
    para_ocr_partial = partial(para_ocr, 20, 20, "-psm 8 tessedit_char_whitelist=0123456789$.")
    pool = mp.Pool(6)
    seats_and_parsed_stacks = pool.map(para_ocr_partial, seats_and_stack_imgs)

    for seat_num, stack in seats_and_parsed_stacks:
        matches = re.findall(MONEY_P, stack)
        try:
            g.players[seat_num].stack = float(matches[0])
        except IndexError:
            # if a stack image parsed by ocr does not match MONEY_P, we assume there isn't a player in that position
            g.players[seat_num].is_empty = True
            g.players[seat_num].stack = 0
    return


# Updates current_screen of each game_state
def update_screens():
    screens = grab_screens()
    for title, screen in screens.items():
        table_id = re.findall(TABLE_ID_P, title)[0]
        game_states[table_id].current_screen = screen
    return


def init():
    """
    Called on startup. Responsible for initializing of game_state objects
    :param interval_time:
    :return:
    """
    screens = grab_screens()
    while screens is None or None in screens:
        screens = grab_screens()
        time.sleep(interval_time)

    for title, screen in screens.items():
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        handedness = get_handedness(screen_gray)
        table_id = re.findall(TABLE_ID_P, title)[0]
        sb, bb = re.findall(STAKE_P, title)[0]
        sb = float(sb)
        bb = float(bb)
        game_states[table_id] = CashGameState(handedness=handedness, table_id=table_id, bb_size=bb, sb_size=sb,
                                              current_screen=screens[title])

    # for each CashGameState, get seat_nums and stacks of players
    for g in game_states.values():
        populate_players(g)
    return


if __name__ == "__main__":
    mp.set_start_method('spawn')  # to imitate Windows environment
    game_states = {}
    init()

    if DEBUG:
        for g in game_states.values():
            print(f"STAKE: {g.bb_size}/{g.sb_size} HANDEDNESS: {g.handedness}")
            for p in g.players.values():
                if not p.is_empty:
                    print(f"SEAT: {p.seat_num} | IS HERO: {p.is_hero} | STACK: {p.stack}")
                else:
                    print(f"SEAT {p.seat_num} is EMPTY {p.is_empty}")




