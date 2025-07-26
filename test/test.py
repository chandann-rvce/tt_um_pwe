# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb.result import TestFailure


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Start a 10us clock (100 kHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Apply reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # === Test Scenario 1: No operation (start=0, enable=0) ===
    dut._log.info("Scenario 1: No operation")
    dut.ui_in.value = 0b00000000  # start=0, enable=0, data_in=0000
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 0, "Scenario 1 failed: expected uo_out = 0"

    # === Scenario 2: 4-cycle pulse (start=1, enable=1, data_in=0100) ===
    dut._log.info("Scenario 2: 4-cycle pulse")
    dut.ui_in.value = 0b0100011  # start=1, enable=1, data_in=0100
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b01000010  # deassert start
    await ClockCycles(dut.clk, 1)

    # Pulse should remain high for 4 cycles, then done should go high
    pulse_seen = 0
    while int(dut.uo_out.value) & 0x2 == 0:  # Wait for done (bit 1)
        if (int(dut.uo_out.value) & 0x1):     # pulse_out = bit 0
            pulse_seen += 1
        await ClockCycles(dut.clk, 1)

    assert pulse_seen == 4, f"Scenario 2 failed: expected 4 pulse cycles, got {pulse_seen}"

    # === Scenario 3: 3-cycle pulse ===
    dut._log.info("Scenario 3: 3-cycle pulse")
    dut.ui_in.value = 0b0011011  # data_in=0011, start=1, enable=1
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b00110010  # deassert start
    await ClockCycles(dut.clk, 1)

    pulse_seen = 0
    while int(dut.uo_out.value) & 0x2 == 0:  # Wait for done
        if (int(dut.uo_out.value) & 0x1):
            pulse_seen += 1
        await ClockCycles(dut.clk, 1)

    assert pulse_seen == 3, f"Scenario 3 failed: expected 3 pulse cycles, got {pulse_seen}"

    # === Scenario 4: 1-cycle pulse ===
    dut._log.info("Scenario 4: 1-cycle pulse")
    dut.ui_in.value = 0b0001011  # data_in=0001, start=1, enable=1
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b00010010
    await ClockCycles(dut.clk, 1)

    pulse_seen = 0
    while int(dut.uo_out.value) & 0x2 == 0:
        if (int(dut.uo_out.value) & 0x1):
            pulse_seen += 1
        await ClockCycles(dut.clk, 1)

    assert pulse_seen == 1, f"Scenario 4 failed: expected 1 pulse cycle, got {pulse_seen}"

    # === Scenario 5: Remain idle (start=0, enable=0, data_in=0000) ===
    dut._log.info("Scenario 5: IDLE again")
    dut.ui_in.value = 0b00000000
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 0, "Scenario 5 failed: expected IDLE state output"

    dut._log.info("All test scenarios passed successfully!")

