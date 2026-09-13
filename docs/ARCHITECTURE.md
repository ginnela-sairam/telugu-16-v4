# T-16 SoC Architecture

The TELUGU-16 (T-16 V4.1) is a 16-bit RISC System-on-Chip designed for the SkyWater 130nm process. It features a custom instruction set, on-chip ROM and RAM, and experimental stochastic hardware (P-bit).

## System Block Diagram

```mermaid
graph TD
    %% Core Components
    subgraph CPU [T-16 Core]
        ALU[ALU]
        REGS[8x16 Registers]
        CTRL[Control Unit]
        PC[Program Counter]
    end

    subgraph MEMORY [Memory Subsystem]
        ROM[(Program ROM<br/>256x16)]
        RAM[(Data RAM<br/>128x16)]
    end

    subgraph PERIPHERALS [Peripherals]
        GPIO[GPIO Latch<br/>16-bit]
        TIMER[Hardware Timer<br/>16-bit]
        RO[Ring Oscillator<br/>15-stage]
        PBIT[P-Bit Generator<br/>Thermal Noise]
    end

    %% Connections
    PC -->|Address| ROM
    ROM -->|Instruction| CTRL
    CTRL --> ALU
    CTRL --> REGS
    ALU <--> REGS
    
    %% Bus Connections
    ALU -->|Address/Data| RAM
    RAM -->|Data| ALU
    
    %% Peripheral Connections (Memory Mapped)
    ALU -->|Write| GPIO
    ALU -->|Read| TIMER
    RO -->|Pulses| PBIT
    PBIT -->|Stochastic Bit| ALU
```

## RTL-to-GDS Flow

```mermaid
graph TD
    A[Verilog RTL] -->|Linter & Checker| B(Verilator)
    B -->|Synthesis| C(Yosys)
    C -->|Gate-Level Netlist| D[Floorplanning]
    
    subgraph OpenLane Flow
    D -->|Placement| E(RePLace)
    E -->|Clock Tree Synthesis| F(TritonCTS)
    F -->|Routing| G(TritonRoute)
    end
    
    G -->|Signoff DRC/LVS| H(Magic & Netgen)
    H -->|Final Output| I((GDSII Factory File))
```
