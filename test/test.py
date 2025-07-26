# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    """
    Tiny Tapeout - Example test with pulse tests:
    1. No operation (start/en = 0)
    2. 4-cycle pulse with start/en = 1
    Adapt according to your design's expected outputs!
    """
    dut._log.info("Start")

    # Clock
    clock = Clock(dut.clk, 10, units="us")   # 10 us period => 100 KHz
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("\n--- Test Case 1: No Operation ---")
    # Case 1
    # ui_in[5:2] = 0000, start(0), enable(0)
    dut.ui_in.value = 0b000000  # All zero
    await ClockCycles(dut.clk, 1)
    # Expect no operation, so uo_out/other outputs unchanged/inactive
    assert dut.uo_out.value == 0, f"Case 1 Failed: uo_out={dut.uo_out.value}"

    dut._log.info("\n--- Test Case 2: 4-cycle pulse (start & enable = 1) ---")
    # Case 2
    # ui_in[5:2]=0100 (pulse width 4), start=1 (bit0), enable=1 (bit1)
    # So, ui_in = [5]=0, [4]=1, [3]=0, [2]=0, [1]=1, [0]=1 => 0b010011
    dut.ui_in.value = 0b010011
    await ClockCycles(dut.clk, 1)  # Inputs take effect

    # The expected behavior (example): output goes high for 4 cycles, then low
    for pulse_cycle in range(4):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == 1, f"Pulse not active at cycle {pulse_cycle+1}"

    await ClockCycles(dut.clk, 1)
    # After 4 cycles, should return to inactive
    assert dut.uo_out.value == 0, f"uo_out did not deactivate after pulse"

    dut._log.info("All test cases passed")
