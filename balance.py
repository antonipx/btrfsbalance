import os
import sys
import subprocess
import re
dev_size=0
dev_alloc=0
dev_used=0
data_size=0
data_used=0
meta_size=0
meta_used=0
syst_size=0
syst_used=0
free=0
free_expected=0
verbose=0
MB=float(1024*1024)
# Temporarily set to always run rebalance
force=1
# These need to be tuned
optimal_usage_threshold=90
default_dusage=0
if len(sys.argv) == 1:
    print "Need a valid mount path"
    sys.exit(0)
else:
    mountpath = sys.argv[1]
    print "Using mount path: " + mountpath
try:
    out=subprocess.check_output(['btrfs', 'fi', 'usage', '-b', mountpath])
except subprocess.CalledProcessError as e:
    print "Failed to retrieve FS usage"
    sys.exit(0)
for line in out.splitlines():
    if not dev_size:
        m=re.match('^\s*Device size:\s*([0-9]+)', line)
        if m:
            dev_size=m.group(1)
    if not dev_alloc:
        m=re.match('^\s*Device allocated:\s*([0-9]+)', line)
        if m:
		dev_alloc=m.group(1)
    if not dev_used:
        m=re.match('^\s*Used:\s*([0-9]+)', line)
        if m:
            dev_used=m.group(1)
    if not data_size:
        m=re.match('^Data,.*Size:([0-9]+), Used:([0-9]+)', line)
        if m:
            data_size=m.group(1)
            data_used=m.group(2)
    if not meta_size:
        m=re.match('^Metadata,.*Size:([0-9]+), Used:([0-9]+)', line)
        if m:
            meta_size=m.group(1)
            meta_used=m.group(2)
    if not syst_size:
        m=re.match('^System,.*Size:([0-9]+), Used:([0-9]+)', line)
        if m:
            syst_size=m.group(1)
            syst_used=m.group(2)
    if not free:
        m=re.match('^\s*Free.*?:\s*([0-9]+).*', line)
        if m:
            free=m.group(1)

if verbose:
    print "dev_size ", dev_size
    print "dev_alloc", dev_alloc
    print "dev_used ", dev_used
    print "data_size", data_size
    print "data_used", data_used
    print "meta_size", meta_size
    print "meta_used", meta_used
    print "free", free
# Expected free based on what is used 
free_expected=int(dev_size)-int(dev_used)
# This delta represents space locked by outstanding frees
delta=float((float(free_expected) - float(free)) / MB)
delta_pct=float(100 * (float(free_expected) - float(free)) / float(free_expected))
# Used over allocated, a low number indicated empty unused chunks
total_used_pct=float(100 * float(dev_used) / float(dev_alloc))
datapart_used_pct=float(100 * float(data_used) / float(data_size))
metapart_used_pct=float(100 * float(meta_used) / float(meta_size))
print "FS free: {0:.2f}".format(float(free) / MB) + "MB Expected: {0:.2f}".format(float(free_expected) / MB) + "MB"
print "Free delta is: " + "{0:.2f}".format(delta)  + "MB (" + "{0:.2f}%".format(float(delta_pct)) + ")"
print "\nOverall used is {0:.2f}% of allocation".format(total_used_pct)
print "Data partition used is {0:.2f}% of allocation".format(datapart_used_pct)
print "Metadata partition used is {0:.2f}% of allocation".format(metapart_used_pct)
# If the percent used of allocated is below optimal_usage_threshold then start rebalance
if force or (100 * float(dev_used) / float(dev_alloc)) <= optimal_usage_threshold:
    print "\nStarting rebalance on: " + mountpath
    dusage="-dusage="+str(default_dusage)
    try:
        out=subprocess.check_output(['btrfs', 'balance', 'start', dusage, mountpath])
    except subprocess.CalledProcessError as e:
        print "Failed to start rebalance"
    print out
