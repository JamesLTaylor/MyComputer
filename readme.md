# Introduction

This is a python application to support a simple 8-bit computer that I am building. This program plus
an old Velleman K8055 kit plays the role of a clock pulse and the main RAM of the computer. All
the other logic is implemented in the electronics on the breadboards.

![20240624_120002.jpg](images%2F20240624_120002.jpg)


## Wrapping DLL
This uses a Python module created By Fergus Leahy a.k.a. Fergul Magurgul
(https://sourceforge.net/projects/pyk8055/)

## 32 Bitness

The K8055 dll is 32bit so you need a 32bit python to run this.

## Role of Board in MyComputer

Acts as the main memory of the computer and the clock.
The basic cycle is:
 * read contents of address bus (8bits) ()
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

 * 0, 1 = 8 bits of address/data
 * *2, 3 = future extra 8 bits of address.* 
 * 4, 5 = 8 bits of address used during phase 2 write
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
 * click to 1 (write result of calculations to registers/memory)
 * click to 0 (moves to phase 3)
 * click to 1 (write incremented program counter if not written in phase 2)
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

| Name | Wired | Tested | 
|------|-------|--------|
| P1   | Yes   |        |
| M1   | Yes   |        |
| W    | Yes   |        |
| A    | Yes   |        |
| R    | Yes   |        |
 
### Instructions
| Name | Binary    | Wired | Comment                                                                                         | 
|------|-----------|-------|-------------------------------------------------------------------------------------------------|
| RDV  | 00111     | Yes   | Read the immediate value into the specified register                                            |
| CPY  | 00101     | Yes   | Copy from SRC register to TGT register                                                          |
| WRT  | 00100     | Yes   |                                                                                                 |
| RDM  | 00110     | Yes   |                                                                                                 |
| ADV  | 01001     | Yes   | Add immediate value to TGT. Will use carry from previous ADV/ADM. Run ADV A 0 to clear          |
| ADM  | 01000     | Yes   | Add value currently pointed to by M1 to SRC.                                                    |
| JMZ  | 10001     | Yes   | Copy the immediate value to P1 if the SRC register is zero.                                     |
| NEG  | 11001     | Yes   | Write X to R where SRC+X = 256. Set immediate to 1 to use carry from previous NEG, 0 to ignore. |
| NOP  | 00111_100 | N/A   | Do nothing, read zero to nonexistent register 4                                                 |
| HLT  | 00000     | N/A   | Do nothing. Not interpreted by device. Used by interface to halt and send no more clocks.       |



Instruction bits are n0 n1 n2 n3 n4.

* n1 says if phase 3 should write to R
* n3 says if first address is Target not Source.
* n4 says if phase 2 should load from P+1 not M1

**Valid Sources**

Note that M0 and P0 can only be written to, not read from. i.e. you can only CPY to, RDV and RDM.


### Registers

| Index | Binary  | Name     |
|-------|---------|----------|
| ~~0~~ | ~~000~~ | ~~P0~~   |
| 1     | 001     | P1       |
| ~~2~~ | ~~010~~ | ~~M0~~   |
| 3     | 011     | M1       |
| 4     | 100     | *unused* |
| 5     | 101     | *unused* |
| 6     | 110     | A        |
| 7     | 111     | R        |

## Languange/Assembler/Compiler

Comment lines start with `#`

```
# This is a comment
```

Pariable declarations start with  `*`

Line labels begin with ':'

Page labels begin with '::'

## TODO

 * Only write for 00100
 * Add M0, P0 - they are always targets so can avoid some logic. (they have to be because their output is always to the
                connection bus)
 * Have special addresses for "screen" output

## Test Programs

1. Add 16 bit numbers
2. Subtract 16 bit numbers
3. Find the largest number in list
4. Sort a list
5. Find the largest number in a list that is longer than 128 numbers



