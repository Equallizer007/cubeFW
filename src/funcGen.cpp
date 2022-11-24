#include "funcGen.h"
#include "pinDefs.h"
#include <Arduino.h>

namespace
{
    // ESP32 Hardware Limits
    const int F_10_BIT = 80000;
    const int F_8_BIT = 300000;
    const int F_6_BIT = 1200000;
    const int F_4_BIT = 5000000;

    const int MIN_WIDTH_NS = 62;
    const float ERROR_RATIO = 0.1;

}

// arguments in ns
bool setFunc(unsigned long onTime, unsigned long offTime)
{
    if (onTime < MIN_WIDTH_NS || offTime < MIN_WIDTH_NS)
    {
        Serial.printf("ERROR: ontime and offtime must not be < %i!\n", MIN_WIDTH_NS);
        return false;
    }
    int expErrorOn = onTime - (onTime / MIN_WIDTH_NS) * MIN_WIDTH_NS;
    int expErrorOff = offTime - (offTime / MIN_WIDTH_NS) * MIN_WIDTH_NS;
    float expErrorOnRatio = (float)expErrorOn / onTime;
    float expErrorOffRatio = (float)expErrorOff / offTime;

    Serial.printf("INFO: expError: on: %ins (%f) off %ins (%f)\n",
                  expErrorOn, expErrorOnRatio, expErrorOff, expErrorOffRatio);
    if (expErrorOnRatio > ERROR_RATIO || expErrorOffRatio > ERROR_RATIO)
    {
        Serial.println("ERROR: Expected frequency error to high!");
        return false;
    }

    long freq = 1000000000 / (onTime + offTime);
    // set bit resolution;
    unsigned bitres;
    if (freq <= F_10_BIT)
        bitres = 10;
    else if (freq <= F_8_BIT)
        bitres = 8;
    else if (freq < F_6_BIT)
        bitres = 6;
    else if (freq < F_4_BIT)
        bitres = 4;
    else if (onTime == offTime)
        bitres = 1;
    else
    {
        Serial.println("ERROR: requested frequency to high!");
        return false;
    }

    unsigned duty = (onTime * pow(2, bitres)) / (onTime + offTime);
    if (duty == 0)
    {
        Serial.println("ERROR: dutycycle must not be 0!");
        return false;
    }
    Serial.printf("INFO: set freq: %lu bitres %lu duty: %u\n", freq, bitres, duty);

    // Make sure outputpin is available and low
    ledcDetachPin(PIN_GENERATOR);
    digitalWrite(PIN_GENERATOR, LOW);

    // attach pin to timer 0 and set frequency and dutycycle
    ledcAttachPin(PIN_GENERATOR, 0);
    ledcSetup(0, freq, bitres);
    ledcWrite(0, duty);
    return true;
}