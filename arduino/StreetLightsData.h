#include <cstdint>
#include <ArduinoJson.h>

#define MAX_RANGES 4
#define MAX_LAMPS_AFTER 4

class IlluminationRange {
public:
  uint16_t minLux;
  uint8_t intensityMov;
  uint8_t intensityNoMov;

  IlluminationRange(uint16_t _minLux, uint8_t _intensityMov, uint8_t _intensityNoMov);
  String toString();
};

class StreetLight {
public:
  String MAC;
  uint8_t order;

  IlluminationRange* illumRanges[MAX_RANGES];
  uint8_t nRanges;

  IPAddress* neighborsAddresses[MAX_LAMPS_AFTER];
  uint8_t nIPAddresses;

  uint8_t nLampsAfter;
  uint8_t illumSeconds;

  uint16_t lastEnvBrightness;
  uint16_t lastIntensity;
  uint8_t currentRange;

  StreetLight(String _MAC, uint8_t _order, DynamicJsonDocument _neighborsIPs,
              DynamicJsonDocument _info, uint16_t _lastEnvBrightness, uint16_t _lastIntensity);
  StreetLight();
  String toString();
};
