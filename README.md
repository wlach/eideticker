Project Eideticker
==================

Project Eideticker is an automated test harness that captures and analyzes
browser output (currently only on Fennec on Android, but support for other
platforms is planned).

### Requirements

* Linux system with zip and ffmpeg installed.

* Blackmagic Design DeckLink card and the appropriate drivers.

 * Testing has been done with the DeckLink HD Extreme 3D; no idea if other
   cards would work.


### Installation

Run `bootstrap.sh` in the root directory to set everything up.

### Usage

Eideticker is meant to be run in a virtualenv, so the first step is to set
that up in your shell by running this command within the root directory:

    source ./bin/activate

The next step is to configure Eideticker to work with a copy of Fennec on
your phone. Currently we only support the LG G2X, running Android 2.2,
rooted and with a fairly recent version of Fennec. Assuming this is your
configuration, you should be able to get Eideticker running by installing
SUTAgent on your device and then issuing the following commands:

    ./bin/setup.py <ip address of phone> \
                   <name of fennec application to test>

For example, I've built a custom version of fennec with the name
org.mozilla.fennec_wlach, and my phone has an ip address of 192.168.1.4.
I'd thus run setup-talos.sh as follows:

    ./bin/setup.py 192.168.1.4 org.mozilla.fennec_wlach

Once you've configured talos, you can capture the results of an eideticker
test with a single command:

    ./bin/runtest.py <name of test> <subtest>

For example, to run the SVG test hixie-007.xml, try this:

    ./bin/runtest.py tpageload tsvg:hixie-007.xml

You should then have a bunch of capture data stored in `src/talos/captures`.
You can run some basic analysis on the capture utility as follows:

    ./bin/analyze.py <captured file>

For example:

    ./bin/analyze.py  ./src/talos/talos/captures/capture-2011-11-11T11:23:51.627183.zip
