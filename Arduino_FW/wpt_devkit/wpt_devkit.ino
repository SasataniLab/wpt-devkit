#include <Arduino.h>
#include "globals.h"
#include "initDevKit.h"
#include "SenseIV.h"
#include "SCPICommands.h"

// Buffer to concatenate data for a single print
char data[100];

void setup() {
  iLimit = 0.8;
  vMin = 1;
  float vInit = 3;
  float freqInit = 6.78e6;
  Serial.begin(SERIAL_BAUD_RATE);
  init_wpt_devkit();
  set_frequency(freqInit);
  set_DC_voltage(vInit);
  power_on();
}

void loop() {
  static unsigned long previousMillis = 0;
  unsigned long currentMillis = millis();

  // Check if the specified period has elapsed
  if (currentMillis - previousMillis >= PERIOD) {
    // Update the stored time
    previousMillis = currentMillis;

    sense_iv(data, sizeof(data));  // Sense and format data

    // Print out preformatted data string
    Serial.print(data);
  }

  // Check for SCPI commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    process_scpi_command(command);
  }
}