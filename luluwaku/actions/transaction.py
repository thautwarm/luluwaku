from __future__ import annotations
from luluwaku.core import *
import uuid

from luluwaku.core import _GameStateType


class Data:
    money: int
    items: set[Item]


# TODO
def create_ticket_id(g: _GameStateType) -> str:
    return str(uuid.uuid4())


class Cancel(Effect):
    emitter: Unit
    ticket_id: str

    def __init__(self, emitter: Unit, ticket_id: str):
        self.emitter = emitter
        self.ticket_id = ticket_id

    def on_step(self) -> bool:
        transacs = GameState.matching_effects(
            lambda eff: isinstance(eff, Create) and eff.ticket_id == self.ticket_id
        )
        for transac in transacs:
            transac = typing.cast(Create, transac)
            transac.cancelled = True
            GameState.log(
                f"交易【{transac.ticket_id}】已取消",
                transac.emitter.uname,
                transac.target.uname,
            )
            break
        return False


class Shake(Effect):
    emitter: Unit
    ticket_id: str

    def __init__(self, emitter: Unit, ticket_id: str):
        self.emitter = emitter
        self.ticket_id = ticket_id

    def on_step(self) -> bool:
        transacs = GameState.matching_effects(
            lambda eff: isinstance(eff, Create) and eff.ticket_id == self.ticket_id
        )
        for transac in transacs:
            transac = typing.cast(Create, transac)
            if transac.emitter is self.emitter:
                transac.shaked_by_emitter = True
                GameState.log(
                    f"交易【{transac.ticket_id}】被甲方确认",
                    transac.emitter.uname,
                    transac.target.uname,
                )
            elif transac.target is self.emitter:
                transac.shaked_by_target = True
                GameState.log(
                    f"交易【{transac.ticket_id}】被乙方确认",
                    transac.emitter.uname,
                    transac.target.uname,
                )
            return False
        return False


class ModMoney(Effect):
    ticket_id: str
    emitter: Unit
    money: int
    ask_other: bool

    def __init__(self, emitter: Unit, money: int, ask_other: bool = True):
        self.ticket_id = create_ticket_id(GameState)
        self.emitter = emitter
        self.money = money
        self.ask_other = ask_other

    def on_step(self) -> bool:
        transacs = GameState.matching_effects(
            lambda eff: isinstance(eff, Create) and eff.ticket_id == self.ticket_id
        )
        for transac in transacs:
            transac = typing.cast(Create, transac)
            if transac.emitter == self.emitter:
                data = self.ask_other and transac.cost or transac.gain
            elif transac.target == self.emitter:
                data = self.ask_other and transac.gain or transac.cost
            else:
                break
            data.money = self.money
            GameState.log(
                f"交易【{transac.ticket_id}】金额设置为 {data.money}", self.emitter.uname
            )
            break

        return False


class ModItem(Effect):
    ticket_id: str
    emitter: Unit
    item: Item
    modifier: typing.Literal["add", "remove"]
    ask_other: bool

    def __init__(
        self,
        emitter: Unit,
        ticket_id: str,
        item: Item,
        modifier: typing.Literal["add", "remove"],
        ask_other: bool = False,
    ):
        self.ticket_id = ticket_id
        self.emitter = emitter
        self.item = item
        self.modifier = modifier
        self.ask_other = ask_other

    def on_step(self) -> bool:
        transacs = GameState.matching_effects(
            lambda eff: isinstance(eff, Create) and eff.ticket_id == self.ticket_id
        )

        for transac in transacs:
            transac = typing.cast(Create, transac)
            if transac.emitter == self.emitter:
                data = self.ask_other and transac.cost or transac.gain
            elif transac.target == self.emitter:
                data = self.ask_other and transac.gain or transac.cost
            else:
                break
            if self.modifier == "add":
                data.items.add(self.item)
                GameState.log(
                    f"交易【{transac.ticket_id}】添加物品 {self.item.name}", self.emitter.uname
                )
            elif self.modifier == "remove":
                data.items.discard(self.item)
                GameState.log(
                    f"交易【{transac.ticket_id}】移除物品 {self.item.name}", self.emitter.uname
                )
            break
        return False


class Create(Effect):
    emitter: Unit
    target: Unit
    ticket_id: str
    cost: Data
    gain: Data
    shaked_by_emitter: bool = False
    shaked_by_target: bool = False
    cancelled: bool = False

    def __init__(self, emitter: Unit, target: Unit, cost: Data, gain: Data):
        self.emitter = emitter
        self.target = target
        self.cost = cost
        self.gain = gain
        self.ticket_id = create_ticket_id(GameState)

        if not target[Board].alive:
            self.shaked_by_target = True

    def on_step(self) -> bool:
        if self.cancelled:
            return False

        if not self.shaked_by_target or not self.shaked_by_emitter:
            return True

        emitterBag = self.emitter[Bag]
        targetBag = self.target[Bag]

        if emitterBag.money < self.cost.money:
            GameState.log(
                f"交易失败，{self.emitter.uname}的金钱不足", self.emitter.uname, self.target.uname
            )
            return False

        if targetBag.money < self.gain.money:
            GameState.log(
                f"交易失败，【{self.target.uname}】的金钱不足",
                self.emitter.uname,
                self.target.uname,
            )
            return False

        cost_items = self.cost.items
        gain_items = self.gain.items

        for item in gain_items:
            if not targetBag.has_item(item):
                GameState.log(
                    f"交易失败，【{self.target.uname}】没有物品【{item.name}】",
                    self.emitter.uname,
                    self.target.uname,
                )
                return False

        for item in cost_items:
            if not emitterBag.has_item(item):
                GameState.log(
                    f"交易失败，【{self.emitter.uname}】没有物品【{item.name}】",
                    self.emitter.uname,
                    self.target.uname,
                )
                return False

        emitterBag.add_money(self.gain.money)
        emitterBag.remove_money(self.cost.money)

        targetBag.add_money(self.cost.money)
        targetBag.remove_money(self.gain.money)

        for item in cost_items:
            if emitterBag.remove_item(item):
                targetBag.add_item(item)

        for item in gain_items:
            if targetBag.remove_item(item):
                emitterBag.add_item(item)

        GameState.log(f"交易【{self.ticket_id}】成功", self.emitter.uname, self.target.uname)
        return False
