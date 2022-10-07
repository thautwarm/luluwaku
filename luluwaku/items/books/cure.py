from __future__ import annotations
from luluwaku.core import *
from luluwaku.items.book import Book


@typing.final
class CureEffect(Effect):
    left_heal: float
    each_heal: float
    target: Unit

    def __init__(self, target: Unit, total_heal: float, each_heal: float):
        self.target = target
        self.left_heal = total_heal
        self.each_heal = each_heal

    def on_step(self) -> bool:
        board = self.target[Board]
        if self.left_heal > self.each_heal:
            board.apply_HP(board.HP + self.each_heal)
            self.left_heal -= self.each_heal
            return True
        board.apply_HP(board.HP + self.left_heal)
        self.left_heal = 0
        return False


def skill_distance(level: float):
    return 10 + level * 0.35


@typing.final
class Cure(Skill):
    casting_consumption: int = 2

    def __init__(self):
        pass

    def name(self) -> str:
        return "治疗"

    def cast(self, emitter: Unit, target: Entity | None) -> Effect | None:
        if (
            target
            and (targetUnit := target.get_component(Unit))
            and (level := emitter[Caster].level(self))
        ):
            if emitter[Positional].compute_distance(
                targetUnit[Positional]
            ) > skill_distance(level):
                GameState.log(f"目标距离过远，施法未能命中", emitter.uname)
                return None
            board = targetUnit[Board]
            r = get_ratio(level + 0.1 * board.SPR + 0.9 * board.INT)
            heal_val = 2 * level + 0.5 * board.INT * r
            each_heal = level + 0.5 * board.INT * r / 2
            emitter[Caster].level_up(self, 1 / (2 ** (0.01 + level)))
            return CureEffect(targetUnit, heal_val, each_heal)
        return None


@typing.final
class PasterBook(Book):
    def condition(self, src: Unit):
        board = src[Board]
        if board.MP > 5 and board.INT > 3 and board.SPR > 3:
            return True

    def get_name(self) -> str:
        return "牧师基础"

    def imply(self, src: Unit) -> Skill:
        return Cure()
