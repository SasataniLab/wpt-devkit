#include "SCPICommands.h"
#include "globals.h"
#include "initDevKit.h"

// Custom function to convert unsigned long long to string
String ullToString(unsigned long long value) {
    char buffer[21]; // Buffer to hold max 64-bit integer value
    sprintf(buffer, "%llu", value);
    return String(buffer);
}

void process_scpi_command(String command) {
    command.trim();

    if (command.equalsIgnoreCase("*IDN?")) {
        // Device identification
        Serial.print(SCPI_IDN_RESPONSE);
    } else if (command.startsWith("FREQ ")) {
        // Set frequency
        unsigned long long target_f = command.substring(5).toInt();
        set_frequency(target_f);
        Serial.println("OK");
    } else if (command.equalsIgnoreCase("FREQ?")) {
        // Get current frequency
        Serial.print("FREQ = ");
        Serial.println(ullToString(currentFrequency)); // Use custom conversion function
    } else if (command.startsWith("VOLT ")) {
        // Set voltage
        float target_v = command.substring(5).toFloat();
        set_DC_voltage(target_v);
        Serial.println("OK");
    } else if (command.equalsIgnoreCase("VOLT?")) {
        // Get current voltage
        Serial.print("VOLT = ");
        Serial.println(currentVoltage, 2); // Print with 2 decimal places
    } else if (command.equalsIgnoreCase("VOLT_STATUS?")) {
        // Get voltage status
        Serial.print("VOLT_STATUS = ");
        Serial.println(voltageOn ? "ON" : "OFF");
    } else if (command.equalsIgnoreCase("WIP?")) {
        // Read wiper register
        int wiperValue = digiPot.readWiper();
        Serial.print("WIP = ");
        Serial.println(wiperValue);
    } else if (command.equalsIgnoreCase("POWER ON")) {
        // Power on the module
        power_on();
        Serial.println("MODULE POWERED ON");
    } else if (command.equalsIgnoreCase("POWER OFF")) {
        // Power off the module
        power_off();
        Serial.println("MODULE POWERED OFF");
    } else {
        Serial.println("ERROR: Command not recognized");
    }
}