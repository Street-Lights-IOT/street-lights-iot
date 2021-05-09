#include "StreetLightsData.h"

#define LAMPS_AFTER "la"
#define ILLUMINATION_SECONDS "is"
#define MIN_LUX "min"
#define WITH_MOVEMENT "wm"
#define WITHOUT_MOVEMENT "wom"


IlluminationRange::IlluminationRange(uint16_t _minLux, uint8_t _intensityMov, uint8_t _intensityNoMov) {
  this->minLux = _minLux;
  this->intensityMov = _intensityMov;
  this->intensityNoMov = _intensityNoMov;
}

String IlluminationRange::toString() {
  String str = "";
  str += "Range:" + String(this->minLux) + "LUX, " + //TODO: vedere se in percentuali oppure se in (0-255)
         String(this->intensityMov) + ", " + String(this->intensityNoMov) + "\n";
  return str;
}

StreetLight::StreetLight(String _MAC, uint8_t _order, DynamicJsonDocument _neighborsIPs,
                         DynamicJsonDocument _info, uint16_t _lastEnvBrightness, uint16_t _lastIntensity) {

  this->MAC = _MAC;
  this->order = _order;
  this->lastEnvBrightness = _lastEnvBrightness;
  this->lastIntensity = _lastIntensity;

  this->nLampsAfter = _info[LAMPS_AFTER];

  this->nIPAddresses = _neighborsIPs.size();
  for (int i = 0; i < this->nIPAddresses; i++)
    this->neighborsAddresses[i] = new IPAddress(_neighborsIPs[i][0], _neighborsIPs[i][1], _neighborsIPs[i][2], _neighborsIPs[i][3]);

  this->nRanges = _info[MIN_LUX].size();
  for (int i = 0; i < this->nRanges; i++)
    this->illumRanges[i] = new IlluminationRange(_info[MIN_LUX][i], _info[WITH_MOVEMENT][i], _info[WITHOUT_MOVEMENT][i]);

  this->illumSeconds = _info[ILLUMINATION_SECONDS];
}

StreetLight::StreetLight() {}

String StreetLight::toString() {
  String str = "";
  str += "MAC: " + this->MAC + "\n";
  str += "order: " + String(this->order) + "\n";
  str += "lastEnvBrightness: " + String(this->lastEnvBrightness) + "\n";
  str += "lastIntensity: " + String(this->lastIntensity) + "\n";
  str += "nLampsAfter: " +  String(this->nLampsAfter) + "\n";
  str += "illumSeconds: " +  String(this->illumSeconds) + "\n";

  str += "nIPAddresses: " +  String(this->nIPAddresses) + "\n";

  /*for (int i = 0; i < this->nIPAddresses; i++)
    str += "IP Address: " +  this->neighborsAddresses[i] + "\n";*/
    
  for (int i = 0; i < this->nRanges; i++)
    str += this->illumRanges[i]->toString();
    
  return str;
}
