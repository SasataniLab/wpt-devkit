# wpt-devkit-v0.1 SCPI Command Set

## UART setting
- Baudrate: 57600

## Introduction

This document describes the SCPI (Standard Commands for Programmable Instruments) commands implemented for the wpt-devkit-v0.1. These commands allow for the control and monitoring of the device's state and parameters via a serial interface.

## Identification

### `*IDN?`

- **Description**: Query device identification.
- **Usage**: `*IDN?`
- **Response**: `wpt-devkit-v0.1`

## Frequency Commands

### `FREQ <value>`

- **Description**: Set the operating frequency.
- **Usage**: `FREQ <value>`
  - `<value>`: Desired frequency in Hz.
- **Response**: `OK`
  
  **Example**: `FREQ 6780000` (Sets the frequency to 6.78 MHz)

### `FREQ?`

- **Description**: Query the current operating frequency.
- **Usage**: `FREQ?`
- **Response**: `FREQ = <value>`
  - `<value>`: Current frequency in Hz.
  
  **Example**: `FREQ?` → `FREQ = 6780000`

## Voltage Commands

### `VOLT <value>`

- **Description**: Set the operating voltage.
- **Usage**: `VOLT <value>`
  - `<value>`: Desired voltage in Volts.
- **Response**: `OK`
  
  **Example**: `VOLT 5.0` (Sets the voltage to 5.0 Volts)

### `VOLT?`

- **Description**: Query the current operating voltage.
- **Usage**: `VOLT?`
- **Response**: `VOLT = <value>`
  - `<value>`: Current voltage in Volts with 2 decimal places.
  
  **Example**: `VOLT?` → `VOLT = 5.00`

## Wiper Commands

### `WIP?`

- **Description**: Read the current wiper register value.
- **Usage**: `WIP?`
- **Response**: `WIP = <value>`
  - `<value>`: Current wiper register value.
  
  **Example**: `WIP?` → `WIP = 128`

## Power Control Commands

### `POWER ON`

- **Description**: Turn on the module.
- **Usage**: `POWER ON`
- **Response**: `MODULE POWERED ON`

### `POWER OFF`

- **Description**: Turn off the module.
- **Usage**: `POWER OFF`
- **Response**: `MODULE POWERED OFF`

## Voltage Status

### `VOLT_STATUS?`

- **Description**: Query the voltage status (whether it is on or off).
- **Usage**: `VOLT_STATUS?`
- **Response**: `VOLT_STATUS = <status>`
  - `<status>`: `ON` if the voltage is on, `OFF` if the voltage is off.
  
  **Example**: `VOLT_STATUS?` → `VOLT_STATUS = ON`

## Command Error Handling

If an unrecognized or malformed command is received, the device responds with:

**Response**: `ERROR: Command not recognized`