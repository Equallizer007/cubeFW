#include <Arduino.h>
#include <CommandParser.h>
#include "serialParser.h"
#include "logging.h"
#include "movement.h"
#include "funcGen.h"
#include "adc.h"

typedef CommandParser<> MyCommandParser;
MyCommandParser parser;

// movement command in microMeters as double
void cmd_G1(MyCommandParser::Argument *args, char *response)
{
    char *input = args[0].asString;
    Log.notice("-> G1 %s\n", input);
    if (toupper(input[0]) != 'Z')
    {
        Log.error("Only Z-Axis is supported! \n");
        return;
    }
    double coord = strtod(input + 1, NULL);
    Log.notice("Read Parameter: %D\n", coord);
    setNewTargetPosition(coord);

    // strlcpy(response, "success", MyCommandParser::MAX_RESPONSE_SIZE);
}

// home command
void cmd_G28(MyCommandParser::Argument *args, char *response)
{
    Log.notice("-> G28\n");
    homingFlag = true;
}

// enable absolute positioning
void cmd_G90(MyCommandParser::Argument *args, char *response)
{
    Log.notice("-> G90 enable absolute Positioning\n");
    relativePositioningFlag = false;
}

// enable relative positioning
void cmd_G91(MyCommandParser::Argument *args, char *response)
{
    Log.notice("-> G91 enable relative Positioning\n");
    relativePositioningFlag = true;
}

// send report
void cmd_M1(MyCommandParser::Argument *args, char *response)
{
    double voltage = readADC();
    Serial.println(voltage);
    char report[64];
    sprintf(report, "<REPORT> adc:%.2f rel_pos:%d current_steps:%u target_steps:%u\n", voltage, relativePositioningFlag, currentSteps, targetSteps);
    Serial.print(report);
}

// enable stepper
void cmd_M17(MyCommandParser::Argument *args, char *response)
{
    Log.notice("-> M17 enable Stepper\n");
    stepperEnable();
}

// disable stepper
void cmd_M18(MyCommandParser::Argument *args, char *response)
{
    Log.notice("-> M18 disable Stepper\n");
    stepperDisable();
}

// set Mosfet1 state
void cmd_M20(MyCommandParser::Argument *args, char *response)
{
    bool val = args[0].asUInt64;
    Log.notice("-> M20 set Mosfet T1: %s\n", val ? "on" : "off");
    setF1(val);
}

// set Mosfet2 state
void cmd_M21(MyCommandParser::Argument *args, char *response)
{
    bool val = args[0].asUInt64;
    Log.notice("-> M21 set Mosfet T2: %s\n", val ? "on" : "off");
    setF2(val);
}

void registerCommands()
{
    // CommandParser contains a bug where negative int64 can't be parsed so always use string type instead

    // G - commands
    parser.registerCommand("G0", "s", &cmd_G1);
    parser.registerCommand("G1", "s", &cmd_G1);
    parser.registerCommand("G28", "", &cmd_G28);
    parser.registerCommand("G90", "", &cmd_G90);
    parser.registerCommand("G91", "", &cmd_G91);

    // M - commands
    parser.registerCommand("M1", "", &cmd_M1);
    parser.registerCommand("M17", "", &cmd_M17);
    parser.registerCommand("M18", "", &cmd_M18);
    parser.registerCommand("M20", "u", &cmd_M20);
    parser.registerCommand("M21", "u", &cmd_M21);
}

void readSerial()
{
    if (Serial.available())
    {
        char line[128];
        size_t lineLength = Serial.readBytesUntil('\n', line, 127);
        line[lineLength] = '\0';

        char response[MyCommandParser::MAX_RESPONSE_SIZE];
        parser.processCommand(line, response);
        Serial.println(response);
    }
}

void serialParserTask(void *param)
{
    Log.trace("serialParserTask started ...\n");
    for (;;)
    {
        readSerial();
    }
    Log.trace("SerialParserTask closed ...\n");
}

void serialParserInit()
{
    registerCommands();
    xTaskCreate(
        serialParserTask,   /* Task function. */
        "serialParserTask", /* String with name of task. */
        10000,              /* Stack size in bytes. */
        NULL,               /* Parameter passed as input of the task */
        0,                  /* Priority of the task. */
        NULL);              /* Task handle. */
}
