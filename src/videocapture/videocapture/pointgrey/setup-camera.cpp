#include <stdlib.h>

#include "FlyCapture2.h"
#include "settings.h"

using namespace FlyCapture2;

void printError(Error error)
{
  error.PrintErrorTrace();
}

int main(int argc, char *argv[])
{
  if (argc != 2) {
    fprintf(stderr, "Usage: %s <properties file>\n", argv[0]);
    exit(1);
  }

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

  processPropertiesFile(argv[1], cam);
}
