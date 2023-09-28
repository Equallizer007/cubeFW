#pragma once
#include <ArduinoLog.h>

#define LOG_LEVEL LOG_LEVEL_VERBOSE // Set the log level

// Configure the logging system by setting the prefix and suffix print functions
// and starting log output to the specified output stream at the specified log level.
void logInit();

// Print the log level description corresponding to the given log level.
void printLogLevel(Print *_logOutput, int logLevel);

void printSuffix(Print *_logOutput, int logLevel);

void printPrefix(Print *_logOutput, int logLevel);