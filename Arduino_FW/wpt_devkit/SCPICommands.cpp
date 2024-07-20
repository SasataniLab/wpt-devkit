#include "SCPICommands.h"
#include "globals.h"
#include "initDevKit.h"

// Error queue definitions
const int ERROR_QUEUE_SIZE = 10;
String errorQueue[ERROR_QUEUE_SIZE];
int errorQueueHead = 0;

// Custom function to convert unsigned long long to string
String ullToString(unsigned long long value) {
    char buffer[21]; // Buffer to hold max 64-bit integer value
    sprintf(buffer, "%llu", value);
    return String(buffer);
}

// Function to add errors to the queue
void addErrorToQueue(String error) {
    if (errorQueueHead < ERROR_QUEUE_SIZE) {
        errorQueue[errorQueueHead++] = error;
    } else {
        // Error queue is full; handle overflow if necessary
    }
}

// Function to handle SCPI commands
void process_scpi_command(String command) {
    command.trim();

    if (command.equalsIgnoreCase("*IDN?")) {
        // Device identification
        Serial.print(SCPI_IDN_RESPONSE);
    } else if (command.startsWith("FREQ ")) {
        // Set frequency
        unsigned long long target_f = command.substring(5).toInt();
        if (target_f >= 1 && target_f <= 30000000) {
            set_frequency(target_f);
            Serial.println("OK");
        } else {
            addErrorToQueue("-222, \"Data out of range\"");
            Serial.println("-222, \"Data out of range\"");
        }
    } else if (command.equalsIgnoreCase("FREQ?")) {
        // Get current frequency
        Serial.print("FREQ=");
        Serial.println(ullToString(currentFrequency)); // Use custom conversion function
    } else if (command.startsWith("VOLT ")) {
        // Set voltage
        float target_v = command.substring(5).toFloat();
        if (target_v >= 0.0 && target_v <= 10.0) { // Example voltage range check
            set_DC_voltage(target_v);
            Serial.println("OK");
        } else {
            addErrorToQueue("-222, \"Data out of range\"");
            Serial.println("-222, \"Data out of range\"");
        }
    } else if (command.equalsIgnoreCase("VOLT?")) {
        // Get current voltage
        Serial.print("VOLT=");
        Serial.println(currentVoltage, 2); // Print with 2 decimal places
    } else if (command.equalsIgnoreCase("WIP?")) {
        // Read wiper register
        int wiperValue = digiPot.readWiper();
        Serial.print("WIP=");
        Serial.println(wiperValue);
    } else if (command.equalsIgnoreCase("POWER ON")) {
        // Power on the module
        power_on();
        Serial.println("MODULE POWERED ON");
    } else if (command.equalsIgnoreCase("POWER OFF")) {
        // Power off the module
        power_off();
        Serial.println("MODULE POWERED OFF");
    } else if (command.equalsIgnoreCase("POWER:STATE?")) {
        // Get power state
        Serial.print("POWER:STATE=");
        Serial.println(powerOn ? "ON" : "OFF");
    } else if (command.equalsIgnoreCase("SYST:ERR?")) {
        // Return the latest error
        if (errorQueueHead == 0) {
            Serial.println("0, \"No error\"");
        } else {
            Serial.println(errorQueue[--errorQueueHead]);
            errorQueue[errorQueueHead] = "";
        }
    } else {
        addErrorToQueue("-100, \"Command error\"");
        Serial.println("-100, \"Command error\"");
    }
}

void pollForErrors() {
    // Internal error polling logic
    // This function should be called periodically to simulate error checking
    Serial.println("Polling for errors... (for internal logging only)");
}