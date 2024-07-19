#ifndef INITDEVKIT_H
#define INITDEVKIT_H

#include <Arduino.h>
#include "si5351.h"

extern Si5351 si5351;

void init_wpt_devkit();
void power_on();
void power_off();
int set_frequency(unsigned long long target_f);
int set_DC_voltage(float target_v);

#endif // INITDEVKIT_H