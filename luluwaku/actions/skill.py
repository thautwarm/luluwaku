from __future__ import annotations
from luluwaku.core import *


class Cast:
    def __init__(self, emitter: Unit, skill: Skill, target: Entity | None):
        self.emitter = emitter
        self.skill = skill
        self.target = target

    def on_step(self) -> bool:
        if not self.emitter[Caster].has_skill(self.skill):
            GameState.log(f"技能【{self.skill.name}】未学习，无法使用", self.emitter.uname)
            return False
        if self.emitter[Board].consume_efforts(self.skill.casting_consumption):
            effect = self.skill.cast(self.emitter, self.target)
            if effect:
                effect.submit()
        return False
