#include <Arduino.h>       // include the Arduino library
#include <ArduinoLog.h>    // include the ArduinoLog library for logging functionality
#include "logging.h"       // include the logging.h file for logging setup
#include "serialCommand.h" // include the serialCommand.h file for serial command functionality
#include "serialParser.h" // include the serialParser.h file for serial command functionality
#include "movement.h"      // include the movement.h file for movement functionality
#include "adc.h"           // include the adc.h file for communicating with the adc

void setup()
{
  Serial.begin(9600);
  logSetup();
  Log.trace("CubeFW compiled at %s\n", __DATE__ " " __TIME__);
  //serialCmdInit();
  serialParserInit();
  stepperSetup();
  initADC();
}

void loop()
{
  vTaskDelete(NULL);
}
