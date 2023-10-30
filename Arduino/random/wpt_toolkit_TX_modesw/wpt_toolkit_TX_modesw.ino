#include <Arduino.h>
#include <MCP45HVX1.h>
#include <PAC1720.h>
#include "si5351.h"
#include "Wire.h"

#define DCDC_ENABLE 2
PAC1720 Sense; //Instatiate sensor

unsigned long Period = 1; //Wait 1 second between prints
uint8_t ResVals[2] = {27, 27}; //Mapping of resistor values [mOhms]

MCP45HVX1 digiPot(0x3C);
Si5351 si5351;

void setup()
{
  bool i2c_found;
  pinMode(DCDC_ENABLE, OUTPUT);
  digitalWrite(DCDC_ENABLE, LOW);

  Serial.begin(57600);
  i2c_found = si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0);
  if (!i2c_found)
  {
    Serial.println("Device not found on I2C bus!");
  }

  Sense.begin(); //Basic setup
  while (!Serial); //Wait for serial to start

  // Set CLK0 to output 14 MHz
  digiPot.begin();

  //set_frequency(180e3);
  //set_frequency(6.78e6);
  set_frequency(6.94e6);
  set_DC_voltage(5);
  digitalWrite(DCDC_ENABLE, HIGH);
  delay(1000);
  Serial.println("Input voltage");
  Serial.println(Sense.GetSenseVoltage(1));

  Serial.println("\n----- Wiper Register ----");
  Serial.print("readWiper: ");
  Serial.println(digiPot.readWiper());

  delay(500);
}

void loop()
{

  
  set_frequency(6.94e6);
  set_DC_voltage(4);
  delay(Period);
  set_frequency(4.91e6);
  set_DC_voltage(13);
  delay(Period);
  set_frequency(5.54e6);
  set_DC_voltage(11);
  delay(Period);
}

int set_frequency(unsigned long long target_f) {
  si5351.set_freq(100 * target_f, SI5351_CLK0);
  si5351.update_status();
  return 0;
}

int set_DC_voltage(int target_v) {
  float target_r = ((target_v / 0.9) - 1) * 3.9e3 - 100;

  digiPot.writeWiper(round(target_r / 392));

  Serial.println("\n----- Wiper Register ----");
  Serial.print("readWiper: ");
  Serial.println(digiPot.readWiper());

  return round(target_r / 392);
}
