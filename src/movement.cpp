#include "pinDefs.h"
#include "movement.h"
#include <TMCStepper.h>
#include <SpeedyStepper.h>
#include <ESP32Encoder.h>
#include <ArduinoLog.h>

bool homingFlag = false, stopFlag = false, relativePositioningFlag = false;
unsigned int targetSteps = 0, currentSteps = 0;

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

bool ddigitalRead(unsigned pin)
{
    // Always check two times to prevent stray signals from the hall sensors
    return (digitalRead(pin) == HIGH && digitalRead(pin) == HIGH);
}

bool tmcSetup()
{
    TMC_Z_SERIAL.begin(115200);                  // INITIALIZE UART TMC2209
    driver.begin();                              // Initialize driver
    driver.toff(5);                              // Enables driver in software
    driver.rms_current(STEPPER_CURRENT_DEFAULT); // Set motor RMS current
    driver.pwm_autoscale(true);                  // Needed for stealthChop
    driver.en_spreadCycle(true);                 // false = StealthChop / true = SpreadCycle
    driver.microsteps(0);                        // Set it to 0 to test the connection
    if (driver.microsteps() != 0)
    {
        Log.error("TMC connection error!\n");
        return false;
    }
    driver.microsteps(STEPPER_MICROSTEPS); // Set microsteps 0->fullStep
    if (driver.microsteps() != STEPPER_MICROSTEPS)
    {
        Log.error("could not set TMC microstepping value!\n");
        return false;
    }
    return true;
}

bool stepperSetup()
{
    pinMode(PIN_Z_MIN_DEC, INPUT_PULLUP);
    pinMode(PIN_Z_MAX_DEC, INPUT_PULLUP);
    pinMode(PIN_Z_EN, OUTPUT);
    stepperDisable();
    if (!tmcSetup())
        return false;
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
    Log.notice("stepper Initialized\n");

    // start movement task
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
    Log.notice("homing to %s ...\n", dir ? "max" : "min");
    bool limitSwitchFlag = false;
    const int sensorPin = dir ? PIN_Z_MAX_DEC : PIN_Z_MIN_DEC;
    stepper.setAccelerationInMillimetersPerSecondPerSecond(STEPPER_ACC_HOME);
    stepper.setSpeedInMillimetersPerSecond(STEPPER_SPEED_HOMING);

    // If switch already triggered back off first
    if (ddigitalRead(sensorPin) == HIGH)
    {
        Log.notice("move away from switch\n");
        stepper.setupRelativeMoveInMillimeters(STEPPER_BUMP_DIST * (dir ? -1 : 1));
        while (!stepper.processMovement())
        {
        }
        delay(25);
        if (ddigitalRead(sensorPin) == HIGH)
        {
            Log.error("endstop never released!\n");
            return false;
        }
    }

    // Move towards Switch
    Log.notice("moving towards switch...\n");
    stepper.setupRelativeMoveInMillimeters((STEPPER_LEN_LINEAR_AXIS + 5) * (dir ? 1 : -1));
    while (!stepper.processMovement())
    {
        if (ddigitalRead(sensorPin) == HIGH)
        {
            Log.notice("endstop %i triggered min:%i, max:%i\n", sensorPin, digitalRead(PIN_Z_MIN_DEC), digitalRead(PIN_Z_MAX_DEC));
            limitSwitchFlag = true;
            break;
        }
    }
    delay(25);
    if (limitSwitchFlag != true)
    {
        Log.error("endstop never triggered!\n");
        return (false);
    }
    float newPos = dir ? STEPPER_LEN_LINEAR_AXIS : 0;
    Log.notice("set new pos: %f\n", newPos);
    stepper.setCurrentPositionInMillimeters(newPos);
    stepper.setAccelerationInMillimetersPerSecondPerSecond(STEPPER_ACC_DEFAULT);
    stepper.setSpeedInMillimetersPerSecond(STEPPER_SPEED_DEFAULT);
    Log.notice("homing complete\n");
    stepperStop();
    return true;
}

void movementTask(void *param)
{
    Log.trace("movementTask started ...\n");
    bool moveStarted = false;
    for (;;)
    {
        // check if home command was received
        if (homingFlag)
        {
            stepperHome(false);
            delay(200);
            Log.notice("encoder set to 0\n");
            homingFlag = false;
            encoder.setCount(0);
            targetSteps = 0;
        }
        currentSteps = encoder.getCount();
        unsigned int curTargetSteps = targetSteps;
        if (stepper.motionComplete() && digitalRead(PIN_Z_EN) == LOW)
        {
            // if the last move is complete and the stepper enabled
            if (moveStarted)
            {
                stepperStop();
                currentSteps = encoder.getCount();
                long coords = round(currentSteps * 1000.0 / ENCODER_STEPS_PER_MM);
                Log.notice("move finished curr: %i, tar: %i (%l)\n", currentSteps, curTargetSteps, coords);
                moveStarted = false;
            }
            else if (curTargetSteps != currentSteps)
            {
                int stepsToTake = ((curTargetSteps - currentSteps) * mcFactor() * STEPPER_STEPS_PER_MM) / ENCODER_STEPS_PER_MM;
                if (stepsToTake == 0)
                {
                    continue;
                }
                if (abs(int(curTargetSteps) - int(currentSteps)) < ENCODER_STEPS_PER_MM)
                {
                    // Slower speed if distance is < 1mm
                    Log.notice("move using slower speeds\n");
                    stepper.setAccelerationInMillimetersPerSecondPerSecond(STEPPER_ACC_DEFAULT / 3.0);
                    stepper.setSpeedInMillimetersPerSecond(STEPPER_SPEED_DEFAULT / 3.0);
                }
                else
                {
                    stepper.setAccelerationInMillimetersPerSecondPerSecond(STEPPER_ACC_DEFAULT);
                    stepper.setSpeedInMillimetersPerSecond(STEPPER_SPEED_DEFAULT);
                }
                Log.notice("move started curr: %i, tar: %i steps:%i\n", currentSteps, curTargetSteps, stepsToTake);
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
            // if the last move was not complete
            // Serial.printf("curr: %i, tar: %i\n", currentSteps, curTargetSteps);

            // check for endstops
            if (curTargetSteps > currentSteps && ddigitalRead(PIN_Z_MAX_DEC) == HIGH)
            {
                Log.error("Movement canceld because max endstop was triggered!\n");
                targetSteps = currentSteps;
                stepperStop();
            }
            else if (curTargetSteps < currentSteps && ddigitalRead(PIN_Z_MIN_DEC) == HIGH)
            {
                Log.error("Movement canceld because min endstop was triggered!\n");
                targetSteps = currentSteps;
                stepperStop();
            }
            else
            {
                stepper.processMovement();
            }
        }
        else
        {
            // if the stepper is disabled
            stepperStop();
            vTaskDelay(0);
        }
    }
    Log.trace("movementTask stopped ...\n");
}