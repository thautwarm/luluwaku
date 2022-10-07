from __future__ import annotations
from luluwaku.core import *


class Drug(Item):
    @abc.abstractmethod
    def use(self, src: Unit) -> Effect:
        raise NotImplementedError

    def on_activated(self, unit: Unit, _):
        bag = unit[Bag]
        bag.remove_item(self)
        eff = self.use(unit)
        eff.submit()
        return True
