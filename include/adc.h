#pragma once

void initADC();

inline double readADC() __attribute__((always_inline));;

void activateADCinterrupt();

