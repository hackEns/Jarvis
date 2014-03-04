unsigned int mode;

void setup() {
  pinMode(11, OUTPUT);
  analogWrite(11, 0);
  
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);
  pinMode(7, OUTPUT);
  digitalWrite(7, HIGH);
  Serial.begin(115200);
  Serial.println("ready");
  mode = 0;
}

void loop() {

  if (Serial.available()) {
    char ch = Serial.read();
    switch (mode) {
      case 1:
        analogWrite(11, ch);
        Serial.println("ack");
        mode = 0;
        break;
      
      case 2:
        if (ch == 0) {
          digitalWrite(8, HIGH);
          digitalWrite(7, HIGH);
          delay(1000);
          Serial.println("ATX is OFF");
        }
        else {
          digitalWrite(8, LOW);
          digitalWrite(7, LOW);
          delay(1000);
          Serial.println("ATX is ON");
        }
        mode = 0;
        break;
      
      default:
        mode = int(ch);
        Serial.print("waiting for instruction (mode ");
        Serial.print(mode, DEC);
        Serial.println(") ...");
    }
  }

} 
