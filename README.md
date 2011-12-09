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
your phone. Currently we only support the LG G2X, running Android 2.2.
Both native and XUL-based Fennec should work.

    ./bin/runtest.py <fennec appname> <path to test>

For example, to run the canvas clock example, try this:

    ./bin/runtest.py org.mozilla.fennec src/tests/canvas/clock.html

A capture of this test should be stored in `src/talos/captures`.

The recommended way of viewing captures (and performing analysis)
is through the Eideticker web interface. To run it, execute:

    ./bin/webapp.sh

Then connect to http://localhost:8080

(note that currently converting frames in the frame difference screen is rather
slow and there is no loading indicator, please be patient!)