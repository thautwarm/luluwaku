from luluwaku.core import *


def _create_normal_atk(emitter: Unit, target: Unit):
    board = emitter[Board]
    focus = 1 + board.DEX * 0.3 + board.CHR * 0.1 + board.SPR * 0.6
    physical_damage = 1 + board.STR * 0.8 + board.CON * 0.1 + board.DEX * 0.6
    return Damage(
        focus=focus,
        physical_damage=physical_damage,
    )


class NormalAttack(Effect):
    def __init__(self, emitter: Unit, target: Unit):
        self.emitter = emitter
        self.target = target

    def on_step(self) -> bool:
        if not self.emitter[Board].consume_efforts(2):
            return False
        AttackEffect(
            self.emitter,
            self.target,
            _create_normal_atk,
            distance=self.emitter[Board].ATTACK_DIST,
            aoe=0,
        ).submit()
        return False
