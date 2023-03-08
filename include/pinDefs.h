#pragma once

/*   Debug pins: 12(AD1),14(AD3),13(AD0),15(AD2)    */ 

#define PIN_GENERATOR  2              // Generator Output Pin 
#define PIN_GENERATOR_INV  4          // Generator Inverted Output Pin 

#define PIN_Z_MIN 27                  // Min Endstop
#define PIN_Z_MIN_DEC 26              // Min Dec Endstop
#define PIN_Z_MAX_DEC 35              // Max Dec Endstop
#define PIN_Z_MAX 34                  // Max Endstop

#define PIN_Z_CH_A 39                 // Encoder Channel A
#define PIN_Z_CH_B 36                 // Encoder Channel B

#define PIN_Z_EN 25                   // Enable
#define PIN_Z_DIR 33                  // Direction
#define PIN_Z_STEP 32                 // Step
#define TMC_Z_SERIAL Serial2          // Default port pins 16 & 17

#define PIN_ADC 5                     // Pin 18 and 19 are also used by VSPI!
#define ADC_NUM_BITS 12               // Number of bits for SPI communicaton
#define ADC_VREF 5.0                  // Reference Voltage
#define VOLTAGE_DIVIDER_FACTOR 30     // Factor of the voltage divider
