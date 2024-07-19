#include "UtilFunctions.h"

void floats2str(char* outputBuffer, size_t bufferSize, const float* values, size_t count) {
    char temp[20];  // Temporary buffer for each float conversion

    // Ensure the output buffer starts as an empty string
    outputBuffer[0] = '\0';

    for (size_t i = 0; i < count; i++) {
        // Convert float to string with width 6 and 2 decimal places
        dtostrf(values[i], 6, 2, temp);

        // Append the formatted string to the output buffer
        strncat(outputBuffer, temp, bufferSize - strlen(outputBuffer) - 1);

        // Append a comma and space if it's not the last element
        if (i < count - 1) {
            strncat(outputBuffer, ", ", bufferSize - strlen(outputBuffer) - 1);
        }
    }

    // Append a newline character at the end
    strncat(outputBuffer, "\n", bufferSize - strlen(outputBuffer) - 1);
}