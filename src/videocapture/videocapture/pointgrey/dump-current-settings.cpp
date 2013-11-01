#include <stdlib.h>

#include "FlyCapture2.h"

using namespace FlyCapture2;

void printError(Error error)
{
  error.PrintErrorTrace();
}

int main(int argc, char *argv[])
{
  BusManager busMgr;
  PGRGuid guid;
  Error error;

  error = busMgr.GetCameraFromIndex(0, &guid);
  if (error != PGRERROR_OK) {
    printError(error);
    exit(1);
  }

  Camera cam;
  error = cam.Connect(&guid);
  if (error != PGRERROR_OK) {
    printError(error);
    return -1;
  }

  // do different things depending on camera model detected...
  CameraInfo camInfo;
  error = cam.GetCameraInfo(&camInfo);
  if (error != PGRERROR_OK) {
    printError(error);
    return -1;
  }

  printf("{\n  \"properties\": {\n");

  PropertyType propTypes[5] = { AUTO_EXPOSURE, SHARPNESS, SHUTTER, GAIN,
                                WHITE_BALANCE };
  const char *propTypeNames[5] = { "AUTO_EXPOSURE", "SHARPNESS", "SHUTTER",
                                   "GAIN", "WHITE_BALANCE" };
  for (int i=0; i<5; i++) {
    Property property;
    property.type = propTypes[i];
    cam.GetProperty(&property);

    if (i>0)
      printf(",\n");
    printf("    \"%s\": { \"onOff\": %s, \"autoManualMode\": %s, \"absValue\": %f, "
           "\"valueA\": %d, \"valueB\": %d }", propTypeNames[i],
           property.onOff ? "true" : "false",
           property.autoManualMode ? "true" : "false",
           (float)property.absValue, property.valueA, property.valueB);
  }
  printf("\n  }\n}\n");
}
