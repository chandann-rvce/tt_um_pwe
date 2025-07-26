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

    #####################################################################
    # Test Case 1: No operation (start=0, enable=0, data_in=0)
    #####################################################################
    dut._log.info("\n--- Test Case 1: No Operation ---")
    dut.ui_in.value = 0b00000000  # all low
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == 0, f'Case 1: uo_out={dut.uo_out.value} expected 0'

    #####################################################################
    # Test Case 2: 4-cycle pulse (start=1, enable=1, data_in=4)
    #####################################################################
    dut._log.info("\n--- Test Case 2: 4-cycle pulse (start & enable = 1) ---")
    # ui_in[5:2]=0100 (4), enable=1 (bit1), start=1 (bit0)
    test_val = (4 << 2) | (1 << 1) | 1    # 0b010011 == 19
    dut.ui_in.value = test_val

    await ClockCycles(dut.clk, 1)  # hold start/en at least one cycle

    # (optionally) release start
    dut.ui_in.value = test_val & ~1
    await ClockCycles(dut.clk, 1)

    # FSM: pulse_out active 4 cycles
    for i in range(4):
        await ClockCycles(dut.clk, 1)
        val = int(dut.uo_out.value)
        pulse = val & 1
        dut._log.info(f'   Cycle {i+1}: uo_out={val:08b}, pulse={pulse}')
        assert pulse == 1, f'Pulse not active at cycle {i+1} (uo_out={val:08b})'

    # Next cycle: pulse_out is STILL 1 (FSM is in COUNTING with counter==0)
    await ClockCycles(dut.clk, 1)
    val = int(dut.uo_out.value)
    pulse = val & 1
    done = (val >> 1) & 1
    dut._log.info(f'   After last pulse: uo_out={val:08b}')
    assert pulse == 1 and done == 0, f'Expected pulse_out=1, done=0 after last pulse_cycle (uo_out={val:08b})'

    # Now, FSM enters DONE; pulse_out=0, done=1
    await ClockCycles(dut.clk, 1)
    val = int(dut.uo_out.value)
    pulse = val & 1
    done = (val >> 1) & 1
    dut._log.info(f'   In DONE state: uo_out={val:08b}')
    assert pulse == 0 and done == 1, f'Expected pulse_out=0, done=1 in DONE state (uo_out={val:08b})'

    # Next: both go back to 0.
    await ClockCycles(dut.clk, 1)
    val = int(dut.uo_out.value)
    dut._log.info(f'   Back to IDLE: uo_out={val:08b}')
    assert val == 0, f'After done should return to zero (uo_out={val:08b})'

    dut._log.info("All test cases PASSED.")
