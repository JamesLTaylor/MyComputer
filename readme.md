# Introduction

This is a python application to support a simple 8-bit computer. This program, plus
an old Velleman K8055 kit to send the bits, plays the role of a clock pulse and the main RAM of the computer. All
the other logic is implemented in the electronics on the breadboards.

This is a picture of the finished computer
![20240624_120002.jpg](images%2F20240624_120002.jpg)

And this is one with a description of the parts:
![2024-06-24 dark with labels.png](images%2F2024-06-24%20dark%20with%20labels.png)


## Wrapping DLL
This uses a Python module created By Fergus Leahy a.k.a. Fergul Magurgul
(https://sourceforge.net/projects/pyk8055/)

## 32 Bitness

The K8055 dll is 32bit so you need a 32bit python to run this.

## Role of Board in MyComputer

Acts as the main memory of the computer and the clock.
The basic cycle is:
 * read contents of address bus (8bits + 8bits for page)
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
 * 2, 3 = 8 bits for memory or program page counter. 
 * 4, 5 = 8 bits of address used during phase 2 write
 * 6, 7 = 8 bits of data from MyComputer

## Cycle
 * start in phase 0
 * Read/write
 * click to 1 (writes N and TP1)
 * click to 0 (moves to phase 1)
 * Read/write
 * click to 1 (writes to W, T, TM1)
 * click to 0 (moves to phase 2)
 * calculations take place in this phase
 * click to 1 (write result of calculations to registers/memory, write carry bits)
 * click to 0 (moves to phase 3)
 * click to 1 (write incremented program counter TP1 if not written in phase 2, copy carry bits to storage for next cycle)
 * click to 0 (moves to phase 0)
 

### Clicks
Clicks control when a register will write the contents of the bus to registers

### Flags

Flags control which register is enabled to so that its contents are presented to the bus from registers.

 
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


### Addressable registers

| Index | Binary | Name     |
|-------|--------|----------|
| 0     | 000    | P0       |
| 1     | 001    | P1       |
| 2     | 010    | M0       |
| 3     | 011    | M1       |
| 4     | 100    | *unused* |
| 5     | 101    | *unused* |
| 6     | 110    | A        |
| 7     | 111    | R        |

### Other registers/storage
| Name          | Note |
|---------------|------|
| N             |      |
| T             |      |
| W             |      |
| TM1           |      |
| TP1           |      |
| Carry bits JK |      |
| Carry bits D  |      |


## Languange/Assembler/Compiler

To make it a bit easier to write programs, I have human readable instructions and a few other minimal features:

* variables can be declared and their addresses used:

```
*value = 55
RDV M1 value
RDM A
```

* lists are supported:
```
*values = [55, 56, 57]
RDV M1 value
RDM A
```
The pointer points to the first value, each value takes 16 bits so you need to add 2 to the address to get the next one
```
*values = [55, 56, 57]
RDV A value
ADV A 2         
CPY R M1              # set pointer to 2nd value
RDM A
```

* The code can have comments

```
# This is a comment
```

* Lines can be labelled. Line labels begin with `:`

```
JMZ A CASEZERO       # jump to CASEZERO is A is zero
RDV P1 CASENOTZERO   # jump to CASENOTEZERO is A is not zero
:CASEZERO
# do something if A is zero
RDV P1 CONTINUE      # jump over the not zero instructions
:CASENOTZERO
# do something if A is not zero
:CONTINUE
```
* instructions can be forced onto a clean page (256 8bit memory locations). Page labels begin with `::`. When you 
move between pages, you update date P0 but P1 just keeps on incrementing, so you cannot control where you land. see 
`pages2.prog` for and idea how to deal with this. There the instruction at 2 always jumps off the page with the target 
page stored in A and the target instruction address stored in R. Then the instruction at 4 is where you always land
and you can jump immediately to the addess in R.

```
::PAGE0
RDV P1 START0
:LEAVE0
CPY A P0         # jump to page stored in A
:LAND0
CPY R P1         # jump to instruction on this page stored in R
:START0
RDV A 1
RDV R START1     # names are all global
RDV P1 LEAVE0    

::PAGE1
RDV P1 START1
:LEAVE1
CPY A P0         # jump to page stored in A
:LAND1
CPY R P1         # jump to instruction on this page stored in R
:START1
HLT
```

### Macros

Macros simply expand inline to the instructions they are defined with. They are specified with `DEFINE` and curly braces. 

```
# head is a pointer to a pointer to some piece of data. This reads that data into A  
DEFINE READ_A {
RDV M1 head
RDM A
CPY A M1
RDM A}
```

see `turing_or.prog` for usages.

# Python UI

The python UI lists the machine instructions alongside the human readable program and while it is running
calculates what should be in the registers. In the final tested version of the computer the physical registers
have the same values, however the UI is not actually reading the registers while it is running.

![python UI.png](images%2Fpython%20UI.png)

## Test Programs

* add16bit
* fibonacci
* find_largest
* find_largest16bit
* mult
* turing_or - run a universal turing machine for a simple problem, OR on 2 bits
* subtract16bit


## TODO
 * Change computer to have clear input output lines in case I want to change the interface one day and maybe even 
implement everything in hardware.
   * 16 line address
   * 8 line input
   * 8 line output
   * 1 line read/write
   * 1 line clock pulse
 * Have special addresses for "screen" output

## Test Programs still to write

1. Paging that allows nested calls
2. Sort a list
3. Find the largest number in a list that is longer than 128 numbers



