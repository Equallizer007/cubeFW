#include <Arduino.h>
#include <ArduinoLog.h>
#include "movement.h"
#include "funcGen.h"

extern double adcVoltage;

namespace
{
    const int buffSize = 100;
    bool relativePositioning = true;
    bool adcReport = false;

    void parseCmd(char cmdType, int cmdNumber, char *cmdArgument)
    {
        switch (cmdType)
        {
        case 'G':
            Log.notice("G%i command: %s\n", cmdNumber, cmdArgument);
            switch (cmdNumber)
            {
            case 0:
            case 1:
            {
                if (toupper(cmdArgument[0]) != 'Z')
                {
                    Log.error("can't parse argument: %s\n", cmdArgument);
                    return;
                }
                long coordZ = strtod(cmdArgument + 1, NULL) * (ENCODER_STEPS_PER_MM / 1000.0);
                Log.notice("read G%i Z with encoder steps %i\n", cmdNumber, coordZ);
                if (abs(coordZ) > ENCODER_STEPS_PER_MM * STEPPER_LEN_LINEAR_AXIS)
                {
                    Log.error("illegal command to many steps!\n");
                    return;
                }
                unsigned currentSteps = targetSteps;
                Log.notice("targetSteps : %i\n", currentSteps);
                if (relativePositioning)
                {
                    coordZ += currentSteps;
                }
                targetSteps = coordZ;
                break;
            }
            case 28:
            {
                // home to min position
                homingFlag = true;
            }
            case 90:
            {
                // absolute positioning
                relativePositioning = false;
                Log.notice("absolute positioning enabled\n");
                break;
            }
            case 91:
            {
                // relative positioning
                relativePositioning = true;
                Log.notice("relative positioning enabled\n");
                break;
            }
            default:
            {
                Log.error("unknown command G%i\n", cmdNumber);
            }
            }
            break;
        case 'M':
            switch (cmdNumber)
            {
            case 17:
            {
                stepperEnable();
                break;
            }
            case 18:
            case 84:
            {
                stepperDisable();
                break;
            }
            case 100:
            {
                if (toupper(cmdArgument[0]) != 'S')
                {
                    Log.error("can't parse argument: %s\n", cmdArgument);
                    return;
                }
                char delimiter[] = ":/|";
                char *on = strtok(cmdArgument + 1, delimiter);
                char *off = strtok(NULL, delimiter);
                if (on == NULL || off == NULL)
                {
                    Log.error("can't split argument string!\n");
                    return;
                }
                unsigned long onTime = strtoul(on, NULL, 10);
                unsigned long offTime = strtoul(off, NULL, 10);
                if (onTime > 1000 && offTime > 1000)
                {
                    Log.notice("set onTime: %Fns offTime: %Fns\n", onTime / 1000.0, offTime / 1000.0);
                }
                else
                {
                    Log.notice("set onTime: %lns offTime: %lns\n", onTime, offTime);
                }

                setFunc(onTime, offTime);
                break;
            }
            case 101:
            {
                Log.notice("set output off\n");
                setFuncOff();
                break;
            }
            case 102:
            {
                Log.notice("set output on\n");
                setFuncOn();
                break;
            }
            case 103:
            {
                Log.notice("enable ADC\n");
                adcReport = true;
                
                break;
            }
            case 104:
            {
                Log.notice("disable ADC\n");
                adcReport = false;

                break;
            }
            default:
            {
                Log.error("unknown command G%i\n", cmdNumber);
            }
            }
            break;
        default:
            Log.error("unknown command %c\n", cmdType);
        }
    }

    void parseCmdBuffer(const char *inputBuffer)
    {
        Log.notice("readCmd: %s\n", inputBuffer);
        while (isspace(inputBuffer[0])) // skip whitespace
        {
            inputBuffer++;
        }
        int i = 0;
        char cmdType = toupper(inputBuffer[i]);
        if (!isdigit(inputBuffer[++i])) // make sure char after cmdType is letter
        {
            Log.error("cant parse command: %s\n", inputBuffer);
            return;
        }
        char *cmdArgument;
        int cmdNumber = strtoul(inputBuffer += i, &cmdArgument, 10);
        while (isspace(cmdArgument[0])) // skip whitespace
        {
            cmdArgument++;
        }
        // Serial.printf("cmdType: %c\n", cmdType);
        // Serial.printf("cmdNumber: %i\n", cmdNumber);
        // Serial.printf("cmdArgument is %s\n", cmdArgument);
        parseCmd(cmdType, cmdNumber, cmdArgument);
    }

    void serialInputTask(void *param)
    {
        Log.trace("serialInputTask started ...\n");
        char readBuffer[buffSize] = {0};
        int i = 0;
        auto reportTimer = millis();

        for (;;)
        {
            while (Serial.available() > 0)
            {
                if (i >= buffSize)
                {
                    Log.error("ERROR: serialInput buffer overflow\n");
                    i = 0;
                }
                char c = Serial.read();
                if (c != '\n')
                {
                    readBuffer[i++] = c;
                }
                else
                {
                    readBuffer[i] = '\0';
                    parseCmdBuffer(readBuffer);
                    i = 0;
                    break;
                }
            }
            if (adcReport && millis() - reportTimer > 1000)
            {
                Serial.print("voltage: ");
                Serial.println(adcVoltage);
                reportTimer = millis();
            }
            vTaskDelay(10);
        }
        Log.trace("serialInputTask closed ...\n");
    }

}

void serialCmdInit()
{
    initFunc();
    xTaskCreate(
        serialInputTask,   /* Task function. */
        "serialInputTask", /* String with name of task. */
        10000,             /* Stack size in bytes. */
        NULL,              /* Parameter passed as input of the task */
        0,                 /* Priority of the task. */
        NULL);             /* Task handle. */
}
