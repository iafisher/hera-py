import pytest
from unittest.mock import patch
from .utils import helper

from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_SWI_emits_warning(vm):
    with patch("hera.vm.VirtualMachine.warn") as mock_warn:
        helper(vm, "SWI(1)")

        assert mock_warn.call_count == 1
        assert "SWI is a no-op in this simulator" in mock_warn.call_args[0][0]


def test_SWI_increments_pc(vm):
    helper(vm, "SWI(1)")

    assert vm.pc == 1


def test_RTI_emits_warning(vm):
    with patch("hera.vm.VirtualMachine.warn") as mock_warn:
        helper(vm, "RTI()")

        assert mock_warn.call_count == 1
        assert "RTI is a no-op in this simulator" in mock_warn.call_args[0][0]


def test_RTI_increments_pc(vm):
    helper(vm, "RTI()")

    assert vm.pc == 1
