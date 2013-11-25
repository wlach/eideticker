#include <sys/stat.h>
#include <unistd.h>
#include "JSON.h"
#include "FlyCapture2.h"

using namespace FlyCapture2;

PropertyType getPropertyType(const std::wstring propertyTypeStr)
{
  if (propertyTypeStr == L"BRIGHTNESS") return BRIGHTNESS;
  else if (propertyTypeStr == L"AUTO_EXPOSURE") return AUTO_EXPOSURE;
  else if (propertyTypeStr == L"SHARPNESS") return SHARPNESS;
  else if (propertyTypeStr == L"SHUTTER") return SHUTTER;
  else if (propertyTypeStr == L"GAIN") return GAIN;
  else if (propertyTypeStr == L"FRAME_RATE") return FRAME_RATE;
  else if (propertyTypeStr == L"WHITE_BALANCE") return WHITE_BALANCE;

  char propertyLabel[40];
  wcstombs(propertyLabel, propertyTypeStr.c_str(), 40);
  fprintf(stderr, "Error: Unknown property type '%s'\n", propertyLabel);
  exit(1);
}

void processPropertiesFile(const char *filename, Camera &cam)
{
  struct stat st;
  if (stat(filename, &st) != 0) {
    fprintf(stderr, "Error processing prefs file '%s': can't stat", filename);
  }
  char *contents = new char[st.st_size + 1];
  FILE *fp = fopen(filename, "r");
  fread(contents, st.st_size, 1, fp);
  contents[st.st_size] = '\0';
  JSONValue *prefdict = JSON::Parse(contents);
  if (!prefdict) {
    fprintf(stderr, "Error processing prefs file '%s': not valid JSON\n", filename);
    exit(1);
  }
  if (!prefdict->IsObject()) {
    fprintf(stderr, "Error processing prefs file '%s': root not a JSON object\n", filename);
    exit(1);
  }

  JSONObject root = prefdict->AsObject();
  JSONObject properties = root[L"properties"]->AsObject();
  for (JSONObject::iterator iter = properties.begin();
       iter != properties.end(); iter++) {
    Property property;

    property.type = getPropertyType(iter->first);
    cam.GetProperty(&property);
    char pname[512];
    wcstombs(pname, iter->first.c_str(), 512);

    JSONObject propertySettings = iter->second->AsObject();
    for (JSONObject::iterator iter2 = propertySettings.begin();
         iter2 != propertySettings.end(); iter2++) {
      if (iter2->first == L"onOff" || iter2->first == L"autoManualMode") {
        if (!iter2->second->IsBool()) {
          fprintf(stderr, "Error: Expected onOff/auto property to be boolean, was not\n");
          exit(1);
        }
        if (iter2->first == L"onOff")
          property.onOff = iter2->second->AsBool();
        else
          property.autoManualMode = iter2->second->AsBool();
      }
      else if (iter2->first == L"absValue" || iter2->first == L"valueA" ||
               iter2->first == L"valueB") {
        if (!iter2->second->IsNumber()) {
          fprintf(stderr, "Error: Expected absValue/valueA/valueB property "
                  "to be a number, was not\n");
          exit(1);
        }
        if (iter2->first == L"absValue")
          property.absValue = iter2->second->AsNumber();
        else if (iter2->first == L"valueA")
          property.valueA = iter2->second->AsNumber();
        else
          property.valueB = iter2->second->AsNumber();
      }
    }
    cam.SetProperty(&property);
  }
}
