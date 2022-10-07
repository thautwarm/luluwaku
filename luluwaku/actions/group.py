from luluwaku.core import *
import typing


@typing.final
class Create(Effect):
    def __init__(self, emitter: Unit, name: str):
        self.emitter = emitter
        self.name = name

    def on_step(self) -> bool:
        if self.name in GameState.groups:
            GameState.log(f"队伍【{self.name}】已成立，创建失败", self.emitter.uname)
            return False
        Group.leave(self.emitter)
        Group(self.emitter, self.name)
        return False


@typing.final
class Leave(Effect):
    def __init__(self, emitter: Unit):
        self.emitter = emitter

    def on_step(self) -> bool:
        Group.leave(self.emitter)
        return False


@typing.final
class Join(Effect):
    def __init__(self, emitter: Unit, name: str):
        self.emitter = emitter
        self.name = name
        self.agreed: typing.Literal["pending", "refused", "agreed"] = "pending"

    def on_step(self) -> bool:
        if self.name not in GameState.groups:
            GameState.log(f"队伍【{self.name}】不存在，加入失败", self.emitter.uname)
            return False
        if self.agreed == "pending":
            return True
        if self.agreed == "refused":
            return False
        if self.agreed != "agreed":
            GameState.log(f"队伍【{self.name}】加入失败，未知错误", self.emitter.uname)
            return False
        Group.leave(self.emitter)
        g = GameState.groups[self.name]
        Group.join(self.emitter, g)
        return False


@typing.final
class ResponseJoin(Effect):
    def __init__(self, emitter: Unit, name: str, requester: str, agreed: bool):
        self.emitter = emitter
        self.name = name
        self.agreed = agreed
        self.requester = requester

    def on_step(self) -> bool:
        if self.name not in GameState.groups:
            GameState.log(f"队伍【{self.name}】不存在，处理失败", self.emitter.uname)
            return False
        group = GameState.groups[self.name]
        if self.emitter is not group.owner:
            GameState.log(f"不是队伍【{self.name}】的队长，无法处理申请", self.emitter.uname)
            return False

        def cond(e: Effect) -> bool:
            if not isinstance(e, Join):
                return False
            if e.name != self.name:
                return False
            if e.emitter.uname != self.requester:
                return False
            return True

        for eff in GameState.matching_effects(cond):
            typing.cast(Join, eff).agreed = "agreed" if self.agreed else "refused"
            break
        return False
