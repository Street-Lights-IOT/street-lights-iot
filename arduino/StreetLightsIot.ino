#include <SPI.h>
#include <Dhcp.h>
#include <Dns.h>
#include <WiFiNINA.h>
#include <WiFiUdp.h>
#include <coap-simple.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <ErriezBH1750.h>  //luxometer
#include <VL53L0X.h>       //IR sensor

#include "StreetLightsData.h"

//_________________________________
//_____________DEFINE______________
//_________________________________

#define LIGHT_PIN 5
#define FAULTCON_PIN A1

#define NUM_VALUES 10

#define FIRST_LAMP_HEIGHT 480  //TODO:cambiare
#define LAMP_HEIGHT 466
#define MIN_OBJ_HEIGHT 10
#define LUX_STEP_DURATION 5000 //TODO: rimuovere?

#define CODE_CREATED 65
#define CODE_CHANGED 68
#define CODE_NOTACCEPTABLE 160

#define JSON_DIM 256

//_________________________________
//_________GLOBAL VARIABLES________
//_________________________________
unsigned long luxDeadline = millis();
unsigned long movementDeadline = millis();

const bool serialPortActive = true;

const char* tokenPostRegis = "A";
const char* tokenGetIPs = "B";
const char* tokenGetInfo = "C";
bool registered = false;
bool ipsGot = false;
bool infoGot = false;

DynamicJsonDocument neighborsIPs(JSON_DIM);
DynamicJsonDocument info(JSON_DIM);
uint8_t order;

const char* wifiSsid = "HUAWEI-B311-7240";
const char* wifiPassword = "9L6B349JEY6";

IPAddress edgeIP(2, 39, 75, 165);

WiFiUDP udp;
Coap coap(udp);

StreetLight* streetLight;

BH1750 lightSensor(LOW);
VL53L0X* distSensor = new VL53L0X();

//_________________________________
//____________PROTOTYPES___________
//_________________________________
void callback_response(CoapPacket& packet, IPAddress ip, int port);  // CoAP client response callback
void callback_light(CoapPacket& packet, IPAddress ip, int port);

void connectToWifi();
void setupCoapCallbacks();
void initSensActs();

void initSerialPort();
void condPrintln(String text);
void condPrintln(IPAddress text);
void condPrint(String text);

String obtainMac(byte mac[]);

uint16_t readEnvBrightness(uint16_t defaultValue);


//_________________________________
//_____________SETUP_______________
//_________________________________
void setup() {

  initSerialPort();
  initSensActs();
  connectToWifi();

  setupCoapCallbacks();
  coap.start();  // start coap server/client

  byte mac[6];
  WiFi.macAddress(mac);
 
  String macString = obtainMac(mac);
  String macJson = "{\"mac\":\"" + macString + "\"}";

  int strLen = macJson.length() + 1;
  char macChar[strLen];
  macJson.toCharArray(macChar, strLen);


  do {
    int msgid = coap.send(edgeIP, 5683, "lights/", COAP_CON, COAP_POST,
                          (uint8_t*)tokenPostRegis, strlen(tokenPostRegis),
                          (uint8_t*)macChar, strlen(macChar));
    delay(1000);
  } while (!registered);

  do {
    int msgid = coap.send(edgeIP, 5683, "lights/mode", COAP_CON, COAP_GET,
                          (uint8_t*)tokenGetInfo, strlen(tokenGetInfo), NULL, 0);
    delay(1000);
  } while (!infoGot);

  do {
    int msgid = coap.send(edgeIP, 5683, "lights/", COAP_CON, COAP_GET,
                          (uint8_t*)tokenGetIPs, strlen(tokenGetIPs), NULL, 0);
    delay(1000);
  } while (!ipsGot);
  /*
     1. ed manda mac tramite una post (Json con MAC, String); ENDPOINT: "lights/"
        Risposta: codice Created (65) = aggiunto al DB e prima connessione
                  codice Changed (68) = MAC già registrato: Json (MAC, order, IP)
                  codice Not acceptable (160) = internal server error

     2. get per gli IP dei vicini ENDPOINT: "lights/<order>(detection)" -> Json
     3. get per conoscere le impostazioni "lights/mode" -> Json
  */
  /*/****************************** TODO:da togliere
  streetLight = new StreetLight();
  streetLight->nRanges = 3;
  streetLight->illumRanges[0] = new IlluminationRange(0, 255, 15);
  streetLight->illumRanges[1] = new IlluminationRange(4, 20, 3);
  streetLight->illumRanges[2] = new IlluminationRange(50, 0, 0);
  streetLight->illumSeconds = 5;
  //******************************/

  streetLight = new StreetLight(macString, order, neighborsIPs, info, 0, 0);
  condPrintln("\n\n***\n" + streetLight->toString());
}

//_________________________________
//______________LOOP_______________
//_________________________________
void loop() {
  //TODO: gestire disconnessione/riconnessione
  /*
  //MOVEMENT DETECTION
  int values[NUM_VALUES];
  int sum = 0;
  for (int i = 0; i < NUM_VALUES; i++) {
    values[i] = distSensor->readRangeSingleMillimeters();
    sum += values[i];
  }
  int distance = sum / NUM_VALUES;

  if (distance <= (LAMP_HEIGHT - MIN_OBJ_HEIGHT)) {  //TODO: vedere se è FIRST_LAMP_H...
    condPrintln("movement Detected!");
    movementDeadline = millis() + streetLight->illumSeconds * 1000;
    //TODO: inviare agli indirizzi IP dei successivi il messaggio di accensione
  }

  //___________________________
  if (millis() > luxDeadline) {

    //LUX MEASUREMENT
    uint16_t previousBrightness = streetLight->lastEnvBrightness;
    streetLight->lastEnvBrightness = readEnvBrightness(previousBrightness);
    uint16_t brightness = streetLight->lastEnvBrightness;
    luxDeadline = millis() + LUX_STEP_DURATION;
    condPrintln("brightness = " + String(streetLight->lastEnvBrightness) + " LUX");

    //RANGE INDETIFICATION
    if (brightness != previousBrightness) {
      bool rangeFound = false;

      uint8_t i = 0;
      while ((i < streetLight->nRanges) && !rangeFound) {
        if (brightness >= streetLight->illumRanges[i]->minLux && (i == streetLight->nRanges - 1 || brightness < streetLight->illumRanges[i + 1]->minLux)) {
          rangeFound = true;
          streetLight->currentRange = i;
        }
        i++;
      }
    }
    condPrintln("range = " + String(streetLight->currentRange));
  }


  uint8_t currRange = streetLight->currentRange;
  uint8_t previousIntensity = streetLight->lastIntensity;
  if ((millis() > movementDeadline)) {
    streetLight->lastIntensity = streetLight->illumRanges[currRange]->intensityNoMov;
  } else {
    streetLight->lastIntensity = streetLight->illumRanges[currRange]->intensityMov;
  }

  if (streetLight->lastIntensity != previousIntensity) {
    analogWrite(LIGHT_PIN, streetLight->lastIntensity);
    condPrintln("Change of intensity");
  }


  coap.loop();*/
}


//_________________________________
//____________CALLBACKS____________
//_________________________________

// CoAP server endpoint URL
void callback_light(CoapPacket& packet, IPAddress ip, int port) {
}

// CoAP client response callback
void callback_response(CoapPacket& packet, IPAddress ip, int port) {
  condPrintln("[Coap Response got]");

  char p[packet.payloadlen + 1];
  memcpy(p, packet.payload, packet.payloadlen);
  p[packet.payloadlen] = NULL;

  char t[packet.tokenlen + 1];
  memcpy(t, packet.token, packet.tokenlen);
  t[packet.tokenlen] = NULL;


  condPrintln("Payload : " + String(p));
  //condPrintln("Type : " + String(packet.type));
  condPrintln("Code : " + String(packet.code));
  condPrintln("Token : " + String(t));
  //condPrintln("Option num : " + String(packet.optionnum));

  String token = String(t);

  if (token.equals(tokenPostRegis)) {
    condPrintln("CALLBACK REGISTRATION");

    if (packet.code == CODE_CREATED || packet.code == CODE_CHANGED) {
      DynamicJsonDocument doc(JSON_DIM);
      deserializeJson(doc, p);
      order = doc["order"];
      registered = true;
    } else {
      condPrintln("Error in registration!");
    }

  } else if (token.equals(tokenGetIPs)) {
    condPrintln("CALLBACK GET IPs"); //TODO:inserire controlli 1
    deserializeJson(neighborsIPs, p);
    ipsGot = true;
  } else if (token.equals(tokenGetInfo)) {
    condPrintln("CALLBACK GET INFO"); //TODO:inserire controlli 2
    deserializeJson(info, p);
    infoGot = true;
  }
}

//_________________________________
//_________SENSORS RILEVs__________
//_________________________________
uint16_t readEnvBrightness(uint16_t defaultValue) {
  lightSensor.startConversion();

  // Wait synchronous for completion (blocking)
  if (lightSensor.waitForCompletion())
    return lightSensor.read();
  //else
  return defaultValue;
}

//_________________________________
//__________INIT FUNCTIONS_________
//_________________________________
void connectToWifi() {
  WiFi.begin(wifiSsid, wifiPassword);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    condPrint(".");
  }

  condPrintln("\nWiFi connected");
  condPrintln("IP address: ");
  condPrintln(WiFi.localIP());
}

void initSensActs() {

  // Initialize I2C bus
  Wire.begin();

  //LIGHT SENSOR
  // Initialize sensor in one-time mode, medium 1 lx resolution
  lightSensor.begin(ModeOneTime, ResolutionMid);

  //IR SENSOR
  distSensor->setTimeout(500);
  if (!distSensor->init()) {
    Serial.println("Failed to detect and initialize sensor!");
    while (1) {}
  }

  //LIGHT
  pinMode(LIGHT_PIN, OUTPUT);
  analogWrite(LIGHT_PIN, 0);
}

void setupCoapCallbacks() {
  // client response callback.
  // this endpoint is single callback.
  condPrintln("Setup Response Callback");
  coap.response(callback_response);

  condPrintln("Setup Callback Light");
  coap.server(callback_light, "lights/2/proximity");
}

//_________________________________
//____________CONVERSIONS__________
//_________________________________

String obtainMac(byte mac[]) {
  String macString = "";

  for (int i = 5; i >= 0; i--) {

    if (mac[i] < 16)
      macString += "0";

    macString += String(mac[i], HEX);

    if (i > 0)
      macString += ":";
  }
  return macString;
}

//_________________________________
//_______SERIAL PORT FUNCTIONS_____
//_________________________________
void condPrintln(String text) {
  if (serialPortActive)
    Serial.println(text);
}

void condPrintln(IPAddress text) {
  if (serialPortActive)
    Serial.println(text);
}

void condPrint(String text) {
  if (serialPortActive)
    Serial.print(text);
}

void initSerialPort() {
  if (serialPortActive) {
    Serial.begin(9600);
    while (!Serial) {}
  }
}
