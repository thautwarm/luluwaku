from __future__ import annotations
from luluwaku.core import *


class Book(Item):
    @abc.abstractmethod
    def imply(self, src: Unit) -> Skill:
        raise NotImplementedError

    @abc.abstractmethod
    def condition(self, src: Unit):
        raise NotImplementedError

    def on_activated(self, unit: Unit, dst: Entity):
        if not self.condition(unit):
            return False
        skill = self.imply(unit)
        if unit[Caster].learn(skill):
            unit[Bag].remove_item(self)
            return True
        return False
