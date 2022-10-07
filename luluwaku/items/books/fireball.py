from __future__ import annotations
from luluwaku.core import *
from luluwaku.items.book import Book


def skill_dist(level: float):
    return 7.2 + level * 0.3


@typing.final
class FireBall(Skill):
    casting_consumption: int = 1

    def name(self) -> str:
        return "火球术"

    def cast(self, emitter: Unit, target: Entity | None) -> Effect | None:
        if (
            target
            and (targetUnit := target.get_component(Unit))
            and (level := emitter[Caster].level(self))
        ):
            emitterBoard = emitter[Board]
            emitter[Caster].level_up(self, 1 / (1.9 ** (0.01 + level)))
            eff = AttackEffect(
                emitter,
                targetUnit,
                lambda _, __: Damage(
                    focus=0.5 * emitterBoard.SPR + level + 0.22 * emitterBoard.INT,
                    magical_damage=0.18 * emitterBoard.SPR
                    + 2 * level
                    + 0.32 * emitterBoard.INT,
                ),
                skill_dist(level),
                aoe=1,
            )
            return eff
        return None


@typing.final
class RudiFireBook(Book):
    def condition(self, src: Unit):
        board = src[Board]
        return board.MP > 5 and board.INT > 5 and board.SPR > 5

    def get_name(self) -> str:
        return "初级火球术"

    def imply(self, src: Unit) -> Skill:
        return FireBall()
