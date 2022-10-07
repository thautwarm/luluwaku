from __future__ import annotations
from collections import deque
import math
import typing
import typing_extensions
import abc
import array
import random
from dataclasses import dataclass

## Functional lists

_R = typing.TypeVar("_R")
Step = typing.Generator[int, bool, _R]


class PList(abc.ABC, typing.Sequence[_R]):
    @property
    @abc.abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def split(self) -> tuple[_R, PList[_R]] | None:
        raise NotImplementedError

    @staticmethod
    def cons(head: _R, tail: PList[_R]) -> PList[_R]:
        return PCons(head, tail)

    @staticmethod
    def remove(x: _R, lst: PList[_R]) -> PList[_R]:
        if isinstance(lst, PCons):
            if lst.head == x:
                return lst.tail
            else:
                return PList.cons(lst.head, PList.remove(x, lst.tail))
        else:
            return lst

    @staticmethod
    def empty(t: typing.Type[_R]) -> PList[_R]:
        return PNil()

    @staticmethod
    def empty_cov() -> PList[typing.Any]:
        return PNil()

    @staticmethod
    def of(arg: typing.Iterable[_R]) -> PList[_R]:
        arg = reversed(list(arg))
        x = PNil()
        for each in arg:
            x = PCons(each, x)
        return x

    @staticmethod
    def create(*args: _R) -> PList[_R]:
        return PList.of(args)

    def __contains__(self, value: object) -> bool:
        for e in self:
            if e == value:
                return True
        return False

    def count(self, value: _R) -> int:
        c = 0
        for each in self:
            if each == value:
                c += 1
        return c


@dataclass(frozen=True, order=True)
class PNil(PList[_R]):
    @property
    def is_empty(self) -> bool:
        return True

    def split(self) -> tuple[_R, PList[_R]] | None:
        return None

    def __len__(self) -> int:
        return 0

    def __getitem__(self, item: int) -> _R:
        raise IndexError

    def __iter__(self) -> typing.Iterator[_R]:
        return iter(())


@dataclass(frozen=True, order=True)
class PCons(PList[_R]):
    head: _R
    tail: PList[_R]

    @property
    def is_empty(self) -> bool:
        return False

    def split(self) -> tuple[_R, PList[_R]] | None:
        return self.head, self.tail

    def __len__(self) -> int:
        n = 0
        x = self
        while isinstance(x, PCons):
            n += 1
            x = x.tail
        return n

    def __getitem__(self, item: int) -> _R:
        if item < 0:
            raise IndexError
        x = self
        while isinstance(x, PCons):
            if item == 0:
                return x.head
            x = x.tail
            item -= 1
        raise IndexError

    def __iter__(self) -> typing.Iterator[_R]:
        x = self
        while isinstance(x, PCons):
            yield x.head
            x = x.tail


## Events


Listener = typing.Callable[[], None]


class Event:
    def __init__(self):
        self.listeners: set[Listener] = set()

    def __iadd__(self, listener: Listener):
        self.listeners.add(listener)
        return self

    def __isub__(self, listener: Listener):
        self.listeners.discard(listener)
        return self

    def __call__(self):
        for listener in self.listeners:
            listener()


## ECS


class Metadata:
    indices: dict[type, array.array[int]] = {}
    exact_indices: dict[type, int] = {}

    def __init__(self, *types: type):
        exact_indices: dict[type, int] = {}
        indices: dict[type, set[int]] = {}
        for t in types:
            self._aware_component(t, exact_indices, indices)
        self.exact_indices = exact_indices
        self.indices = {k: array.array("i", list(indices[k])) for k in indices}

    @staticmethod
    def _aware_component(
        t: type, exact_indices: dict[type, int], indices: dict[type, set[int]]
    ):
        for each in t.__mro__:
            if each is Component:
                continue
            if not issubclass(each, Component):
                continue
            if each in exact_indices:
                continue
            index = exact_indices[each] = len(exact_indices)
            if each not in indices:
                indices[each] = {index}
            for k, v in indices.items():
                if k is each:
                    continue
                if issubclass(each, k):
                    v.add(index)
            parent = indices[each]
            for k, v in indices.items():
                if k is each:
                    continue
                if issubclass(k, each):
                    parent.update(v)


class Component:
    entity: Entity

    def ready(self, e: Entity):
        self.entity = e
        self.entity.set_component(self)

    def init(self):
        pass

    def get_component(self, t: typing.Type[_C]) -> _C | None:
        return self.entity.get_component(t)

    def __getitem__(self, t: typing.Type[_C]) -> _C:
        return self.entity[t]


_C = typing.TypeVar("_C", bound=Component)


class NoComponentError(Exception):
    t: typing.Type[Component]

    def __init__(self, t: typing.Type[Component]) -> None:
        super().__init__(f"Component {t} not found")
        self.t = t


class Entity:

    __components__: tuple[typing.Type[Component], ...] = ()
    __metadata__: Metadata

    def __init_subclass__(cls) -> None:
        cls.__metadata__ = Metadata(*cls.__components__)

    components: list[Component | None]

    def __init__(self):
        self.components = [None] * len(self.__metadata__.exact_indices)

    def set_component(self, o: Component):
        t = type(o)
        i = self.__metadata__.exact_indices.get(t, -1)
        if i != -1:
            self.components[i] = o
            return True
        return False

    def get_component(self, t: typing.Type[_C]) -> _C | None:
        indices = self.__metadata__.indices.get(t, None)
        if indices is not None:
            for i in indices:
                o = self.components[i]
                if isinstance(o, t):
                    return o
        return None

    def __getitem__(self, t: typing.Type[_C]) -> _C:
        o = self.get_component(t)
        if o is not None:
            return o
        index = self.__metadata__.exact_indices.get(t, -1)
        if index == -1:
            raise NoComponentError(t)
        result: _C = t()
        result.ready(self)
        result.init()
        # self.components[index] = result
        return result


## Map


class Map(Component):
    _cells: list[MapCell | None]
    row: int
    col: int
    name: str

    def __init__(self, row: int, col: int, name: str, entity: Entity):
        self.ready(entity)
        self._cells = [None] * (row * col)
        self.row = row
        self.col = col
        self.name = name

    def __getitem__(self, ij: tuple[int, int]):
        i, j = ij

        index = i * self.row + j
        if index < 0 or index > len(self._cells):
            return None
        cell = self._cells[index]
        if cell is None:
            cell = self._cells[index] = MapCell(i, j, self)
        return cell

    def find_cell_at_point(self, x: int, y: int) -> MapCell | None:
        i = y
        j = x
        if 0 <= i < self.row and 0 <= j < self.col:
            return self[i, j]
        return None

    def find_cells_within_circle(self, x: int, y: int, radius: float):
        i = y
        j = x
        r = math.ceil(radius)
        for k in range(i - r, i + r + 1):
            for l in range(j - r, j + r + 1):
                if k < 0 or k >= self.row or l < 0 or l >= self.col:
                    continue
                if (k - i) ** 2 + (l - j) ** 2 <= r * r:
                    cell = self[k, l]
                    assert cell
                    yield cell


class MapListener(typing_extensions.Protocol):
    def __call__(self, __unit: Unit, __cell: MapCell) -> typing.Any:
        ...


class MapCell:
    def __init__(self, Y: int, X: int, map: Map):
        self.x = X
        self.y = Y
        self.map = map
        self.pass_consumption: int = 1
        self.contained_units: set[Unit] = set()
        self.enter_listeners: PList[MapListener] = PList.empty_cov()
        self.exit_listeners: PList[MapListener] = PList.empty_cov()

    def register_leave_events(self, listener: MapListener):
        self.exit_listeners = PList.cons(listener, self.exit_listeners)

    def register_enter_events(self, listener: MapListener):
        self.enter_listeners = PList.cons(listener, self.enter_listeners)

    def unsafe_left_by(self, unit: Unit, cell: MapCell):
        if unit in self.contained_units:
            self.contained_units.remove(unit)
            for each in self.exit_listeners:
                each(unit, cell)

    def unsafe_entered_by(self, unit: Unit, cell: MapCell):
        if unit not in self.contained_units:
            self.contained_units.add(unit)
            for each in self.enter_listeners:
                each(unit, cell)

    def __repr__(self) -> str:
        return f"MapCell({self.x}, {self.y} at {self.map})"


## Positional


class Positional(Component):
    _X = -1
    _Y = -1

    def __init__(self, map: Map, unit: Unit):
        self.ready(unit.entity)
        self.map = map
        self.unit = unit

    def loc(self):
        return self.map[self._X, self._Y]

    def set_pos(self, x: int, y: int, map: Map | None = None):
        self.map = new_map = map or self.map
        old_area = self.map.find_cell_at_point(self._X, self._Y)
        new_area = new_map.find_cell_at_point(x, y)
        self._X = x
        self._Y = y
        if old_area is not new_area:
            if old_area:
                old_area.unsafe_left_by(self.unit, old_area)
            if new_area:
                new_area.unsafe_entered_by(self.unit, new_area)
        return new_area

    def compute_distance(self, pos: Positional):
        if pos.map is self.map:
            return math.hypot(self._X - pos._X, self._Y - pos._Y)
        return math.inf

    def select_line_targets(
        self, distance: float, targetPos: Positional, radius: float = 1.0
    ):
        delta = self.compute_distance(targetPos)
        if delta == 0.0:
            yield self.unit
            yield targetPos.unit
            return
        dx = (targetPos._X - self._X) / delta
        dy = (targetPos._Y - self._Y) / delta

        acc = 0.0
        x = self._X
        y = self._Y

        visited: set[Unit] = set()
        going = True
        while going:
            if acc > distance:
                going = False
            for cell in self.map.find_cells_within_circle(int(x), int(y), radius):
                for unit in cell.contained_units:
                    if unit not in visited:
                        visited.add(unit)
                        yield unit
            acc += radius
            x = dx * acc
            y = dy * acc


### GameState


class EffectPredicate(typing_extensions.Protocol):
    def __call__(self, __eff: Effect) -> bool:
        ...


class Logger(typing_extensions.Protocol):
    def __call__(self, __msg: str, unames: tuple[str, ...], public: bool) -> None:
        ...


class _GameStateType:
    def __init__(self):
        self.groups: dict[str, Group] = {}
        self.units: dict[str, Unit] = {}
        self._effect_loop: deque[Effect] = deque()
        self._effect_loop_cache: deque[Effect] = deque()
        self._loggers: list[Logger] = []

    def add_effect(self, eff: Effect):
        if isinstance(eff, CompositeEffect):
            for subeff in eff.effects:
                self.add_effect(subeff)
        else:
            self._effect_loop.append(eff)
            eff.on_start()

    def log(self, msg: str, *unames: str, public: bool = True):
        for each in self._loggers:
            each(msg, unames, public)

    def matching_effects(self, f: EffectPredicate) -> typing.Iterable[Effect]:
        for eff in self._effect_loop:
            if f(eff):
                yield eff
        for eff in self._effect_loop_cache:
            if f(eff):
                yield eff

    def judge(self):
        cache = self._effect_loop_cache
        loop = self._effect_loop
        while loop:
            eff = loop.popleft()
            if eff.on_step():
                cache.append(eff)
        (self._effect_loop_cache, self._effect_loop) = (
            self._effect_loop,
            self._effect_loop_cache,
        )


GameState = _GameStateType()

### Step


class Effect(abc.ABC):
    @abc.abstractmethod
    def on_step(self) -> bool:
        raise NotImplementedError

    def on_start(self) -> None:
        pass

    def on_end(self) -> None:
        pass

    def submit(self):
        GameState.add_effect(self)


class CompositeEffect(Effect):
    def __init__(self, *effs: Effect) -> None:
        self.effects = effs

    def on_step(self) -> bool:
        raise NotImplementedError


class AttackEffect(Effect):
    attacker: Unit
    target: Unit
    create_damage: DamageCreation
    distance: float
    aoe: float

    def __init__(
        self,
        attacker: Unit,
        target: Unit,
        create_damage: DamageCreation,
        distance: float,
        aoe: float = 0.0,
    ):
        self.attacker = attacker
        self.target = target
        self.create_damage = create_damage
        self.distance = distance
        self.aoe = aoe

    def on_step(self) -> bool:
        attacker = self.attacker
        target = self.target
        if self.aoe:
            targets = attacker[Positional].select_line_targets(
                self.distance, target[Positional], self.aoe
            )
        elif attacker[Positional].compute_distance(target[Positional]) <= self.distance:
            targets = [target]
        else:
            targets = []
        for target in targets:
            if Group.same_group(attacker, target):
                continue
            damage = self.create_damage(attacker, target)
            da = target.get_component(DamanageAccepter)
            if not da:
                return False
            if dodger := target.get_component(Dodger):
                if dodger.dodge(attacker, damage):
                    continue
            da.on_damage(attacker, damage)
        return False


## Board


class Board(Component):
    STR: float = 0.0
    CON: float = 0.0
    DEX: float = 0.0
    INT: float = 0.0
    SPR: float = 0.0
    CHR: float = 0.0

    ATTACK_DIST: float = 4

    EFFORTS: int = 10
    MAX_EFFORTS: int = 10

    HP: float = 0
    MP: float = 0

    MAX_HP: float = 0
    MAX_MP: float = 0

    alive: bool = True

    on_death: Event
    buffs: set[Buff]

    def init(self):
        self.on_death = Event()

    def apply_STR(self, value: float):
        self.STR = value

    def apply_CON(self, value: float):
        self.CON = value
        self.MAX_HP = value
        self.HP = clamp(self.HP, 0, self.MAX_HP)

        self.MAX_EFFORTS = 10 + int(0.7 * value) + int(0.3 * self.SPR)
        self.EFFORTS = clamp(self.EFFORTS, 0, self.MAX_EFFORTS)

    def apply_DEX(self, value: float):
        self.DEX = value

    def apply_INT(self, value: float):
        self.INT = value

    def apply_SPR(self, value: float):
        self.SPR = value
        self.MAX_MP = value / 2
        self.MP = clamp(self.MP, 0, self.MAX_MP)

        self.MAX_EFFORTS = 10 + int(0.7 * self.CON) + int(0.3 * value)
        self.EFFORTS = clamp(self.EFFORTS, 0, self.MAX_EFFORTS)

    def apply_CHR(self, value: float):
        self.CHR = value

    def apply_HP(self, value: float):
        if not self.alive:
            return
        HP = self.HP = clamp(value, 0, self.MAX_HP)
        if HP == 0:
            self.alive = False
            self.on_death()

    def apply_ATTACK_DIST(self, value: float):
        self.ATTACK_DIST = value

    def consume_efforts(self, value: int):
        if not self.alive:
            return False
        if self.EFFORTS > value:
            self.EFFORTS -= value
            return True
        return False


## Battle System


@dataclass
class Damage:
    focus: float = 0
    real_damage: float = 0
    physical_damage: float = 0
    magical_damage: float = 0


@dataclass
class Shield:
    value: float


class DamanageAccepter(Component):
    enable: bool
    physical_shields: list[Shield]
    magical_shields: list[Shield]

    def init(self):
        self.enable = True
        self.physical_shields = []
        self.magical_shields = []

    def set_enable(self, value: bool):
        self.enable = value

    def on_damage(self, attacker: Unit, damage: Damage):
        if not self.enable:
            return
        unit = self[Unit]
        if random.random() > get_ratio(
            1 + 0.9 * unit[Board].SPR * 0.6 * unit[Board].DEX - damage.focus
        ):
            damage.physical_damage *= 2
            damage.magical_damage *= 2

        for shield in self.physical_shields:
            if damage.physical_damage <= 0:
                break

            if shield.value > damage.physical_damage:
                shield.value -= damage.physical_damage
                damage.physical_damage = 0
                break
            else:
                damage.physical_damage -= shield.value
                shield.value = 0

        for shield in self.magical_shields:
            if damage.magical_damage <= 0:
                break

            if shield.value > damage.magical_damage:
                shield.value -= damage.magical_damage
                damage.magical_damage = 0
                break
            else:
                damage.magical_damage -= shield.value
                shield.value = 0

        if damage.physical_damage != 0:
            unit[Board].apply_HP(unit[Board].HP - damage.physical_damage)
        if damage.magical_damage != 0:
            unit[Board].apply_HP(unit[Board].HP - damage.magical_damage)
        if damage.real_damage != 0:
            unit[Board].apply_HP(unit[Board].HP - damage.real_damage)


class Dodger(Component):
    def dodge(self, attacker: Unit, damage: Damage):
        unit = self[Unit]
        if damage.focus > 3 * unit[Board].SPR:
            return False
        if random.random() > get_ratio(
            damage.focus
            - 0.2 * unit[Board].SPR
            - 0.7 * unit[Board].DEX
            - 0.1 * unit[Board].CON
        ):
            return True
        return False


## components/buff


class Buff(abc.ABC):
    def on_start(self, target: Unit):
        target[Board].buffs.add(self)

    def on_end(self, target: Unit):
        target[Board].buffs.remove(self)


## Group


class Group:
    name: str
    units: list[Unit]
    owner: Unit

    def __init__(self, owner: Unit, name: str) -> None:
        self.owner = owner
        self.name = name
        self.units = []
        assert name not in GameState.groups
        GameState.groups[name] = self
        Group.join(owner, self)

    @staticmethod
    def same_group(x: Unit, y: Unit):
        return x.group is y.group

    @staticmethod
    def join(unit: Unit, group: Group):
        if unit.group is group:
            return False
        Group.leave(unit)
        group.units.append(unit)
        unit.group = group
        GameState.log(f"加入队伍【{group.name}】", unit.uname, public=True)

    @staticmethod
    def leave(unit: Unit):
        g = unit.group
        if g is not None:
            g.units.remove(unit)
            GameState.log(f"离开队伍【{g.name}】", unit.uname, public=True)
            unit.group = None
            if not g.units:
                GameState.groups.pop(g.name, None)
            else:
                if g.owner is unit:
                    g.owner = g.units[0]
                    GameState.log(f"队伍【{g.name}】的队长变更为【{unit.uname}】", public=True)


## components/Skill
class Skill(abc.ABC):
    casting_consumption: int = 2

    @abc.abstractmethod
    def cast(self, emitter: Unit, target: Entity | None) -> Effect | None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError


class Caster(Component):
    learnt_skills: dict[Skill, float]

    def init(self):
        super().init()
        self.learnt_skills = {}

    def has_skill(self, skill: Skill) -> bool:
        return skill in self.learnt_skills

    def level(self, skill: Skill) -> float:
        return self.learnt_skills.get(skill, 0)

    def level_up(self, skill: Skill, value: float):
        if skill in self.learnt_skills:
            self.learnt_skills[skill] += value

    def learn(self, skill: Skill):
        if skill in self.learnt_skills:
            return False
        self.learnt_skills[skill] = 1.0
        return True

    def forget(self, skill: Skill):
        if skill not in self.learnt_skills:
            return False
        del self.learnt_skills[skill]
        return True


## components/Items


class Item(abc.ABC):
    weight: int = 0
    activation_consumption = 1

    @property
    def name(self):
        return self.get_name()

    @abc.abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError

    def on_activated(self, unit: Unit, dst: Entity | None):
        return True

    def on_deactivated(self, unit: Unit):
        return True

    def on_install(self, unit: Unit):
        return

    def on_uninstall(self, unit: Unit):
        self.on_deactivated(unit)

    @staticmethod
    def install(unit: Unit, item: Item):
        bag = unit[Bag]
        return bag.add_item(item)

    @staticmethod
    def uninstall(unit: Unit, item: Item):
        bag = unit[Bag]
        return bag.remove_item(item)


class ItemPredicate(typing_extensions.Protocol):
    def __call__(self, item: Item) -> bool:
        ...


MAX_MONEY = 99999999


class Bag(Component):
    max_capacity: int = 100
    cur_capacity: int = 0
    money: int = 0
    _items: set[Item]

    def init(self):
        super().init()
        self._items = set()

    def all_items(self) -> typing.Iterable[Item]:
        return self._items

    def matching_items(self, f: ItemPredicate):
        for item in self._items:
            if f(item):
                yield item

    def add_money(self, value: int):
        self.money += value
        self.money = clamp(self.money, 0, MAX_MONEY)

    def remove_money(self, value: int):
        self.money -= value
        self.money = clamp(self.money, 0, MAX_MONEY)

    def add_item(self, item: Item):
        if item in self._items:
            return False
        if self.cur_capacity + item.weight > self.max_capacity:
            return False
        self._items.add(item)
        self.cur_capacity += item.weight
        item.on_install(self[Unit])
        return True

    def has_item(self, item: Item):
        return item in self._items

    def remove_item(self, item: Item):
        if item not in self._items:
            return False
        self._items.remove(item)
        self.cur_capacity -= item.weight
        item.on_uninstall(self[Unit])
        return True


## Unit


class Unit(Component):
    group: Group | None = None
    uname: str = ""


## Utils


@typing.overload
def clamp(value: int, minval: int, maxval: int) -> int:
    ...


@typing.overload
def clamp(value: float, minval: float, maxval: float) -> float:
    ...


def clamp(value: float, minval: float, maxval: float) -> float:
    return max(minval, min(value, maxval))


def get_ratio(x: int | float) -> float:
    return x / (100 + abs(x))


def sign(x: int | float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


DamageCreation = typing.Callable[[Unit, Unit], Damage]
