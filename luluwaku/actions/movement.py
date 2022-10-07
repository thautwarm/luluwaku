from __future__ import annotations
from luluwaku.core import *


class MoveTo(Effect):
    target: tuple[int, int]
    emitter: Unit

    def __init__(self, emitter: Unit, x: int, y: int):
        self.emitter = emitter
        self.target = (x, y)

    def on_step(self):
        pos = self.emitter[Positional]
        status = self.emitter[Board]
        dx = self.target[0] - pos._X
        dy = self.target[1] - pos._Y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return False

        limit = status.DEX * 0.3 + status.SPR * 0.05 + status.CON * 0.1
        finalX = pos._X + dx * limit / dist
        finalY = pos._Y + dy * limit / dist

        x = pos._X
        y = pos._Y

        if abs(dx) > abs(dy):
            dx_unit = sign(dx)
            k = dy / dx
            while x < finalX:
                x += dx_unit
                y += k * dx_unit
                cell = pos.map.find_cell_at_point(int(x), int(y))
                if cell and status.consume_efforts(cell.pass_consumption):
                    pos.set_pos(int(x), int(y))
                else:
                    break
        else:
            dy_unit = sign(dy)
            k = dx / dy
            while y < finalY:
                y += dy_unit
                x += k * dy_unit
                cell = pos.map.find_cell_at_point(int(x), int(y))
                if cell and status.consume_efforts(cell.pass_consumption):
                    pos.set_pos(int(x), int(y))
                else:
                    break
        return False


def Move(emitter: Unit, target: tuple[int, int]):
    pos = emitter[Positional]
    return MoveTo(emitter, target[0] + pos._X, target[1] + pos._Y)
