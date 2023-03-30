#pragma once

#define DRIVER_ADDRESS 0b00 // TMC2209 Driver address according to MS1 and MS2
#define R_SENSE 0.11f       // SilentStepStick series use 0.11Ohm

#define STEPPER_STEPS_PER_REVOLUTION 200
#define STEPPER_MICROSTEPS 256
#define STEPPER_STEPS_PER_MM 200
#define STEPPER_SPEED_DEFAULT 1.5
#define STEPPER_SPEED_HOMING 1.5
#define STEPPER_ACC_DEFAULT 100000
#define STEPPER_ACC_HOME 100000
#define STEPPER_CURRENT_DEFAULT 800
#define STEPPER_LEN_LINEAR_AXIS 25
#define STEPPER_BUMP_DIST 2
#define ENCODER_STEPS_PER_MM  4000

bool stepperInit();
bool stepperHome(bool dir);
void stepperEnable();
void stepperDisable();
void movementTask(void* args);
void movementReport();
void setNewTargetPosition(double newPos);

extern bool homingFlag, stopFlag, touchModeFlag, autoModeFlag, relativePositioningFlag;
extern int targetSteps, currentSteps;
extern unsigned int position_report_interval;