# Introduction

This is a python application to support a simple 8-bit computer that I am building. This program plus
an old Velleman K8055 kit plays the role of a clock pulse and the main RAM of the computer. All
the other logic is implemented in the electronics on the breadboards.

## Wrapping DLL
This uses a Python module created By Fergus Leahy a.k.a. Fergul Magurgul
(https://sourceforge.net/projects/pyk8055/)

## 32 Bitness

The K8055 dll is 32bit so you need a 32bit python to run this.

## Role of Board in MyComputer

Acts as the main memory of the computer and the clock.
The basic cycle is:
 * read contents of address bus (16bits)
 * read R/W bit
 * if read, get contents at address and put them on the data bus
 * if write, take contents on data bus and write them to the memory 

## Pins
* In5 = R/W flag
* In1-4 = data from computer
* Out1 = clock
* Out2-Out4 = bus address
* Out 5-8 = data read from memory

## Memory Bus

8 blocks of 4 bits each, numbered 0-7

 * 0, 1, 2, 3 = 16 bits of address
 * 4, 5 = 8 bits of data from memory
 * 6, 7 = 8 bits of data from MyComputer

## Cycle
 * start in phase 0
 * Read/write
 * click to 1 (writes N)
 * click to 0 (moves to phase 1)
 * Read/write
 * click to 1 (writes to W & T)
 * click to 0 (moves to phase 2)
 * calculations take place in this phase
 * click to 1 (write result of calculations)
 * click to 0 (moves to phase 3)
 * click to 1 (*future* write incremented program counter)
 * click to 0 (moves to phase 0)
 
## Wiring status

### Clicks
Clicks control when a register will write the contents of the bus to registers

| Name | Wired | Tested | 
|------|-------|--------|
| P1   | No    |        |
| M1   | Yes   |        |
| W    | Yes   |        |
| A    | Yes   |        |
| R    | No    |        |
| N    | Yes   |        |
| TN   | Yes   |        |

### Flags

Flags control which register is enabled to so that its contents are presented to the bus from registers.

| Name | Wired                           | Tested | 
|------|---------------------------------|--------|
| P1   | only RDV, CPY. open OR for rest |        |
| M1   | Yes                             |        |
| W    | Yes                             |        |
| A    | Yes                             |        |
| R    | Only for RDV, CPY. need for ADV |        |
 
### Instructions
| Name | Wired | Comment | 
|------|-------|---------|
| RDV  | Yes   |         |
| CPY  | Yes   |         |
| WRT  | Yes   |         |
| RDM  | Yes   |         |
| ADV  |       |         |
| ADM  |       |         |
| JMZ  |       |         |
| ---  | ---   | ---     |
| DBG  |       |         |
| PAG  |       |         |



