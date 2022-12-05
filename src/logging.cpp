#include "logging.h" // inlcude the corresponding header file

// Configure the logging system by setting the prefix and suffix print functions
// and starting log output to the specified output stream at the specified log level.
void logSetup()
{
    Log.setPrefix(printPrefix);
    Log.setSuffix(printSuffix);
    Log.begin(LOG_LEVEL, &Serial);
    Log.setShowLevel(false);
}

void printLogLevel(Print *_logOutput, int logLevel)
{
    /// Show log description based on log level
    switch (logLevel)
    {
    // For unknown log levels, use the "SILENT" log level description
    default:
    case 0:
        _logOutput->print("SILENT ");
        break;
    case 1:
        _logOutput->print("<FATAL> ");
        break;
    case 2:
        _logOutput->print("<ERROR> ");
        break;
    case 3:
        _logOutput->print("<WARNING> ");
        break;
    case 4:
        _logOutput->print("<INFO> ");
        break;
    case 5:
        _logOutput->print("<TRACE> ");
        break;
    case 6:
        _logOutput->print("<VERBOSE> ");
        break;
    }
}

// Print an empty suffix message.
void printSuffix(Print *_logOutput, int logLevel)
{
    _logOutput->print("");
}

// Print the log level description corresponding to the given log level.
void printPrefix(Print *_logOutput, int logLevel)
{
    printLogLevel(_logOutput, logLevel);
}