# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


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

    # === Scenario 1: No operation (start=0, enable=0) ===
    dut._log.info("Scenario 1: No operation")
    dut.ui_in.value = 0b00000000
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 0, "Scenario 1 failed: expected uo_out = 0"

    # Helper to run a pulse test
    async def run_pulse_test(data_in_val, expected_cycles, label):
        dut._log.info(f"{label}: data_in={data_in_val}")
        dut.ui_in.value = (data_in_val << 2) | 0b11  # start=1, enable=1
        await ClockCycles(dut.clk, 1)
        dut.ui_in.value = (data_in_val << 2) | 0b10  # deassert start
        await ClockCycles(dut.clk, 1)

        pulse_seen = 0
        while dut.uo_out.value.integer & 0x2 == 0:  # while done == 0
            if dut.uo_out.value.integer & 0x1:      # pulse_out == 1
                pulse_seen += 1
            await ClockCycles(dut.clk, 1)

        assert pulse_seen == expected_cycles, (
            f"{label} failed: expected {expected_cycles} pulse cycles, got {pulse_seen}"
        )

    # === Scenario 2: 4-cycle pulse ===
    await run_pulse_test(data_in_val=4, expected_cycles=4, label="Scenario 2")

    # === Scenario 3: 3-cycle pulse ===
    await run_pulse_test(data_in_val=3, expected_cycles=3, label="Scenario 3")

    # === Scenario 4: 1-cycle pulse ===
    await run_pulse_test(data_in_val=1, expected_cycles=1, label="Scenario 4")

    # === Scenario 5: Remain idle ===
    dut._log.info("Scenario 5: IDLE again")
    dut.ui_in.value = 0b00000000
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 0, "Scenario 5 failed: expected IDLE output"

    dut._log.info("All test scenarios passed successfully!")
