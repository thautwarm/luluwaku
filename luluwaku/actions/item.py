from __future__ import annotations
from luluwaku.core import *

# TODO
def search_item_by_name(unit: Unit, itemname: str) -> Item | None:
    raise NotImplementedError


@typing.final
class Activate(Effect):
    def __init__(self, emitter: Unit, item: Item, target: Entity):
        self.emitter = emitter
        self.item = item
        self.target = target

    def on_step(self) -> bool:
        if not self.emitter[Bag].has_item(self.item):
            GameState.log(f"物品【{self.item.name}】不在背包中，无法使用", self.emitter.uname)
            return False
        if self.emitter[Board].consume_efforts(self.item.activation_consumption):
            self.item.on_activated(self.emitter, self.target)

        return False


@typing.final
class Deactivate(Effect):
    def __init__(self, emitter: Unit, item: Item):
        self.emitter = emitter
        self.item = item

    def on_step(self) -> bool:
        if not self.emitter[Bag].has_item(self.item):
            GameState.log(f"物品【{self.item.name}】不在背包中，无法停用", self.emitter.uname)
            return False
        self.item.on_deactivated(self.emitter)
        return False
