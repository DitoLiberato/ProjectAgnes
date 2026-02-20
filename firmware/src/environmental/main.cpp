#include <Arduino.h>
void setup() { Serial.begin(115200); delay(300); Serial.println("[environmental] boot ok"); }
void loop() { delay(1000); }
