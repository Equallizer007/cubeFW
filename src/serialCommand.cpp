#include <Arduino.h>
#include "movement.h"
#include "funcGen.h"

namespace
{
    const int buffSize = 100;

    void parseCmd(char cmdType, int cmdNumber, char *cmdArgument)
    {
        switch (cmdType)
        {
        case 'G':
            Serial.printf("G%i command: %s\n", cmdNumber, cmdArgument);
            switch (cmdNumber)
            {
            case 0:
            case 1:
            {
                if (toupper(cmdArgument[0]) != 'Z')
                {
                    Serial.printf("ERROR: can't parse argument: %s\n", cmdArgument);
                    return;
                }
                int coordZ = strtol(cmdArgument + 1, NULL, 10);
                Serial.printf("G%i Z with coord %i\n", cmdNumber, coordZ);
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
                break;
            }
            case 91:
            {
                // relative positioning
                break;
            }
            default:
            {
                Serial.printf("ERROR: unknown command G%i\n", cmdNumber);
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
                    Serial.printf("ERROR: can't parse argument: %s\n", cmdArgument);
                    return;
                }
                char delimiter[] = ":/|";
                char *on = strtok(cmdArgument + 1, delimiter);
                char *off = strtok(NULL, delimiter);
                if (on == NULL || off == NULL)
                {
                    Serial.println("ERROR: can't split argument string!");
                    return;
                }
                Serial.println(on);
                Serial.println(off);
                unsigned long onTime = strtoul(on, NULL, 10);
                unsigned long offTime = strtoul(off, NULL, 10);
                Serial.printf("INFO: Set onTime: %luns offTime: %luns\n", onTime, offTime);
                setFunc(onTime, offTime);
                break;
            }
            default:
            {
                Serial.printf("ERROR: unknown command G%i\n", cmdNumber);
            }
            }
            break;
        default:
            Serial.printf("ERROR: unknown command %c\n", cmdType);
        }
    }

    void parseCmdBuffer(const char *inputBuffer)
    {
        Serial.printf("readCmd: %s\n", inputBuffer);
        while (isspace(inputBuffer[0])) // skip whitespace
        {
            inputBuffer++;
        }
        int i = 0;
        char cmdType = toupper(inputBuffer[i]);
        if (!isdigit(inputBuffer[++i])) // make sure char after cmdType is letter
        {
            Serial.printf("ERROR: cant parse command: %s\n", inputBuffer);
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
        Serial.println("serialInputTask started ...");
        char readBuffer[buffSize] = {0};
        int i = 0;

        for (;;)
        {
            while (Serial.available() > 0)
            {
                if (i >= buffSize)
                {
                    Serial.println("ERROR: serialInput buffer overflow!");
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
            vTaskDelay(10);
        }
        Serial.println("serialInputTask closed ...");
    }

}

void serialCmdInit()
{
    const char *compileDate = __DATE__ " " __TIME__;
    Serial.begin(115200);
    Serial.printf("\n\nCubeFW compiled at %s\n", compileDate);
    xTaskCreate(
        serialInputTask,   /* Task function. */
        "serialInputTask", /* String with name of task. */
        10000,             /* Stack size in bytes. */
        NULL,              /* Parameter passed as input of the task */
        0,                 /* Priority of the task. */
        NULL);             /* Task handle. */
}
