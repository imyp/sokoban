"""Sokoban only supported on Linux with ANSI terminal."""

from __future__ import annotations
import dataclasses
import typing
import sys
import os
import argparse
import platform
if platform.system() == "Windows":
    import msvcrt
else:
    import termios
    import tty

def get_key_linux():
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    try:
        while True:
            b = os.read(sys.stdin.fileno(), 3).decode()
            return b
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def get_key_windows():
    while True:
        if msvcrt.kbhit():
            return msvcrt.getch().decode()

get_key = get_key_linux if platform.system() != "Windows" else get_key_windows
class Cell:
    def __init__(self, symbol: str) -> None:
        self.state = CellState(symbol)
        self.connections = Connections()
    
    def is_free(self):
        return not self.state.empty and not self.state.box
    
    def is_pushable_to(self, direction: DirectionString):
        if not self.state.box:
            return False
        next_cell: PossibleCell = getattr(self.connections, direction)
        if next_cell is None or not next_cell.is_free():
            return False
        return True
    
    
PossibleCell = Cell | None
DirectionString = typing.Literal["up", "down", "left", "right"]

@dataclasses.dataclass
class Connections:
    up: PossibleCell = None
    down: PossibleCell = None
    left: PossibleCell = None
    right: PossibleCell = None

class CellState:
    """
    Mapping to and from state:

    name     binary decimal
    clear ->    000 0
    cross ->    001 1
    box ->      010 2
    player ->   100 4
    empty ->    110 6
    """
    def __init__(self, symbol: str) -> None:
        if not symbol.isnumeric():
            raise ValueError("Symbol needs to be numeric")
        symbol_ = int(symbol)
        self.cross = symbol_ in [1, 3, 5]
        self.box = symbol_ in [2, 3]
        self.player = symbol_ in [4, 5]
        self.empty = symbol_ == 6
    
    def get_symbol(self):
        return self.cross + self.box * 2 + self.player * 4 + self.empty * 6


def parse_state(state: str):
    lines = state.splitlines()
    width = len(lines[0])
    cells: list[Cell] = []
    cross_cells: list[Cell] = []
    start_cell = None
    for row, line in enumerate(lines):
        for col, symbol in enumerate(line):
            cell = Cell(symbol)
            cells.append(cell)
            if cell.state.cross:
                cross_cells.append(cell)
            if cell.state.player:
                start_cell = cell
            if row != 0:
                cell_above = cells[(row - 1) * width + col]
                cell.connections.up = cell_above
                cell_above.connections.down = cell
            if col != 0:
                cell_left = cells[row * width + col - 1]
                cell.connections.left = cell_left
                cell_left.connections.right = cell
    assert start_cell is not None
    return cells, cross_cells, start_cell

def encode_state(cells: list[Cell], width: int):
    state = ""
    for i, cell in enumerate(cells):
        col = i % width
        row = i // width
        if row != 0 and col == 0:
            state += "\n"
        state += str(cell.state.get_symbol())
    return state

class Map:
    def __init__(self, filename: str):
        self.states: list[str] = []
        with open(filename) as f:
            self.states.append(f.read())
        self.width = len(self.states[0].splitlines()[0])
        self.cells, self.cross_cells, self.start_cell = parse_state(self.states[0])
    
    def draw(self):
        BASE = "\033[{0}m"
        BLACK = BASE.format(40)
        RED = BASE.format(41)
        GREEN = BASE.format(42)
        YELLOW = BASE.format(43)
        BLUE = BASE.format(44)
        WHITE = BASE.format(47)
        RESET = BASE.format(0)
        END = "  " + RESET

        INFO = [
            "",
            f" {BLUE}{END}: Player",
            f" {RED}{END}: Box on wrong square",
            f" {GREEN}{END}: Box on target square",
            f" {YELLOW}{END}: Target square"
        ]

        for i, cell in enumerate(self.cells):
            col = i % self.width
            row = i // self.width
            if col == 0:
                print(INFO[row])
            if cell.state.box and cell.state.cross:
                print(f"{GREEN}{END}", end="")
            elif cell.state.player:
                print(f"{BLUE}{END}", end="")
            elif cell.state.cross:
                print(f"{YELLOW}{END}", end="")
            elif cell.state.box:
                print(f"{RED}{END}", end="")
            elif cell.state.empty:
                print(f"{BLACK}{END}", end="")
            else:
                print(f"{WHITE}{END}", end="")
        print("\n", end="")
    
    def check(self):
        return all(map(lambda s: s.state.box, self.cross_cells))
    
    def save(self):
        self.states.append(encode_state(self.cells, self.width))
    
    def load_last_state(self):
        if len(self.states) == 1:
            return
        self.states.pop()
        self.cells, self.cross_cells, self.start_cell = parse_state(self.states[-1])


class Player:
    def __init__(self, game_map: Map) -> None:
        self.map = game_map
        self.current = self.map.start_cell
    
    def left(self):
        return self.move("left")

    def up(self):
        return self.move("up")

    def down(self):
        return self.move("down")

    def right(self):
        return self.move("right")

    def move(self, direction: DirectionString):
        next_cell: PossibleCell = getattr(self.current.connections, direction)
        if next_cell is None:
            return
        if next_cell.is_pushable_to(direction):
            next_next: Cell = getattr(next_cell.connections, direction)
            next_cell.state.box = False
            next_next.state.box = True
        if next_cell.is_free():
            self.current.state.player = False
            self.current = next_cell
            self.current.state.player = True
            self.map.save()
    

class Sokoban:
    def __init__(self, level_filename: str) -> None:
        self.filename = level_filename
        self.map = Map(filename=self.filename)
        self.player = Player(game_map=self.map)
        self.game_loop()
    
    def game_loop(self):
        while True:
            print("\033c", end="")
            self.map.draw()
            if self.map.check():
                print("You won!")
                return
            print("h/j/k/l/b/r/q [left,down,up,right,back,restart,quit]")
            match get_key():
                case "q":
                    return
                case "h":
                    self.player.left()
                case "l":
                    self.player.right()
                case "j":
                    self.player.down()
                case "k":
                    self.player.up()
                case "r":
                    self.map = Map(filename=self.filename)
                    self.player = Player(game_map=self.map)
                case "b":
                    self.map.load_last_state()
                    self.player.current = self.map.start_cell
                case _:
                    pass

def main(level_file: str):
    Sokoban(level_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", default="level01", help="The file containing the level.")
    args = parser.parse_args()
    main(args.level)
