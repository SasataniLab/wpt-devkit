#ifndef SENSEIV_H
#define SENSEIV_H

#include <Arduino.h>

extern float Bus[2];
extern float Current[2];

void sense_iv(char* outputBuffer, size_t bufferSize);
void haltPower();

#endif // SENSEIV_H