#include <Wire.h>
#include <Adafruit_ADS1015.h>

/*
  VacuumGaugeController

  Reads the output voltage from the vacuum gauge and calculates the pressure.

  Sends the pressure to the computer when requested.
*/

Adafruit_ADS1015 ads1015; 
String command;
int sensorValue;
float v0, v1, v2, v3, p0, p1, p2, p3, c0=1.0, c1=1.000446, c2=1.004030, c3=0.994898;
int16_t adc0, adc1, adc2, adc3;
int digits = 8; // Number of digits for floats to be returned with
char p[60];
char *ptr = &p[15];
char *ptr1 = &p[30];
char *ptr2 = &p[45];

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.setTimeout(10);
  Serial.println("FRG700");
  ads1015.begin();
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('?');
    if(command == "*IDN") {
      Serial.println("FRG700");
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
    else if(command == "PRESSURE") {
      adc0 = ads1015.readADC_SingleEnded(0);
      adc1 = ads1015.readADC_SingleEnded(1);
      adc2 = ads1015.readADC_SingleEnded(2);
      adc3 = ads1015.readADC_SingleEnded(3);
      
      v0 = get_voltage(adc0)*c0;
      v1 = get_voltage(adc1)*c1;
      v2 = get_voltage(adc2)*c2;
      v3 = get_voltage(adc3)*c3;
      p0 = get_pressure(v0);
      p1 = get_pressure(v1);
      p2 = get_pressure(v2);
      p3 = get_pressure(v3);

      dtostrf(p0, 14, 9, p);
      p[14] = ',';
      dtostrf(p1, 14, 9, ptr);
      p[29] = ',';
      dtostrf(p2, 14, 9, ptr1);
      p[44] = ',';
      dtostrf(p3, 14, 9, ptr2);
      Serial.println(p);
    }
    delay(1);        // delay in between reads for stability
  }
}

// Calculate the voltage from the adc value
// Operating in GAIN_TWOTHIRDS, the total range for 12bits is +-6.144
float get_voltage(int adc) {
    return float(adc)*0.003001;
}

// Calculate the pressure from the sensor voltage
float get_pressure(float v) {
    return pow(10., (3.334*v-11.33));
}
