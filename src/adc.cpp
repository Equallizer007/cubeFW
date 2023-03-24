#include "pinDefs.h"
#include "Arduino.h"
#include <ArduinoLog.h> // include the ArduinoLog library for logging functionality
#include "SPI.h"
#include "soc/spi_struct.h"
#include "adc.h"

// VSPI are pins 19, 18
SPIClass SPI_ADC(VSPI);

volatile uint16_t adcVoltage = 0;
volatile bool adcISRflag = false;
uint16_t gapVoltageThreshold = calcADCInputVoltage(30);

namespace
{
    SPISettings settings(26000000L, MSBFIRST, SPI_MODE0);

    void IRAM_ATTR adcISR()
    {
        if (adcVoltage < gapVoltageThreshold)
        {
            adcISRflag = true;
        }
    }
}

void activateADCinterrupt()
{
    attachInterrupt(PIN_GENERATOR, adcISR, RISING);
}

void adcTask(void *param)
{
    Log.trace("adcTask started on core %d ...\n", xPortGetCoreID());
    SPI_ADC.begin();
    pinMode(PIN_ADC, OUTPUT);
    digitalWrite(PIN_ADC, HIGH);
    SPI_ADC.beginTransaction(settings);
    long ttimer = millis();
    for (;;)
    {
        adcVoltage = _readADC();
        if (millis()-ttimer > 3000){
            Serial.printf("<ADC> raw:%d calc:%.2f \n",adcVoltage, calcVoltage(adcVoltage));
            ttimer = millis();
        }
        
        if (adcISRflag)
        {
            //Serial.println("Hi Threshold");
            adcISRflag = false;
        }
    }
    Log.trace("adcTask closed ...\n");
}

// Initiliazie the SPI communication
void adcInit()
{
    xTaskCreatePinnedToCore(
        adcTask,   /* Task function. */
        "adcTask", /* String with name of task. */
        10000,     /* Stack size in bytes. */
        NULL,      /* Parameter passed as input of the task */
        0,         /* Priority of the task. */
        NULL,      /* Task handle. */
        0);        /* which core to run */
    Log.notice("ADC started... %F\n", adcVoltage);
}
