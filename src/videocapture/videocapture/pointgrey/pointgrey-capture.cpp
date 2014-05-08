#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <signal.h>
#include <string>
#include <sstream>
#include <vector>

#include "JSON.h"
#include "FlyCapture2.h"
#include "settings.h"

using namespace FlyCapture2;

bool g_finished = false;

void term(int signum)
{
  printf("Received SIGTERM, exiting...\n");
  g_finished = true;
}

int usage(char *progname, int status)
{
  fprintf(stderr,
          "Usage: %s [OPTIONS]\n"
          "\n"
          "    -d                  Output debugging information\n"
          "    -o                  If specified, print frame numbers while capturing\n"
          "    -r                  Frames per second (default is 60)\n"
          "    -f <outputdir>      Directory video files will be written to\n"
          "    -c <configfile>     Configuration file for camera (in JSON format)\n"
          "    -n <frames>         Max number of frames to capture (default is 20 * framerate)\n"
          "\n"
          "Capture video to a set of pngs.\n"
          "\n"
          "Ex:    %s -f /tmp/eideticker/dirname\n",
          basename(progname), basename(progname));

  exit(status);
}

void printError( Error error )
{
  error.PrintErrorTrace();
}

int main(int argc, char *argv[])
{
  Error error;
  int ch;
  const char *videoOutputDir = NULL;
  const char *configFilename = NULL;
  int maxFrames = 0;
  int fps = 60;
  bool printFrameNums = false;
  bool debug = false;

  // Parse command line options
  while ((ch = getopt(argc, argv, "do?h3f:n:r:c:")) != -1) {
    switch (ch) {
    case 'd':
      debug = true;
      break;
    case 'o':
      printFrameNums = true;
      break;
    case 'f':
      videoOutputDir = optarg;
      break;
    case 'n':
      maxFrames = atoi(optarg);
      break;
    case 'r':
      fps = atoi(optarg);
      break;
    case 'c':
      configFilename = optarg;
      break;
    case '?':
    case 'h':
      usage(argv[0], 0);
    }
  }
  if (!videoOutputDir) {
    fprintf(stderr, "No video output file specified\n");
    exit(1);
  }

  if (!maxFrames)
    maxFrames = 20 * fps;

  BusManager busMgr;
  PGRGuid guid;
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

  FC2Config config;
  config.grabMode = BUFFER_FRAMES;
  cam.SetConfiguration(&config);

  // do different things depending on camera model detected...
  CameraInfo camInfo;
  error = cam.GetCameraInfo(&camInfo);
  if (error != PGRERROR_OK) {
    printError(error);
    return -1;
  }

  if (strcmp(camInfo.modelName, "Flea3 FL3-U3-13Y3M") == 0) {
    Format7ImageSettings f7Settings;
    f7Settings.width = 1280;
    f7Settings.height = 1024;
    f7Settings.pixelFormat = PIXEL_FORMAT_RAW8;

    bool valid = false;
    Format7PacketInfo packetInfo;
    error = cam.ValidateFormat7Settings(&f7Settings, &valid, &packetInfo);
    if (error != PGRERROR_OK) {
      printError(error);
      return -1;
    }

    error = cam.SetFormat7Configuration(&f7Settings, packetInfo.recommendedBytesPerPacket);
    if (error != PGRERROR_OK) {
      printError(error);
      return -1;
    }

    Property frameRateProp;
    frameRateProp.type = FRAME_RATE;
    cam.GetProperty(&frameRateProp);
    frameRateProp.onOff = true;
    frameRateProp.autoManualMode = false;
    frameRateProp.absValue = (float)fps;
    cam.SetProperty(&frameRateProp);
  }
  else {
    if (fps != 60) {
      fprintf(stderr, "Currently only 60fps is supported with this model\n");
      exit(1);
    }

    FrameRate frameRate = FRAMERATE_60; // hardcoded for now

    error = cam.SetVideoModeAndFrameRate(VIDEOMODE_1280x960Y8,
                                         frameRate);
    if (error != PGRERROR_OK) {
      printError(error);
      return -1;
    }
  }

  if (configFilename)
    processPropertiesFile(configFilename, cam);

  // setup signal handler for termination
  signal(SIGTERM, term);

  error = cam.StartCapture();
  if (error != PGRERROR_OK) {
    printError(error);
    return -1;
  }

  std::vector<Image> vecImages;
  vecImages.resize(maxFrames);
  unsigned long frameCount = 0;

  // the first frame always seems to be overly bright, which can cause issues.
  // retrieve it without adding it to the array
  Image rawImage;
  error = cam.RetrieveBuffer(&rawImage);
  if (error != PGRERROR_OK) {
    printError(error);
    return -1;
  }

  while (!g_finished && frameCount < maxFrames) {
    Image rawImage;
    error = cam.RetrieveBuffer(&rawImage);
    if (error != PGRERROR_OK) {
      printError(error);
      return -1;
    }

    if (printFrameNums) {
      struct timespec tp;
      if (debug) {
        clock_gettime(CLOCK_MONOTONIC, &tp);
        printf("%.4f %lu\n", (float)tp.tv_sec + (tp.tv_nsec/1000000000.0), frameCount);
      }
      else
        printf("%lu\n", frameCount);
      fflush(stdout);
    }

    vecImages[frameCount].DeepCopy(&rawImage);
    frameCount++;
  }

  error = cam.Disconnect();
  if (error != PGRERROR_OK) {
    printError(error);
    return -1;
  }

  for (int imageCnt = 0; imageCnt < frameCount; imageCnt++) {
    std::ostringstream fname;
    fname << videoOutputDir << "/" << "image-" << imageCnt << ".png";
    vecImages[imageCnt].Save(fname.str().c_str());
  }
}
