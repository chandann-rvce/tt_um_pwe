# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start Testbench Execution")

    # Start a 10us clock (100 kHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Apply reset
    dut._log.info("Applying Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # === Scenario 1: No operation (start=0, enable=0) ===
    dut._log.info("Scenario 1 [0-10ns]: No operation (start=0, enable=0)")
    dut.ui_in.value = 0b00000000  # ui_in[5:2]=0000, start=0, enable=0
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 0, "Scenario 1 failed: expected uo_out = 0"

    # Helper function to run pulse width test
    async def run_pulse_test(data_in_val, expected_cycles, label):
        dut._log.info(f"{label}: Start Pulse Test with ui_in[5:2]={data_in_val:04b}")
        # Set start=1, enable=1
        dut.ui_in.value = (data_in_val << 2) | 0b11
        await ClockCycles(dut.clk, 1)
        # Deassert start to simulate edge trigger
        dut.ui_in.value = (data_in_val << 2) | 0b10
        await ClockCycles(dut.clk, 1)

        pulse_seen = 0
        while dut.uo_out.value.integer & 0x2 == 0:  # while done == 0
            if dut.uo_out.value.integer & 0x1:      # pulse_out == 1
                pulse_seen += 1
            await ClockCycles(dut.clk, 1)

        assert pulse_seen == expected_cycles, (
            f"{label} failed: expected {expected_cycles} pulses, got {pulse_seen}"
        )
        dut._log.info(f"{label} passed: {pulse_seen} pulses observed.")

    # === Scenario 2: 4-cycle pulse (ui_in[5:2]=0100, start=1, enable=1) ===
    await run_pulse_test(data_in_val=4, expected_cycles=4, label="Scenario 2 [10-30ns]")

    # === Scenario 3: 3-cycle pulse (ui_in[5:2]=0011, start=1, enable=1) ===
    await run_pulse_test(data_in_val=3, expected_cycles=3, label="Scenario 3 [30-60ns]")

    # === Scenario 4: 1-cycle pulse (ui_in[5:2]=0001, start=1, enable=1) ===
    await run_pulse_test(data_in_val=1, expected_cycles=1, label="Scenario 4 [60-90ns]")

    # === Scenario 5: Return to IDLE (start=0, enable=0) ===
    dut._log.info("Scenario 5 [90-100ns]: IDLE mode again (start=0, enable=0)")
    dut.ui_in.value = 0b00000000
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out.value == 0, "Scenario 5 failed: expected IDLE output"

    dut._log.info("✅ All test scenarios passed successfully!")
