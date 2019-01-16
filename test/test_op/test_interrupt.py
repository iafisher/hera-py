import pytest
from unittest.mock import patch

from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_SWI_emits_warning(vm):
    with patch("hera.vm.emit_warning") as mock_emit_warning:
        vm.exec_SWI(1)
        assert mock_emit_warning.call_count == 1
        assert "SWI is a no-op in this simulator" in mock_emit_warning.call_args[0][0]


def test_SWI_increments_pc(vm):
    vm.exec_SWI(1)
    assert vm.pc == 1


def test_RTI_emits_warning(vm):
    with patch("hera.vm.emit_warning") as mock_emit_warning:
        vm.exec_RTI()
        assert mock_emit_warning.call_count == 1
        assert "RTI is a no-op in this simulator" in mock_emit_warning.call_args[0][0]


def test_RTI_increments_pc(vm):
    vm.exec_RTI()
    assert vm.pc == 1
