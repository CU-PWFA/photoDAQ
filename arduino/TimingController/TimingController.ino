/*
  TimingController

  Enables and disables the SDG and sends timing messages back to the DAQ.
*/

String command;
volatile int shot = 0;
int max_shots = 0;
bool new_shot = false;
bool stopped = true;

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.setTimeout(10);
  Serial.println("TC");
  pinMode(8, OUTPUT); // SDG enable output
  digitalWrite(8, HIGH);
  pinMode(3, INPUT); // SDG trigger input
  attachInterrupt(digitalPinToInterrupt(3), fire, RISING);
  pinMode(2, OUTPUT); // output 1
  digitalWrite(2, LOW);
  pinMode(10, OUTPUT); // output 1
  digitalWrite(10, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('\n');
    if(command == "*IDN?") {
      Serial.println("TC");
    }
    else if(command == "OFF") {
      stopped = true;
      digitalWrite(8, HIGH);
    }
    else if(command == "ON") {
      stopped = false;
      digitalWrite(8, LOW);
    }
    else if(command[0] == 'R') {
      command.remove(0, 1);
      max_shots = command.toInt();
      shot = 0;
    }
    else if(command == "1ON") {
      digitalWrite(2, HIGH);
    }
    else if(command == "1OFF") {
      digitalWrite(2, LOW);
    }
    else if(command == "2ON") {
      digitalWrite(10, HIGH);
    }
    else if(command == "2OFF") {
      digitalWrite(10, LOW);
    }
    delay(1);
  }
  if (new_shot) {
    new_shot = false;
    shot += 1;
    if (shot == max_shots) {
      stopped = true;
      digitalWrite(8, HIGH);
  }
    Serial.println(shot);
  }
}

void fire() {
  if(!stopped) {
    new_shot = true;
  }
}
