#include <Arduino.h>       // include the Arduino library
#include <ArduinoLog.h>    // include the ArduinoLog library for logging functionality
#include "logging.h"       // include the logging.h file for logging setup
#include "serialCommand.h" // include the serialCommand.h file for serial command functionality
#include "movement.h"      // include the movement.h file for movement functionality

void setup()
{
  Serial.begin(115200);
  logSetup();
  Log.trace("CubeFW compiled at %s\n", __DATE__ " " __TIME__);
  serialCmdInit();
  stepperSetup();
}

void loop()
{
  vTaskDelete(NULL);
}
