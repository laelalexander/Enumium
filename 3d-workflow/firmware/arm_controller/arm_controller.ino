// Arduino Mega 2560 + AccelStepper (install via Library Manager). UNTESTED ON HARDWARE.
// Protocol, 115200 baud, one line per command, reply "OK" or "ERR ...":
//   V ch sps accel   set max speed (steps/s) and accel      G ch steps  absolute target
//   H ch dir         home toward limit switch (dir -1/+1), sets position 0
//   W                block until all moves finish             X  stop + disable drivers
//   Z                zero positions    ? print positions     E 0|1 enable drivers
// Mega + AccelStepper tops out near ~4 kHz combined step rate: keep joint speeds low
// (see arm/control.py max_dps) or move to a Teensy 4.x.
#include <AccelStepper.h>
const int N = 5;
const int STEP_PIN[N] = {2, 3, 4, 5, 6};
const int DIR_PIN[N]  = {7, 8, 9, 10, 11};
const int LIMIT_PIN[N] = {22, 23, 24, 25, 26};   // NC to GND, INPUT_PULLUP: HIGH = pressed/open
const int ENABLE_PIN = 12;                        // HIGH = drivers disabled (wire to ENA- on all drivers)
AccelStepper st[N] = {AccelStepper(1, 2, 7), AccelStepper(1, 3, 8), AccelStepper(1, 4, 9),
                      AccelStepper(1, 5, 10), AccelStepper(1, 6, 11)};
String line;

void enableDrivers(bool on) { digitalWrite(ENABLE_PIN, on ? LOW : HIGH); }
bool anyRunning() { for (int i = 0; i < N; i++) if (st[i].distanceToGo() != 0) return true; return false; }

void setup() {
  Serial.begin(115200);
  pinMode(ENABLE_PIN, OUTPUT); enableDrivers(false);
  for (int i = 0; i < N; i++) {
    pinMode(LIMIT_PIN[i], INPUT_PULLUP);
    st[i].setMaxSpeed(500); st[i].setAcceleration(500);
  }
}

void home(int ch, int dir) {
  enableDrivers(true);
  st[ch].setSpeed(dir * 300);
  unsigned long t0 = millis();
  while (digitalRead(LIMIT_PIN[ch]) == LOW) {            // NC switch: LOW until it opens
    st[ch].runSpeed();
    if (millis() - t0 > 90000UL) { Serial.println("ERR home timeout"); return; }
  }
  st[ch].setCurrentPosition(0);
  Serial.println("OK");
}

void handle(String s) {
  s.trim(); if (!s.length()) return;
  char c = s[0]; long a = 0, b = 0, d = 0;
  sscanf(s.c_str() + 1, "%ld %ld %ld", &a, &b, &d);
  if (c == 'V' && a >= 0 && a < N) { st[a].setMaxSpeed(b); st[a].setAcceleration(d); Serial.println("OK"); }
  else if (c == 'G' && a >= 0 && a < N) { enableDrivers(true); st[a].moveTo(b); Serial.println("OK"); }
  else if (c == 'H' && a >= 0 && a < N) home(a, b < 0 ? -1 : 1);
  else if (c == 'W') { while (anyRunning()) { for (int i = 0; i < N; i++) st[i].run(); } Serial.println("OK"); }
  else if (c == 'X') { for (int i = 0; i < N; i++) st[i].stop(); enableDrivers(false); Serial.println("OK"); }
  else if (c == 'Z') { for (int i = 0; i < N; i++) st[i].setCurrentPosition(0); Serial.println("OK"); }
  else if (c == 'E') { enableDrivers(a != 0); Serial.println("OK"); }
  else if (c == '?') { for (int i = 0; i < N; i++) { Serial.print(st[i].currentPosition()); Serial.print(' '); } Serial.println(); Serial.println("OK"); }
  else Serial.println("ERR unknown");
}

void loop() {
  for (int i = 0; i < N; i++) st[i].run();
  while (Serial.available()) { char ch = Serial.read(); if (ch == '\n') { handle(line); line = ""; } else line += ch; }
}
