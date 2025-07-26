# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    """Test bench for tt_um_pwe pulse FSM."""
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    ###############################################################################
    # Test Case 1: No operation (start=0, enable=0, data_in=0)
    ###############################################################################
    dut._log.info("\n--- Test Case 1: No Operation ---")
    dut.ui_in.value = 0b00000000  # all low
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == 0, f'Case 1: uo_out={dut.uo_out.value} expected 0'

    ###############################################################################
    # Test Case 2: 4-cycle pulse (start=1, enable=1, data_in=4)
    ###############################################################################
    dut._log.info("\n--- Test Case 2: 4-cycle pulse (start & enable = 1) ---")
    # Prepare input:
    # ui_in[5:2]=0100 (4), enable=1 (bit1), start=1 (bit0)
    test_val = (4 << 2) | (1 << 1) | 1    # 0b010000 | 0b000010 | 0b000001 == 0b010011 == 19
    dut.ui_in.value = test_val

    # Hold start+enable for **at least one cycle** so FSM sees it at clk edge in IDLE
    await ClockCycles(dut.clk, 1)

    # Release 'start' (optionally, depends on spec; FSM latches value at transition)
    dut.ui_in.value = test_val & ~1  # clear 'start'
    await ClockCycles(dut.clk, 1)

    # FSM should now be in COUNTING, with pulse_out active for 4 cycles.
    for i in range(4):
        await ClockCycles(dut.clk, 1)
        uo_val = int(dut.uo_out.value)
        pulse_bit = uo_val & 0b1
        dut._log.info(f'   Cycle {i+1}: uo_out={uo_val:08b}, pulse={pulse_bit}')
        assert pulse_bit == 1, f'Pulse not active at cycle {i+1} (uo_out={uo_val:08b})'

    # Next cycle: pulse_out should drop and done should assert
    await ClockCycles(dut.clk, 1)
    uo_val = int(dut.uo_out.value)
    pulse_bit = uo_val & 0b1
    done_bit = (uo_val >> 1) & 0b1
    dut._log.info(f'  After pulse: uo_out={uo_val:08b}')
    assert pulse_bit == 0, f"Pulse_out still high after end of pulse (uo_out={uo_val:08b})"
    assert done_bit == 1, f"Done not asserted after pulse (uo_out={uo_val:08b})"

    # Next cycle: done bit drops, all zero
    await ClockCycles(dut.clk, 1)
    uo_val = int(dut.uo_out.value)
    assert uo_val == 0, f"After done should return to zero (uo_out={uo_val:08b})"

    dut._log.info("All test cases PASSED.")
