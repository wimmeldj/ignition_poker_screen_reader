class Player:
    def __init__(self, seat_no: int, is_hero: bool):
        self.seat_no: int = seat_no
        self.is_hero = is_hero

        self.stack: float = None
        self.position: str = None

        self.call_count: int = 0
        self.raise_count: int = 0
        self.fold_count: int = 0
        self.avg_bet_size: float = 0
        self.avg_call_size: float = 0

        self.fold_magn: float = 0
        self.call_magn: float = 0
        self.raise_magn: float = 0

        # derived like call raise ratio fold call ratio, etc
        self.fc_ratio = 0
        self.rc_ratio = 0
        self.avg_pot_folded = 0

    def set_stack(self, amount):
        self.stack = amount

    def update_stack(self, amount):
        self.stack += amount

    # TODO: implement other relevant player functions
