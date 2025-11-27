//Functions that have to be defined for specific hardware. Here: RFID/ NFC
#include <stdint.h>

// ----- Communication functions ----
int readRFIDTags(){// polling approach to always know who has sent/ received the msg
    return 4;
}           
void hw_getMsg(){}              
void hw_sendMsg(){}             // also get info on which tag on who is sending msg

// ----- LED functions -----
void hw_setLEDColour(){}
void LEDFPattern_continiouslyOn(){}
void LEDPattern_lonely(){}
void LEDPattern_error(){}
void LEDPattern_correctPos(){}
void LEDPattern_gameCompleted(){}

// ----- Button functions -----
void hw_buttonPressed(){}       // initiate an event once pressed
void hw_buttonLongPress(){}
       
// ----- Delays and timers -----
void shortSleep(){}
void longSleep(){}
void wakeFromSleep(){}

// uint32 hw_millis();
// uint32 hw_micros();

// ----- Init functions -----
void hw_initRFID(){}
void hw_initLED(){}
void hw_initButton(){}
void hw_initGPIO(){}
void initAllHw(){}              // calls all of the above
