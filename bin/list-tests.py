#!/usr/bin/env python

import eideticker

manifest = eideticker.get_test_manifest()
testkeys = [test["key"] for test in manifest.active_tests()]
for key in sorted(testkeys):
    print key

