#include <Wire.h>
#include "Adafruit_ADS1X15.h"

/*
  VacuumGaugeController

  Reads the output voltage from the vacuum gauge and calculates the pressure.

  Sends the pressure to the computer when requested.
*/

Adafruit_ADS1015 ads1015; 
String command;
int sensorValue;
float v0, v1, v2, v3;
int16_t adc0, adc1, adc2, adc3;

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.setTimeout(10);
  Serial.println("GC1");
  ads1015.begin();
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('?');
    if(command == "*IDN") {
      Serial.println("GC1");
    }
    else if(command == "VOLTAGE") {
      adc0 = ads1015.readADC_SingleEnded(0);
      adc1 = ads1015.readADC_SingleEnded(1);
      adc2 = ads1015.readADC_SingleEnded(2);
      adc3 = ads1015.readADC_SingleEnded(3);
      Serial.println(adc0);
      Serial.println(adc1);
      Serial.println(adc2);
      Serial.println(adc3);
    }
    delay(1);        // delay in between reads for stability
  }
}
