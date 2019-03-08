class CashGameState:
    def __init__(self, handedness: int, table_id: str, bb_size: float, sb_size: float, current_screen):
        self.handedness: int = handedness
        self.table_id: str = table_id
        self.bb_size: float = bb_size
        self.sb_size: float = sb_size
        self.current_screen = current_screen
        self.players: dict = {}

    def set_players(self, players: dict):
        self.players: dict = players

    def set_current_screen(self, screen):
        self.current_screen = screen
