/*
  TimingController

  Enables and disables the SDG and sends timing messages back to the DAQ.
*/

String command;
String value;
volatile int shot = 0;
int max_shots = 0;
bool new_shot = false;

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.setTimeout(10);
  Serial.println("TC");
  pinMode(8, OUTPUT); // SDG enable output
  digitalWrite(8, HIGH);
  pinMode(3, INPUT); // SDG trigger input
  attachInterrupt(digitalPinToInterrupt(3), fire, RISING);
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('\n');
    if(command == "*IDN?") {
      Serial.println("TC");
    }
    else if(command == "OFF") {
      digitalWrite(8, HIGH);
    }
    else if(command == "ON") {
      digitalWrite(8, LOW);
    }
    else if(command == "RESET") {
      value = "5";
      max_shots = value.toInt();
      shot = 0;
      Serial.println(value);
    }
    delay(1);
  }
  if (new_shot) {
    new_shot = false;
    shot += 1;
    if (shot == max_shots) {
    digitalWrite(8, HIGH);
  }
    Serial.println(shot);
  }
}

void fire() {
  new_shot = true;
}
