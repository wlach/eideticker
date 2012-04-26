Project Eideticker
==================

Project Eideticker is an automated test harness that captures and analyzes
browser output via HDMI (currently only on Fennec on Android, but support for
other platforms is planned).

### Requirements

* Linux system with zip, ffmpeg, and virtualenv installed. On Ubuntu, you can
  get this setup by running:

    `sudo apt-get install -y ffmpeg zip python-virtualenv`

* Blackmagic Design DeckLink HD Extreme 3D card and the appropriate drivers if
  you want to actually capture video (it is possible to use the Eideticker
  harness without the video capture step, which can be useful for certain
  cases: see below).

* Installed Android SDK with the tools in your path. Please follow the
  instructions at https://wiki.mozilla.org/Mobile/Fennec/Android#Setup_a_Build_Environment

### Installation

Run `bootstrap.sh` in the root directory to set everything up.

Eideticker comes with a default suite of non-copyrighted tests. If you want
to run tests against copyrighted sites, you'll want to download and extract
the ep1 pageset into `src/tests`:

    wget <ep1 url>
    cd src/tests && tar jxf ../../ep1.tar.bz2

### Usage

Eideticker is meant to be run in a virtualenv, so the first step is to set
that up in your shell by running this command within the root directory:

    source ./bin/activate

Now, connect your Android device to your computer's USB port. That's it,
you should now be set to run tests! Eideticker currently supports two methods
of running tests: console mode and dashboard mode.

#### Console Mode

Console mode is meant for internal profiling. You run a program
called get-metric-for-build.py with a specific test against an Android apk,
and out will pop several results.

    ./bin/get-metric-for-build.py <apk of build> <test>

For example, to run the canvas clock example against Fennec nightly, try
this:

    ./bin/get-metric-for-build.py nightly.apk src/tests/canvas/clock.html

If you want to know more about the results (where the numbers are coming from)
you can open them up inside the Eideticker web interface. To open it, execute:

    ./bin/webapp.sh

Then connect to http://localhost:8080

In addition to supporting HDMI capture and analysis, it is also possible to run
the Eideticker harness in a mode that simply "captures" the performance log
of Fennec and outputs results. This has two advantages: first, you don't need
any kind of specialized hardware. Second, it's much faster (since there's no
video encoding/decoding/analysis step). For this you want to pass in
"--no-capture" and "--get-internal-checkerboard-stats", like so:

    ./bin/get-metric-for-build.py --no-capture --get-internal-checkerboard-stats nightly.apk src/tests/scrolling/taskjs.org/index.html

Note that for this to work Fennec performance logging will need to be enabled,
which it isn't by default. Make it so by running:

    adb shell setprop log.tag.GeckoLayerRendererProf DEBUG

#### Dashboard Mode

Dashboard mode is used to generate a dashboard of eideticker results, like
what you see at http://wrla.ch/eideticker/dashboard. From a toplevel, it
is run from a script called `bin/run-update-dashboard.sh`, which can be called
standalone. This script then it turn calls another script called
`bin/update-dashboard.py` with various arguments corresponding to firefox
version, test to run, etc. The dashboard is currently under heavy development
and is not meant to be a developer/qa facing tool. For now, if you have need
to use/modify it, please refer to the source.
