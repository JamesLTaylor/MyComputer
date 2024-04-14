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
* In1 = R/W flag
* In2-5 = data from computer
* Out1 = clock
* Out2-Out4 = bus address
* Out 5-8 = data read from memory

## Memory Bus

8 blocks of 4 bits each, numbered 0-7

 * 0, 1, 2, 3 = 16 bits of address
 * 4, 5 = 8 bits of data from memory
 * 6, 7 = 8 bits of data from MyComputer

## Cycle
 * read 0, 1, 2, 3 into address pointer
 * read In1 into R/W
 * if R
   * read data at address pointer and put it on 4, 5
 * if W
   * read data at 6,7 and write it to address pointer and
 * Toggle clock

## Computer Cycle
1. off->on: transition to next state 0
2. off->on: temp register write
3. off>on: transition to state 1
4. off-on: final register/mem write
