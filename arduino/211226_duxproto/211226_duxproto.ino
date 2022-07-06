#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Servo.h>

// Stepper motor pins
const int M1 = A9; //orange, A-
const int M2 = A10; //pink, A+
const int M3 = A8; //yellow, B+
const int M4 = A7; //blue, B-

// Home sensor constants
const int SENSOR = 6; // home sensor
const int SENSOR_ON = 1; // home sensor polarity

// Led sensor constants
const int LED_ENABLE = 4;
//const int LED_PIN= 3;

// Servo motor constants
const int SERVO_PIN1 = 2;// unknown yet...
const int SERVO_PIN2 = A3;// unknown yet...

// Led var
int pwm = 0;

// Servo var
Servo servo1;
Servo servo2;

// Speed var
int homeHighSp = 0; // home high speed (coarse search 시 사용)
int homeLowSp = 0; // home low speed (fine search 시 사용)
int mSpeed = 0; // max speed
int acc = 0; // acceleration

// Position var
int targetPos = 0;
int targetDir = 0;
int curPos = 0;

// Flag var
bool homing = false; // homing 중인가?
bool homefine = false; // home coarse search가 끝나고 home fine search 중인가?
bool runAllowed = false;

// Command var
char cmd;

AccelStepper stepper(AccelStepper::FULL4WIRE, M1, M2, M3, M4);

void homeInt()
{
  if( homing ){
    if( !homefine ) {// When home fine is 'false'
      homefine = true;
      stepper.setMaxSpeed(homeLowSp);
      stepper.move(10000);
    }
  }
  else {// When home fine is 'true'
    stepper.stop();
    curPos = 0;
    targetPos = 0;

    stepper.setCurrentPosition(0);
    stepper.setMaxSpeed(mSpeed);
    
    homing = false;
    homefine = false;
    runAllowed = false;

    //Serial.println("done");
  }
}

void setup() {
  // Set baudrate
  Serial.begin(9600);
  
  // Set fine search interrupt
  attachInterrupt(digitalPinToInterrupt(SENSOR), homeInt, CHANGE);//중간에 껐다 켰다하면 이상동작

  // Set enable pin
  pinMode(LED_ENABLE, OUTPUT);
  analogWrite(LED_ENABLE, pwm);

  // Set led pins
  //pinMode(LED_PIN, OUTPUT);

  // Set Servo
  servo1.attach(SERVO_PIN1);
  servo2.attach(SERVO_PIN2);
  servo1.writeMicroseconds(1000); // slider in
}

void loop() {
  if(Serial.available() > 0)
  {
    cmd = Serial.read();

    switch(cmd)
    {
      case 'L':// Set leds on
//        digitalWrite(LED_PIN, HIGH);
        break;

      case 'F': // Set leds off
       // digitalWrite(LED_PIN, LOW);
        break;

      case 'P':// Set led PWM
        pwm = Serial.parseInt();
        analogWrite(LED_ENABLE, pwm);
        break;

      case 'p':// Get led PWM
        Serial.println(pwm);
        break;

      //Plz swap J, I code position
      case 'J':// Set servo backward
//        for(int i=0; i<=180; ++i){
//          servo1.write(i);
//          delay(5);
//        }
        servo1.writeMicroseconds(1000);
        Serial.println("done");
        break;

      case 'I':// Set servo forward
//        for(int i=180; i>= 0; --i){
//          servo1.write(i);
//          delay(5);
//        }
        servo1.writeMicroseconds(2000);
        Serial.println("done");
        break;

      case 'X':// Set servo forward
//        for(int i=0; i<=180; ++i){
//          servo2.write(i);
//          delay(5);
//        }
        servo2.writeMicroseconds(1000);
        Serial.println("done");
        break;

      case 'Y':// Set servo backward
//        for(int i=180; i>= 0; --i){
//          servo2.write(i);
//          delay(5);
//        }
        servo2.writeMicroseconds(2000);
        Serial.println("done");
        break;
       
      case 'H':// Set home high speed
        homeHighSp = Serial.parseInt();
        break;
      
      case 'h':// Get home high speed
        Serial.println(homeHighSp);
        break;

      case 'S':// Set home low speed
        homeLowSp = Serial.parseInt();
        break;

      case 's':// Get home low speed
        Serial.println(homeLowSp);
        break;

      case 'M':// Set max speed
        mSpeed = Serial.parseInt();
        stepper.setMaxSpeed(mSpeed);
        break;

      case 'm':// Get max speed
        Serial.println(stepper.maxSpeed());
        break;

      case 'C':{// Set current position
        int pos = Serial.parseInt();
        stepper.setCurrentPosition(pos);
        break;
      }

      case 'c'://Get current position
        Serial.println(stepper.currentPosition());
        break;

      case 'N'://Set target posiition
        targetPos = Serial.parseInt();
        stepper.moveTo(targetPos);
        runAllowed = true;
        break;

      case 'E'://Emergency stop
        homing = false;
        homefine = false;
        runAllowed = false;
        stepper.stop();
        break;

      case 'A'://Set accel
        acc = Serial.parseInt();
        stepper.setAcceleration(acc);
        break;

      case 'a'://Get accel
        Serial.println(acc);
        break;

      case 'o'://Get home sensor signal
        Serial.println(digitalRead(SENSOR));
        break;

      case 'G'://Go home
        homing = true;
        runAllowed = true;

        if(digitalRead(SENSOR) == SENSOR_ON){//home sensor 인식 되면
          homefine = true;
          stepper.setMaxSpeed(homeLowSp);
          targetPos = 10000;
          stepper.move(targetPos);
        }
        else{                               //home sensor 인식이 안되면
          homefine = false;
          stepper.setMaxSpeed(homeHighSp);
          targetPos = -10000;
          stepper.move(targetPos); //negative 방향으로 충분히 검색한다.
        }
        break;
    }// End of switch
  }// End of Serial.avaliable

  if (runAllowed){
    stepper.run();
    if ( !stepper.isRunning() ){
      runAllowed = false;
      Serial.println("done");
    }
  }
}// End of loop
