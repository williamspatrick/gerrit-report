#!/bin/env python

import subprocess
import json

def changes():
    s = subprocess.getoutput("ssh openbmc.gerrit gerrit query " +
                             "--format json --all-reviewers " +
                             "--current-patch-set -- " +
                             "'age:1d status:open -is:draft " +
                             "label:Code-Review>=-1 " +
                             "-project:openbmc/openbmc-test-automation'")

    changes = list(map(json.loads, s.splitlines()))
    del changes[-1]

    return changes


for c in changes():
    print(c['subject'])

