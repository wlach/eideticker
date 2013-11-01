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

  printf("%s\n", camInfo.modelName);
}
