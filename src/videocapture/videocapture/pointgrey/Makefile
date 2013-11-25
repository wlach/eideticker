CC = g++
CFLAGS = -I/usr/include/flycapture
LDFLAGS = -lflycapture
JSON_OBJECTS = JSON.o JSONValue.o

%.o: %.cpp
	g++ $< -c -o $@ $(CFLAGS) -g
	@g++ $< -MM $(CFLAGS) > $*.d
	@mv -f $*.d $*.d.tmp
	@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
	@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
		sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
	@rm -f $*.d.tmp

default: pointgrey-capture get-camera-id setup-camera dump-current-settings

pointgrey-capture: $(JSON_OBJECTS) pointgrey-capture.o settings.o
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS)

dump-current-settings: dump-current-settings.o
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS)

setup-camera: setup-camera.o settings.o $(JSON_OBJECTS)
	$(CC) -o $@ $^  $(CFLAGS) $(LDFLAGS)

get-camera-id: get-camera-id.o
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS)

clean:
	rm -f pointgrey-capture get-camera-id setup-camera dump-current-settings *.o *.d

-include $(OBJECTS:.o=.d)
