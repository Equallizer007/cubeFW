/**
 * @file funcGen.h
 * @author Marcus Voß (you@domain.com)
 * @brief 
 * @version 0.1
 * @date 2023-03-08
 * 
 * @copyright Copyright (c) 2023
 * 
 */
#pragma once

void initFunc();

void setF1(bool val);

void setF2(bool val);

void setOutputOff();

bool setFunc(unsigned long onTime, unsigned long offTime);

extern bool generatorAciveFlag;