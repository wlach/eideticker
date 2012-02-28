Project Eideticker
==================

Project Eideticker is an automated test harness that captures and analyzes
browser output (currently only on Fennec on Android, but support for other
platforms is planned).

### Requirements

* Linux system with zip, ffmpeg, and virtualenv installed. On Ubuntu, you can
  get this setup by running:

    sudo apt-get install -y ffmpeg zip virtualenv

* Blackmagic Design DeckLink card and the appropriate drivers.

 * Testing has been done with the DeckLink HD Extreme 3D; no idea if other
   cards would work.

* Installed Android SDK with the tools in your path. Please follow the
  instructions at https://wiki.mozilla.org/Mobile/Fennec/Android#Setup_a_Build_Environment

### Installation

Run `bootstrap.sh` in the root directory to set everything up.

### Usage

Eideticker is meant to be run in a virtualenv, so the first step is to set
that up in your shell by running this command within the root directory:

    source ./bin/activate

You should now be set to run tests! You should be able to run Eideticker
tests against any Android web browser, though currently only stock and
Fennec (both XUL and native) have been tested. Just run the following
on the command line:

    ./bin/runtest.py <appname> <path to test>

For example, to run the canvas clock example against Fennec nightly, try
this:

    ./bin/runtest.py org.mozilla.fennec src/tests/canvas/clock.html

A capture of this test should be stored in `captures` off the root eideticker
directory.

The recommended way of viewing captures (and performing analysis)
is through the Eideticker web interface. To run it, execute:

    ./bin/webapp.sh

Then connect to http://localhost:8080

(note that the first time you view them, there will be a several minute wait to
see frame difference and checkerboarding statistics -- please be patient!)
