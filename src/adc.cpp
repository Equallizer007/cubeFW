#include "pinDefs.h"
#include "Arduino.h"
#include <ArduinoLog.h> // include the ArduinoLog library for logging functionality
#include "SPI.h"
#include "soc/spi_struct.h"
#include "adc.h"

double adcVoltage = 0;

// Fast alternatives for digitalRead/Write. Specific to ESP32
#define digitalReadFast(pin) (GPIO.in >> pin) & 1
#define digitalWriteFastLOW(pin) GPIO.out_w1tc = ((uint32_t)1 << pin)
#define digitalWriteFastHIGH(pin) GPIO.out_w1ts = ((uint32_t)1 << pin)

#define MSB_16_SET(var, val)                                 \
    {                                                        \
        (var) = (((val)&0xFF00) >> 8) | (((val)&0xFF) << 8); \
    }

// Copied from SPI.h
struct spi_struct_t
{
    spi_dev_t *dev;
#if !CONFIG_DISABLE_HAL_LOCKS
    xSemaphoreHandle lock;
#endif
    uint8_t num;
};

// Mock of SPI class and spi_struct_t from SPI.h
class mockSPIClass
{
public:
    int8_t _spi_num;
    spi_t *_spi;
};

// Forcing the SPI transfer function to be inline removes the call overhead
inline uint16_t spiTransferShortNL2(spi_t *spi, uint16_t data) __attribute__((always_inline));
uint16_t spiTransferShortNL2(spi_t *spi, uint16_t data)
{
    if (!spi->dev->ctrl.wr_bit_order)
    {
        MSB_16_SET(data, data);
    }
    spi->dev->mosi_dlen.usr_mosi_dbitlen = 11;
    spi->dev->miso_dlen.usr_miso_dbitlen = 11;
    spi->dev->data_buf[0] = data;
    spi->dev->cmd.usr = 1;
    while (spi->dev->cmd.usr)
        ;
    data = spi->dev->data_buf[0] & 0xFFFF;
    if (!spi->dev->ctrl.rd_bit_order)
    {
        MSB_16_SET(data, data);
    }
    return data;
}

namespace
{ 
    // VSPI are pins 19, 18
    SPIClass SPI_ADC(VSPI);
    SPISettings settings(26000000L, MSBFIRST, SPI_MODE0);


    void IRAM_ATTR adcISR(){
        adcVoltage = readADC();
        if (adcVoltage > 3.0){
            Serial.println("Hi");
            detachInterrupt(PIN_GENERATOR);
        }
    }
}


void activateADCinterrupt(){
    attachInterrupt(PIN_GENERATOR, adcISR, RISING);
}

// Initiliazie the SPI communication
void initADC()
{
    SPI_ADC.begin();
    pinMode(PIN_ADC, OUTPUT);
    digitalWrite(PIN_ADC, HIGH);
    SPI_ADC.beginTransaction(settings);

    
    Log.notice("ADC started...\n");
}

// Take a reading and return the voltage as double
double readADC()
{
    GPIO.out_w1tc = ((uint32_t)1 << PIN_ADC);                                                      // digitalWrite(SS, LOW);
    uint16_t buff = spiTransferShortNL2(reinterpret_cast<mockSPIClass *>(&SPI_ADC)->_spi, 0xFFFF); // faster way for buff = SPI_ADC.transfer16(0xFFFF);
    GPIO.out_w1ts = ((uint32_t)1 << PIN_ADC);                                                      // digitalWrite(SS, HIGH);
    return (buff >> 4) * (ADC_VREF / (pow(2, ADC_NUM_BITS) - 1));
}

