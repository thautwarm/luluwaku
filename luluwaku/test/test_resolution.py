import typing
from luluwaku.core import *
import array


def test_resolution():
    class A(Component):
        pass

    class C(Component):
        pass

    class B(A, C):
        pass

    class E(Entity):
        __components__ = (C, A, B)

    i_A = E.__metadata__.exact_indices[A]
    i_B = E.__metadata__.exact_indices[B]
    i_C = E.__metadata__.exact_indices[C]

    assert E.__metadata__.indices[A] == array.array("i", sorted([i_A, i_B]))
    assert E.__metadata__.indices[B] == array.array("i", [i_B])
    assert E.__metadata__.indices[C] == array.array("i", sorted([i_B, i_C]))
