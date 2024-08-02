#ifndef GLOBALS_H
#define GLOBALS_H

#include <Arduino.h>
#include <PAC1720.h>
#include <MCP45HVX1.h>

// Global PAC1720 sensor
extern PAC1720 Sense;

// Global MCP45HVX1 digital potentiometer
extern MCP45HVX1 digiPot;

// Global resistor values array
extern uint8_t ResVals[];

// Define constants
const uint32_t SERIAL_BAUD_RATE = 57600;
const uint8_t DCDC_ENABLE_PIN = 2;
const uint8_t RES_VALS[] = {27, 27};
const char SCPI_IDN_RESPONSE[] = "SasataniLab,wpt-devkit-v0.1,000001,0.1.0\n";
const unsigned long PERIOD = 10; // Wait PERIOD ms between prints

// Global variables to store the current frequency and voltage
extern unsigned long long currentFrequency;
extern float currentVoltage;
extern float iLimit;
extern float vMin;
extern bool powerOn;

#endif // GLOBALS_H