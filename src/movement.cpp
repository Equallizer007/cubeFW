
#include "pinDefs.h"
#include "movement.h"
#include <TMCStepper.h>
#include <SpeedyStepper.h>
#include <ESP32Encoder.h>

bool homingFlag = false, stopFlag = false;
unsigned int targetSteps = 0;

namespace
{
    TMC2209Stepper driver(&TMC_Z_SERIAL, R_SENSE, DRIVER_ADDRESS);
    SpeedyStepper stepper;
    ESP32Encoder encoder;

    const int mcFactor()
    {
        if (STEPPER_MICROSTEPS == 0)
        {
            return 0;
        }
        else
        {
            return STEPPER_MICROSTEPS;
        }
    }
}

void stepperEnable()
{
    digitalWrite(PIN_Z_EN, LOW);
}

void stepperDisable()
{
    digitalWrite(PIN_Z_EN, HIGH);
}

void stepperStop()
{
    stepper.setupStop();
    while (!stepper.motionComplete())
    {
        stepper.processMovement();
    }
}

bool stepperSetup()
{
    pinMode(PIN_Z_MIN_DEC, INPUT_PULLUP);
    pinMode(PIN_Z_MAX_DEC, INPUT_PULLUP);
    pinMode(PIN_Z_EN, OUTPUT);

    TMC_Z_SERIAL.begin(115200);                  // INITIALIZE UART TMC2209
    driver.begin();                              // Initialize driver
    driver.toff(5);                              // Enables driver in software
    driver.rms_current(STEPPER_CURRENT_DEFAULT); // Set motor RMS current
    driver.pwm_autoscale(true);                  // Needed for stealthChop
    driver.en_spreadCycle(true);                 // false = StealthChop / true = SpreadCycle
    driver.microsteps(0);                        // Set it to 0 to test the connection
    if (driver.microsteps() != 0)
    {
        Serial.print("TMC connection error!");
        return false;
    }
    driver.microsteps(STEPPER_MICROSTEPS); // Set microsteps 0->fullStep
    if (driver.microsteps() != STEPPER_MICROSTEPS)
    {
        Serial.print("could not set microstepping value!");
        return false;
    }

    stepper.connectToPins(PIN_Z_STEP, PIN_Z_DIR); // INITIALIZE SpeedyStepper
    stepper.setStepsPerRevolution(STEPPER_STEPS_PER_REVOLUTION * mcFactor());
    stepper.setStepsPerMillimeter(STEPPER_STEPS_PER_MM * mcFactor());
    stepper.setCurrentPositionInSteps(0);                                        // Set zero position
    stepper.setSpeedInMillimetersPerSecond(STEPPER_SPEED_DEFAULT);               // Set default  Speed
    stepper.setAccelerationInMillimetersPerSecondPerSecond(STEPPER_ACC_DEFAULT); // Set acceleration, smaller value for super smooth direction changing
    stepperEnable();

    // encoder.attachHalfQuad(PIN_Z_CH_A, PIN_Z_CH_B);
    encoder.attachFullQuad(PIN_Z_CH_A, PIN_Z_CH_B);
    encoder.setCount(0);

    Serial.println("Stepper Initialized");
    xTaskCreate(
        movementTask,   /* Task function. */
        "movementTask", /* String with name of task. */
        10000,          /* Stack size in bytes. */
        NULL,           /* Parameter passed as input of the task */
        0,              /* Priority of the task. */
        NULL);          /* Task handle. */
    return true;
}

bool stepperHome(bool dir)
{
    stepperEnable();
    Serial.printf("homing to %s ...\n", dir ? "max" : "min");
    bool limitSwitchFlag = false;
    const int sensorPin = dir ? PIN_Z_MAX_DEC : PIN_Z_MIN_DEC;
    stepper.setAccelerationInMillimetersPerSecondPerSecond(STEPPER_ACC_HOME);
    stepper.setSpeedInMillimetersPerSecond(STEPPER_SPEED_HOMING);

    // Always check two times to prevent stray signals from the hall sensors
    // If switch already triggered back off first
    if (digitalRead(sensorPin) == HIGH && digitalRead(sensorPin) == HIGH)
    {
        Serial.println("move away from switch");
        stepper.setupRelativeMoveInMillimeters(STEPPER_BUMP_DIST * (dir ? -1 : 1));
        while (!stepper.processMovement())
        {
        }
        delay(25);
        if (digitalRead(sensorPin) == HIGH && digitalRead(sensorPin))
        {
            Serial.println("ERROR: Endstop never released!");
            return false;
        }
    }

    // Move towards Switch
    Serial.println("moving towards switch...");
    stepper.setupRelativeMoveInMillimeters((STEPPER_LEN_LINEAR_AXIS + 5) * (dir ? 1 : -1));
    while (!stepper.processMovement())
    {
        if (digitalRead(sensorPin) == HIGH && digitalRead(sensorPin) == HIGH)
        {
            Serial.println(digitalRead(sensorPin) == HIGH);
            Serial.printf("Endstop %i triggered min:%i, max:%i\n", sensorPin, digitalRead(PIN_Z_MIN_DEC), digitalRead(PIN_Z_MAX_DEC));
            limitSwitchFlag = true;
            break;
        }
    }
    delay(25);
    if (limitSwitchFlag != true)
    {
        Serial.println("ERROR: Endstop never triggered!");
        return (false);
    }
    float newPos = dir ? STEPPER_LEN_LINEAR_AXIS : 0;
    Serial.printf("Set new pos: %f\n", newPos);
    stepper.setCurrentPositionInMillimeters(newPos);
    stepper.setAccelerationInMillimetersPerSecondPerSecond(STEPPER_ACC_DEFAULT);
    stepper.setSpeedInMillimetersPerSecond(STEPPER_SPEED_DEFAULT);
    Serial.println("homing complete");
    stepperStop();
    return true;
}

void movementTask(void *param)
{
    Serial.println("movementTask started ...");
    bool moveStarted = false;
    for (;;)
    {
        if (homingFlag)
        {
            stepperHome(false);
            delay(200);
            Serial.println("encoder set to 0");
            homingFlag = false;
            encoder.setCount(0);
            targetSteps = 0;
        }
        int currentSteps = encoder.getCount();
        long curTargetSteps = targetSteps;
        if (stepper.motionComplete() && digitalRead(PIN_Z_EN) == LOW)
        {
            if (moveStarted)
            {
                stepperStop();
                Serial.printf("move finished curr: %i, tar: %i\n", currentSteps, curTargetSteps);
                moveStarted = false;
            }
            else if (curTargetSteps != currentSteps)
            {
                int stepsToTake = ((curTargetSteps - currentSteps) * mcFactor() * STEPPER_STEPS_PER_MM) / ENCODER_STEPS_PER_MM;
                if (stepsToTake == 0)
                    continue;
                Serial.printf("move started curr: %i, tar: %i steps:%i\n", currentSteps, curTargetSteps, stepsToTake);
                stepper.setupRelativeMoveInSteps(stepsToTake);
                moveStarted = true;
            }
            else
            {
                vTaskDelay(0);
            }
        }
        else if (!stepper.motionComplete())
        {
            // Serial.printf("curr: %i, tar: %i\n", currentSteps, curTargetSteps);
            stepper.processMovement();
        }
        else
        {
            stepperStop();
            vTaskDelay(0);
        }
    }
    Serial.println("movementTask stopped ...");
}