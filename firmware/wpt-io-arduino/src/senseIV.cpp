#include "SenseIV.h"
#include "globals.h"
#include "UtilFunctions.h"
#include "initDevKit.h"

// Define the bus and current arrays
float Bus[2] = { 0 };
float Current[2] = { 0 };

void sense_iv(char* outputBuffer, size_t bufferSize) {
  // Get bus voltages and sensing voltages
  for (int i = 0; i < 2; i++) {
    Bus[i] = Sense.GetBusVoltage(i);                     // Get bus voltage
    Current[i] = Sense.GetSenseVoltage(i) / ResVals[i];  // Get sensing voltage
  }

  // Calculate sense values: logic voltage, logic current, power voltage, power current
  float sense[] = { Bus[0], Current[0], Bus[1], Current[1] };
  size_t count = sizeof(sense) / sizeof(sense[0]);

  // Convert sense values to a formatted string
  floats2str(outputBuffer, bufferSize, sense, count);

  if (Current[1] > iLimit) {
    haltPower();
  }
}

void haltPower() {
  power_off();
  int set_DC_voltage(vMin);
}