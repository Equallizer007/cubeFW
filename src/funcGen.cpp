#include "funcGen.h"    // include the corresponding header file
#include "pinDefs.h"    // include the pin definitions
#include <Arduino.h>    // include the Arduino library
#include <ArduinoLog.h> // include the ArduinoLog library for logging functionality
#include "adc.h"

bool generatorAciveFlag = false;

// Define some constants that specify the hardware limits of the ESP32
namespace
{
    const int F_10_BIT = 80000;  // Maximum frequency for 10-bit resolution
    const int F_8_BIT = 300000;  // Maximum frequency for 8-bit resolution
    const int F_6_BIT = 1200000; // Maximum frequency for 6-bit resolution
    const int F_4_BIT = 5000000; // Maximum frequency for 4-bit resolution

    const int MIN_WIDTH_NS = 62;   // Minimum pulse width in nanoseconds
    const float ERROR_RATIO = 0.1; // Maximum allowed error ratio
}

// Initialize the output pin and its inverse
void initFunc()
{
    pinMode(PIN_GENERATOR, OUTPUT);
    digitalWrite(PIN_GENERATOR, LOW);
    pinMode(PIN_GENERATOR_INV, OUTPUT);
    digitalWrite(PIN_GENERATOR_INV, HIGH);
}

// Manually set the state of the first mosfet
void setF2(bool val)
{
    ledcDetachPin(PIN_GENERATOR);
    digitalWrite(PIN_GENERATOR, val);
}

// Manually set the state of the second mosfet
void setF1(bool val)
{
    ledcDetachPin(PIN_GENERATOR_INV);
    digitalWrite(PIN_GENERATOR_INV, val);
}

void setOutputOff()
{
    Log.info("stopping output\n");
    generatorAciveFlag = false;
    detachInterrupt(PIN_GENERATOR);
    ledcDetachPin(PIN_GENERATOR);
    ledcDetachPin(PIN_GENERATOR_INV);
    digitalWrite(PIN_GENERATOR, LOW);
    digitalWrite(PIN_GENERATOR_INV, LOW);
}

// Check if thethe expected pulse length error is bigger then the accepted Error
// Arguments:
//   pulseLength: pulse width in nanoseconds
// Returns: true if the error is smaller then the treshold, false otherwise
bool checkExpectedError(long pulselength)
{
    int expError = pulselength - (pulselength / MIN_WIDTH_NS) * MIN_WIDTH_NS;
    float expErrorRatio = (float)expError / pulselength;
    //Log.notice("expError: %ins (%F)\n", expError, expErrorRatio);
    if (expErrorRatio > ERROR_RATIO)
    {
        Log.error("expected pulse length error to high!\n");
        return false;
    }
    return true;
}

// Check if the pulse widths are less than the minimum allowed pulse width
// Arguments:
//   onTime: pulse width in nanoseconds
//   offTime: pulse width in nanoseconds
// Returns: true if pulse widths are valid, false otherwise
bool checkPulseWidths(unsigned long onTime, unsigned long offTime)
{
    // Check if the pulse widths are less than the minimum allowed pulse width
    if (onTime < MIN_WIDTH_NS || offTime < MIN_WIDTH_NS)
    {
        Log.error("ontime and offtime must not be < %i!\n", MIN_WIDTH_NS);
        return false;
    }
    return true;
}

// Calculate the frequency of the output signal
// Arguments:
//   onTime: pulse width in nanoseconds
//   offTime: pulse width in nanoseconds
// Returns: frequency of the output signal
long calcFrequency(unsigned long onTime, unsigned long offTime)
{
    return 1000000000 / (onTime + offTime);
}

// Calculate the dutycycle of the output signal
// Arguments:
//   onTime: pulse width in nanoseconds
//   offTime: pulse width in nanoseconds
//   bitres: bit resolution of the output signal
// Returns: dutycycle of the output signal
unsigned calcDuty(unsigned long onTime, unsigned long offTime, unsigned bitres)
{
    return (onTime * pow(2, bitres)) / (onTime + offTime);
}

// Get the bit resolution of the output signal based on the calculated frequency
// Arguments:
//   freq: frequency of the output signal
//   onTime: pulse width in nanoseconds
//   offTime: pulse width in nanoseconds
// Returns: bit resolution of the output signal
unsigned getBitResolution(long freq, long onTime, long offTime)
{
    if (freq <= F_10_BIT)
        return (10);
    else if (freq <= F_8_BIT)
        return (8);
    else if (freq < F_6_BIT)
        return (6);
    else if (freq < F_4_BIT)
        return (4);
    else if (onTime == offTime)
        return (1);
    else
    {
        Log.error("requested frequency too high!\n");
        return 0;
    }
}

// Set the output signal
// Arguments:
//   freq: frequency of the output signal
//   bitres: bit resolution of the output signal
//   duty: dutycycle of the output signal
void setOutput(unsigned long freq, unsigned bitres, unsigned duty)
{
    Log.notice("freq: %lhz bitres %l duty: %u\n", freq, bitres, duty);
    generatorAciveFlag = true;
    // Make sure outputpins are available and low
    setF1(false);
    setF2(false);

    // attach output pins to timer 0 and set frequency and dutycycle
    ledcAttachPin(PIN_GENERATOR, 0);
    ledcSetup(0, freq, bitres);
    ledcAttachPin(PIN_GENERATOR_INV, 0);
    GPIO.func_out_sel_cfg[PIN_GENERATOR_INV].inv_sel = 1;
    ledcSetup(0, freq, bitres);
    ledcWrite(0, duty);
}

// Set the function generator to a specific frequency and duty cycle
// Arguments:
//   onTime: pulse width in nanoseconds
//   offTime: pulse width in nanoseconds
// Returns: true if successful, false otherwise
bool setFunc(unsigned long onTime, unsigned long offTime)
{
    if (onTime >= 1000 && offTime >= 1000)
    {
        Log.notice("set ontime: %Fµs offtime: %Fµs\n", onTime / 1000.0, offTime / 1000.0);
    }
    else
    {
        Log.notice("set ontime: %lns offtime: %lns\n", onTime, offTime);
    }
    // Check if the onTime or offTime is 0, and set the output pin and its inverse accordingly
    if (onTime == 0)
    {
        Log.warning("ontime is 0 -> set output off \n");
        setOutputOff();
        return true;
    }
    if (offTime == 0)
    {
        Log.warning("offtime is 0 -> set output on \n");
        setOutputOff();
        return true;
    }

    // Check if the pulse widths are less than the minimum allowed pulse width
    if (!checkPulseWidths(onTime, offTime))
    {
        return false;
    }

    // Check if the expected error ratio is above the maximum allowed error ratio
    if (!checkExpectedError(onTime) || !checkExpectedError(offTime))
    {
        return false;
    }

    // Calculate the frequency of the output signal
    long freq = calcFrequency(onTime, offTime);
    //Log.notice("frequency: %lhz\n", freq);

    // Set the bit resolution of the output signal based on the calculated frequency
    unsigned bitres = getBitResolution(freq, onTime, offTime);
    //Log.notice("bit resolution: %i\n", bitres);

    // Calculate the duty cycle of the output signal
    unsigned duty = calcDuty(onTime, offTime, bitres);
    if (duty == 0)
    {
        Log.error("dutycycle must not be 0!\n");
        return false;
    }

    // Set the output signal
    setOutput(freq, bitres, duty);
    activateADCinterrupt();
    return true;
}