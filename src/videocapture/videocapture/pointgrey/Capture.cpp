#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <signal.h>
#include <string>
#include <sstream>
#include <vector>

#include "FlyCapture2.h"

using namespace FlyCapture2;

bool g_finished = false;

void term(int signum)
{
  printf("Received SIGTERM, exiting...\n");
  g_finished = true;
}

int usage(int status)
{
    fprintf(stderr,
            "Usage: Capture -m <mode id> [OPTIONS]\n"
            "\n"
            "    -f <outputdir>      Directory video files will be written to\n"
            "    -n <frames>         Max number of frames to capture (default is 20 * 60)\n"
            "\n"
            "Capture video to a set of pngs.\n"
            "\n"
            "    ptgrey-capture -d /tmp/eideticker/dirname\n"
	);

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
  int maxFrames = 20*60; // 20 seconds at 60fps
  bool printFrameNums = true;
  bool debug = false;

  // Parse command line options
  while ((ch = getopt(argc, argv, "do?h3f:n:")) != -1) 
    {
      switch (ch)
        {
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
        case '?':
        case 'h':
          usage(0);
        }
    }
  if (!videoOutputDir)
    {
      fprintf(stderr, "No video output file specified\n");
      exit(1);
    }

  BusManager busMgr;
  PGRGuid guid;
  error = busMgr.GetCameraFromIndex(0, &guid);
  if (error != PGRERROR_OK)
    {
      printError(error);
      exit(1);
    }

  Camera cam;
  error = cam.Connect(&guid);
  if (error != PGRERROR_OK)
    {
      printError(error);
      return -1;
    }

  error = cam.SetVideoModeAndFrameRate(VIDEOMODE_1280x960Y8,
                                       FRAMERATE_60);
  if (error != PGRERROR_OK)
    {
      printError(error);
      return -1;
    }

  // turn off all auto adjustments for eideticker
  PropertyType propTypes[5] = { AUTO_EXPOSURE, SHARPNESS, SHUTTER, GAIN, WHITE_BALANCE };
  for (int i=0; i<5; i++) {
    Property prop;
    prop.type = propTypes[i];
    prop.autoManualMode = false;
    cam.SetProperty(&prop);
  }

  // FIXME: should we be using pointgrey's various apis/techniques for detecting framerate?
  float frameRate = 60.0f;
  AVIOption option;
  option.frameRate = frameRate;

  // setup signal handler for termination
  signal(SIGTERM, term);

  error = cam.StartCapture();
  if (error != PGRERROR_OK)
    {
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
  if (error != PGRERROR_OK)
    {
      printError(error);
      return -1;
    }

  while (!g_finished && frameCount < maxFrames)
    {
      Image rawImage;
      error = cam.RetrieveBuffer(&rawImage);
      if (error != PGRERROR_OK)
        {
          printError(error);
          return -1;
        }

      if (printFrameNums)
        {
          struct timespec tp;
          if (debug)
            {
              clock_gettime(CLOCK_MONOTONIC, &tp);
              printf("%.4f %lu\n", (float)tp.tv_sec + (tp.tv_nsec/1000000000.0), frameCount);
            }
          else
            {
              printf("%lu\n", frameCount);
            }
          fflush(stdout);
        }

      vecImages[frameCount].DeepCopy(&rawImage);
      frameCount++;
    }

  error = cam.Disconnect();
  if (error != PGRERROR_OK)
    {
      printError(error);
      return -1;
    }

  for (int imageCnt = 0; imageCnt < frameCount; imageCnt++)
    {

      std::ostringstream fname;
      fname << videoOutputDir << "/" << "image-" << imageCnt << ".png";
      vecImages[imageCnt].Save(fname.str().c_str());
    }
}
