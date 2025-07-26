/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_pwe (
    input  wire [7:0] ui_in,     // Dedicated inputs
    output wire [7:0] uo_out,    // Dedicated outputs
    input  wire [7:0] uio_in,    // IOs: Input path
    output wire [7:0] uio_out,   // IOs: Output path
    output wire [7:0] uio_oe,    // IOs: Enable path (active high)
    input  wire       ena,       // always 1 when powered (can ignore)
    input  wire       clk,       // clock
    input  wire       rst_n      // active-low reset
);

  // Map ui_in pins to named signals
  wire        start = ui_in[0];
  wire        enable = ui_in[1];
  wire [3:0]  data_in = ui_in[5:2];  // ui_in[5:2] for 4-bit input // ui_in[5:2] for 4-bit input
  wire        unused6 = ui_in[6];
  wire        unused7 = ui_in[7];

  // Output signals
  reg         pulse_out;
  reg         done;
  wire [5:0]  unused_outputs = 6'b000000; // You can use this for debug if needed

  // Assign to uo_out[7:0]
  assign uo_out = {unused_outputs, done, pulse_out};

  // Tie off unused IOs
  assign uio_out = 8'b00000000;
  assign uio_oe  = 8'b00000000;

  // Internal reset (active high)
  wire reset = ~rst_n;

  // FSM states
  localparam IDLE     = 2'b00;
  localparam COUNTING = 2'b01;
  localparam DONE     = 2'b10;

  reg [1:0] state, next_state;
  reg [3:0] counter, pulse_width;

  // State update
  always @(posedge clk or posedge reset) begin
    if (reset) begin
      state       <= IDLE;
      counter     <= 4'd0;
      pulse_width <= 4'd0;
      pulse_out   <= 1'b0;
      done        <= 1'b0;
    end else begin
      state <= next_state;

      if (state == IDLE && start && enable) begin
        pulse_width <= data_in;
        counter     <= data_in;
      end else if (state == COUNTING && counter > 0) begin
        counter <= counter - 1;
      end
    end
  end

  // Next-state logic and outputs
  always @(*) begin
    next_state <= state;
    pulse_out  <= 1'b0;
    done       <= 1'b0;

    case (state)
      IDLE: begin
        if (start && enable)
          next_state = COUNTING;
      end

      COUNTING: begin
        pulse_out = 1'b1;
        if (counter == 0)
          next_state = DONE;
      end

      DONE: begin
        done = 1'b1;
        next_state = IDLE;
      end
    endcase
  end

  // Unused input suppression
  wire _unused = &{ena, uio_in, unused6, unused7};

endmodule
