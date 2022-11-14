#include <Arduino.h>
#include "serialCommand.h"
#include "movement.h"



void setup()
{
  serialCmdInit();
  stepperSetup();
}

void loop()
{

  vTaskDelay(1);
}
