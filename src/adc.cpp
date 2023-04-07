#include "pinDefs.h"
#include "Arduino.h"
#include <ArduinoLog.h> // include the ArduinoLog library for logging functionality
#include "SPI.h"
#include "soc/spi_struct.h"
#include "adc.h"

// VSPI are pins 19, 18
SPIClass SPI_ADC(VSPI);

volatile uint16_t adcVoltage = 0;
volatile bool adcFlagL = false;
volatile bool adcFlagH = false;
volatile bool adcResetCounterFlag = false;
float lowerThr = 0, upperThr = 0;
unsigned auto_sens = 10;
unsigned adc_report_interval = 1000;
unsigned adcCounterL = 0;
unsigned adcCounterH = 0;

uint16_t adcThresholdL = calcADCInputVoltage(5);
uint16_t adcThresholdH = calcADCInputVoltage(30);


namespace
{
    SPISettings settings(26000000L, MSBFIRST, SPI_MODE0);

    void IRAM_ATTR adcISR()
    {
        if (adcResetCounterFlag){
            adcCounterH = 0;
            adcCounterL = 0;
            adcFlagH = false;
            adcFlagL = false;
            adcResetCounterFlag = false;
        }
        uint16_t adcVoltage2 = _readADC();
        //Serial.println(adcVoltage2);
        if (adcVoltage2 < adcThresholdL)
        {
            if (++adcCounterL >= auto_sens){
                adcFlagL = true;
            }
        }
        else if (adcVoltage2 > adcThresholdH)
        {
            if (++adcCounterH >= auto_sens){
                adcFlagH = true;
            }
        }
        else{
            adcCounterH--;
            adcCounterL--;
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
    Log.trace("thresholdH: %d thresholdL: %d\n", adcThresholdH, adcThresholdL);
    SPI_ADC.begin();
    pinMode(PIN_ADC, OUTPUT);
    digitalWrite(PIN_ADC, HIGH);
    SPI_ADC.beginTransaction(settings);
    long ttimer = millis();
    for (;;)
    {
        adcVoltage = _readADC();
        if (millis()-ttimer > adc_report_interval){
            if (adcVoltage == 0){
                //ADC should never read exact 0
                Log.error("ADC reads 0V: This should never happen! Check the connection!\n");
            }
            Serial.printf("<ADC> raw:%d calc:%.2fV \n",adcVoltage, calcVoltage(adcVoltage));
            ttimer = millis();
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
