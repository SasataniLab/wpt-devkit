#include "globals.h"

// Define global objects
PAC1720 Sense;
MCP45HVX1 digiPot(0x3C);

// Initialize global resistor values
uint8_t ResVals[] = {27, 27};

// Initialize global variables for current frequency and voltage
unsigned long long currentFrequency = 0;
float currentVoltage = 0.0;
float iLimit = 0;
float vMin = 1.0;
bool powerOn = false;