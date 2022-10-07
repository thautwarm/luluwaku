import typing
from luluwaku.core import *
from pprint import pprint


def test_maps():
    class MapObject(Entity):
        __components__ = (Map,)

    class User(Entity):

        __components__ = (Unit, Board, Positional, DamanageAccepter, Caster, Bag, Board)

        def __init__(self, map: Map):
            Entity.__init__(self)
            pos = Positional(map, self[Unit])
            pos.set_pos(-1, -1, map)

    pprint(User.__metadata__)

    M = MapObject()
    m = Map(100, 100, "m", M)

    cell = m.find_cell_at_point(2, 4)
    assert cell

    logs = []

    def do_enter(u: Unit, cell: MapCell):
        p = u.entity
        logs.append((p, "enter", cell))

    def do_leave(u: Unit, cell: MapCell):
        p = u.entity
        logs.append((p, "leave", cell))

    cell.register_enter_events(do_enter)
    cell.register_leave_events(do_leave)

    user = User(m)
    cell2 = user[Positional].loc()
    assert not cell2

    user[Positional].set_pos(2, 4)
    user[Positional].set_pos(10, 10)

    assert logs == [
        (user, "enter", m.find_cell_at_point(2, 4)),
        (user, "leave", m.find_cell_at_point(2, 4)),
    ]
