import pytest

from hera.data import Op
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_execute_unknown_instruction(vm):
    with pytest.raises(RuntimeError):
        vm.exec_one(Op("whatever", []))
