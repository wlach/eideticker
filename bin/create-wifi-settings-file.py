#!/usr/bin/env python

import json
import sys

if len(sys.argv) != 2 and len(sys.argv) != 4:
    print "USAGE: %s <SSID> [SECURITY MODEL (WEP or WPA-PSK)] [PASSWORD]"
    sys.exit(1)

network = { 'ssid': sys.argv[1] }
if len(sys.argv) == 4:
    (key_management, passphrase) = sys.argv[2:]
    network['keyManagement'] = key_management
    if key_management == 'WEP':
        network['wep'] = passphrase
    else:
        network['psk'] = passphrase
else:
    network['keyManagement'] = 'NONE'

print json.dumps(network)
