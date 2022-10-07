from __future__ import annotations
from luluwaku.core import *


class Weapon(Item):
    is_equipped: bool = False

    @abc.abstractmethod
    def on_equipped(self, unit: Unit):
        raise NotImplementedError

    @abc.abstractmethod
    def on_unequipped(self, unit: Unit):
        raise NotImplementedError

    def on_activated(self, src: Unit, dst):
        bag = src[Bag]

        equipped_weapon = None

        for item in bag.all_items():
            if item is self:
                continue
            if isinstance(item, Weapon) and item.is_equipped:
                equipped_weapon = item
                break

        if equipped_weapon:
            equipped_weapon.on_unequipped(src)

        if not self.is_equipped:
            self.is_equipped = True
            self.on_equipped(src)
            GameState.log(
                f"物品【{self.name}】已激活",
                src.uname,
            )
            return True
        return False

    def on_deactivated(self, unit: Unit):
        if self.is_equipped:
            self.is_equipped = False
            self.on_unequipped(unit)
            GameState.log(
                f"物品【{self.name}】已取消",
                unit.uname,
            )
            return True
        return False
