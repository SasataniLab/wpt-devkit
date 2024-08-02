#include "initDevKit.h"
#include "globals.h"
#include "PAC1720.h"

// Define global objects
Si5351 si5351;

void init_wpt_devkit() {
  bool i2c_found;
  pinMode(DCDC_ENABLE_PIN, OUTPUT);
  digitalWrite(DCDC_ENABLE_PIN, LOW);
  i2c_found = si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0);

  if (!i2c_found) {
    Serial.println("Device not found on I2C bus!");
    while (1)
      ;  // Halt execution
  }
  digiPot.begin();
}

void power_on() {
  digitalWrite(DCDC_ENABLE_PIN, HIGH);
  powerOn = true;  // Update the voltage status flag
}

void power_off() {
  digitalWrite(DCDC_ENABLE_PIN, LOW);
  powerOn = false;  // Update the voltage status flag
}

int set_frequency(unsigned long long target_f) {
  si5351.set_freq(100 * target_f, SI5351_CLK0);
  si5351.update_status();
  currentFrequency = target_f;  // Update the global frequency variable
  return 0;                     // Add return value for function signature consistency
}

int set_DC_voltage(float target_v) {
  float target_r = ((target_v / 0.9) - 1) * 3.9e3 - 100;
  digiPot.writeWiper(round(target_r / 392));
  currentVoltage = target_v;  // Update the global voltage variable
  return round(target_r / 392);
}