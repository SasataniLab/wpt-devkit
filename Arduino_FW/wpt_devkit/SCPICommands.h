#ifndef SCPICOMMANDS_H
#define SCPICOMMANDS_H

#include <Arduino.h>

void process_scpi_command(String command);
void addErrorToQueue(String error);
void pollForErrors();
String ullToString(unsigned long long value);

// Constants
#endif // SCPICOMMANDS_H