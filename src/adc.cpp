#include "pinDefs.h"
#include "Arduino.h"
#include <ArduinoLog.h> // include the ArduinoLog library for logging functionality
#include "SPI.h"
#include "soc/spi_struct.h"
#include "adc.h"

// VSPI are pins 19, 18
SPIClass SPI_ADC(VSPI);

namespace
{
    double adcVoltage = 0;

    SPISettings settings(26000000L, MSBFIRST, SPI_MODE0);

    void IRAM_ATTR adcISR()
    {
        adcVoltage = readADC();
        if (adcVoltage > 3.0)
        {
            Serial.println("Hi");
            detachInterrupt(PIN_GENERATOR);
        }
    }
}

void activateADCinterrupt()
{
    attachInterrupt(PIN_GENERATOR, adcISR, RISING);
}

// Initiliazie the SPI communication
void initADC()
{
    SPI_ADC.begin();
    pinMode(PIN_ADC, OUTPUT);
    digitalWrite(PIN_ADC, HIGH);
    SPI_ADC.beginTransaction(settings);
    Log.notice("ADC started... %D\n", readADC());
}
