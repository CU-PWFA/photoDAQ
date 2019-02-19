/*
  SerialVacuumGauge

  Reads the output voltage from the vacuum gauge and calculates the pressure.

  Sends the pressure to the computer when requested.
*/
String command;
int sensorValue;
float sensorVoltage, pressure;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.setTimeout(10);
  Serial.println("FRG700");
}

// the loop routine runs over and over again forever:
void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('?');
    if(command == "*IDN") {
      Serial.println("FRG700");
    }
    else if(command == "VOLTAGE") {
      sensorValue = analogRead(A0);
      Serial.println(sensorValue);
    }
    else if(command == "PRESSURE") {
      sensorValue = analogRead(A0);
      sensorVoltage = 5.*float(sensorValue) / 1023.;
      pressure = pow(10., (3.334*sensorVoltage-11.33));
      Serial.println(pressure, 8);
    }
    delay(1);        // delay in between reads for stability
  }
}
