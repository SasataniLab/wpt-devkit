## Introduction

This document describes the SCPI commands implemented for the wpt-devkit-v0.1. These commands allow for the control and monitoring of the device's state and parameters via a serial interface.

## UART Setting
- **Baudrate:** 57600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Flow Control:** None
- **Termination Character:** Newline (`\n`)

## Command Overview

- [Identification](#identification)
- [Frequency Commands](#frequency-commands)
- [Voltage Commands](#voltage-commands)
- [Power Control Commands](#power-control-commands)
- [Error Handling](#error-handling)
- [Command Error Handling](#command-error-handling)
- [Periodic Polling](#periodic-polling)

## Identification

### `*IDN?`

- **Description:** Device identification. The returned string follows the basic convention of SCPI commands
  > Manifacturer, hardware model, serial number, firmware version
  
- **Usage:** `*IDN?`
  
  The command is sent without additional parameters and requests the device to respond with its identification details.

- **Response:** `SasataniLab,wpt-devkit-v0.1,000001,0.1.0`
  - **Developer:** SasataniLab
  - **Hardware Model:** wpt-devkit-v0.1
  - **Serial Number:** 000001 (fixed, not really used yet)
  - **Firmware Version:** 0.1.0

  **Example:**

  Sending the command:
  ```plaintext
  *IDN?
  ```

  The device responds with:
  ```plaintext
  SasataniLab,wpt-devkit-v0.1,000001,0.1.0
  ```

## Frequency Commands

### `FREQ <value>`

- **Description:** Set the operating frequency.
- **Usage:** `FREQ <value>`
  - `<value>`: Desired frequency in Hz (Range: 1 Hz to 30 MHz).
- **Response:** `OK`

**Example:** `FREQ 6780000` (Sets the frequency to 6.78 MHz)

### `FREQ?`

- **Description:** Query the current operating frequency.
- **Usage:** `FREQ?`
- **Response:** `FREQ=<value>`
  - `<value>`: Current frequency in Hz.

**Example:** `FREQ?` → `FREQ=6780000`

## Voltage Commands

### `VOLT <value>`

- **Description:** Set the operating voltage.
- **Usage:** `VOLT <value>`
  - `<value>`: Desired voltage in Volts.
- **Response:** `OK`

**Example:** `VOLT 5.0` (Sets the voltage to 5.0 Volts)

### `VOLT?`

- **Description:** Query the current operating voltage.
- **Usage:** `VOLT?`
- **Response:** `VOLT=<value>`
  - `<value>`: Current voltage in Volts with 2 decimal places.

**Example:** `VOLT?` → `VOLT=5.00`

### `WIP?`

- **Description:** Read the current wiper register value for controlling voltage. This command is primarily used for debugging purposes.
- **Usage:** `WIP?`
- **Response:** `WIP=<value>`
  - `<value>`: Current wiper register value.

**Example:** `WIP?` → `WIP=128`

## Power Control Commands

### `POWER ON`

- **Description:** Turn on the module.
- **Usage:** `POWER ON`
- **Response:** `MODULE POWERED ON`

### `POWER OFF`

- **Description:** Turn off the module.
- **Usage:** `POWER OFF`
- **Response:** `MODULE POWERED OFF`

### `POWER:STATE?`

- **Description:** Query the power state (whether it is on or off).
- **Usage:** `POWER:STATE?`
- **Response:** `POWER:STATE=<status>`
  - `<status>`: `ON` if the power is on, `OFF` if the power is off.

**Example:** `POWER:STATE?` → `POWER:STATE=ON`

## Error Handling

### `SYST:ERR?`

- **Description:** Query the error queue for the latest error message and code. Errors are maintained in a queue, and querying this command will retrieve and remove the oldest error in the queue.
- **Usage:** `SYST:ERR?`
- **Response:** `<error_code>, "<error_message>"`
  - `<error_code>`: Numerical code representing the error type.
  - `<error_message>`: Description of the error.

**Example:**

  Sending the command:
  ```plaintext
  SYST:ERR?
  ```

  If there was a data range error, the device might respond with:
  ```plaintext
  -222, "Data out of range"
  ```

## Command Error Handling

If an unrecognized or malformed command is received, the device responds with:

**Response:** `-100, "Command error"`

## Periodic Polling

### Error Polling

- **Description:** The device periodically checks for errors and updates the error queue. This happens at regular intervals to ensure that all errors are captured and can be reviewed when necessary.
- **Polling Interval:** 5000 milliseconds (5 seconds)

**Implementation Notes:**
  
- The device will query for errors every 5 seconds and handle any discovered errors accordingly.
- This ensures that the system remains aware of its state and can provide up-to-date error messages.

**Example:**

Every 5 seconds, the device will internally run the equivalent of:
```plaintext
SYST:ERR?
```
And handle the result to update the error state and maintain the error queue.