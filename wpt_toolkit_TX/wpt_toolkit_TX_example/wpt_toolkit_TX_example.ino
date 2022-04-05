#include <Arduino.h>
#include <MCP45HVX1.h>
#include <PAC1720.h>
#include "si5351.h"
#include "Wire.h"
#include <avr/sleep.h>

#define DCDC_ENABLE 2
PAC1720 Sense; //Instatiate sensor

unsigned long Period = 1000; //Wait 1 second between prints
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
  if(!i2c_found)
  {
    Serial.println("Device not found on I2C bus!");
  }

  Sense.begin(); //Basic setup
  while(!Serial); //Wait for serial to start

  // Set CLK0 to output 14 MHz
  digiPot.begin();

  set_frequency(180e3);
  set_DC_voltage(10);
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
  float Bus[2] = {0}; //Setup array for bus voltages
  float Current[2] = {0}; //Setup array for current values

  // String Data;
  char Data[100]; //String to concatonate data into for single print

  for(int i = 0; i < 2; i++) {
    Bus[i] = Sense.GetBusVoltage(i); //Get bus voltage
    Current[i] = Sense.GetSenseVoltage(i); //Get sensing voltage
    // Current[i] = Sense.GetCurrent(i, ResVals[i]); //Get calculated current
  }
  sprintf(Data, "Vbus1 = %dmV\tVsense1 = %+dmA\tVbus2 = %dmV\tVsense2 = %+dmA\n", int(Bus[0]*1000.0), int(Current[0]/ResVals[0]*1000), int(Bus[1]*1000.0), int(Current[1]/ResVals[1]*1000)); //Format string for sufficient resolution for each value and +/- indication for clarity on current 
  Serial.print(Data); //Print out preformatted data string
  // Serial.println(Current[0], 8); //DEBUG!
  delay(Period);

}

int set_frequency(unsigned long long target_f) {
  si5351.set_freq(100 * target_f, SI5351_CLK0);
  si5351.update_status();
}

int set_DC_voltage(int target_v) {
  float target_r = ((target_v / 0.9) - 1) * 3.9e3 - 100;

  digiPot.writeWiper(round(target_r / 392));

  Serial.println("\n----- Wiper Register ----");
  Serial.print("readWiper: ");
  Serial.println(digiPot.readWiper());

  return round(target_r / 392);
}
