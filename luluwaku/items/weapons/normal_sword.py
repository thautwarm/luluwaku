from __future__ import annotations
from weakref import WeakKeyDictionary
from luluwaku.core import *
from luluwaku.items.weapon import Weapon

STR_factor = 0.9
STR_const = 2
DEX_factor = 0.1
DIST = 4.7


@typing.final
class NormalSword(Weapon):
    def __init__(self, level: int) -> None:
        self.level = level
        self.weight = 1 + int(level // 2)
        self.previous_ATK_DIST = 0

    def on_equipped(self, unit: Unit):
        board = unit[Board]
        board.apply_STR(board.STR + STR_const + STR_factor * self.level)
        board.apply_DEX(board.DEX + DEX_factor * self.level)
        self.previous_ATK_DIST = board.ATTACK_DIST

    def on_unequipped(self, unit: Unit):
        board = unit[Board]
        board.apply_STR(board.STR - STR_const - STR_factor * self.level)
        board.apply_DEX(board.DEX - DEX_factor * self.level)
        board.apply_ATTACK_DIST(self.previous_ATK_DIST)

    def get_name(self) -> str:
        return f"铁剑{self.level}"
