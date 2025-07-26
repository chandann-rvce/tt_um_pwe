# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start test")

    # Clock: 10 us period = 100 kHz
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # --------------------------
    # Test Case 1: No operation
    # --------------------------
    dut._log.info("Test 1: No operation")
    dut.ui_in.value = 0b00000000  # data_in = 0000, start=0, enable=0
    await ClockCycles(dut.clk, 2)

    # Expect pulse_out and done to remain 0
    assert dut.uo_out.value == 0, f"Unexpected output during No-op: {dut.uo_out.value}"

    # --------------------------
    # Test Case 2: 4-cycle pulse
    # --------------------------
    dut._log.info("Test 2: 4-cycle pulse with start and enable")
    # Set data_in = 0100, start = 1, enable = 1 → ui_in[5:2]=0100, ui_in[1]=1, ui_in[0]=1
    dut.ui_in.value = 0b01100101  # bits: [7:0] = 01|100|1|1 → unused7=0, unused6=1, data_in=0100, enable=1, start=1

    # Wait 1 clock for latching inputs
    await ClockCycles(dut.clk, 1)

    # Observe pulse_out for 4 cycles
    for i in range(4):
        await FallingEdge(dut.clk)
        assert dut.uo_out.value & 0b00000001 == 1, f"Expected pulse_out=1 during cycle {i}, got {dut.uo_out.value}"

    # After pulse is over, pulse_out = 0, done = 1
    await FallingEdge(dut.clk)
    assert dut.uo_out.value & 0b00000001 == 0, f"Expected pulse_out=0 after 4 cycles, got {dut.uo_out.value}"
    assert dut.uo_out.value & 0b00000010 == 2, f"Expected done=1 after 4 cycles, got {dut.uo_out.value}"

    dut._log.info("All tests passed")
