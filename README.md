# Overview

> [!NOTE]
> This charm is under maintenance mode. Only critical bug will be handled.

logrotate is a subordinate charm that ensure that all logrotate.d
configurations within /etc/logrotate.d/ folder are modified accordingly
to a retention period defined in the charm

# Build
```
cd charm-logrotate                                                                  
charm build
```

# Usage
Add to an existing application using juju-info relation.

Example:
```
juju deploy ubuntu
juju deploy ./charm-logrotate
juju add-unit ubuntu
juju add-relation ubuntu logrotate
```

# Configuration                                                                 
The user can configure the following parameters:
* ```logrotate-retention``` (default: ```180```): The logrotate retention period in days. The charm will go through `ALL` logrotate entries in /etc/logrotate.d/ and set the `rotate` config to the appropriate value, depending on the rotation interval used. For example if rotation is monthy and retention is 180 days -> `rotate 6` or rotation is daily and retention is 90 days -> `rotate 90` or rotation is weekly and retention is 21 days -> `rotate 3` Weekly will round up the week count, for example if retention is set to 180 days -> `rotate 26` (26 weeks x 7 days = 182 days) Yearly will put rotate to 1 and increase it with 1 for each 360 days. Monthly will round up, using 30 days for a month. Yearly will round up, adding a year for each 360 days.

* ```override```: (default: ```[]```): JSON formatted field containing a list of files that need to have custom logrotate interval and count. The format is as follows:
[ {"path": "/etc/logrotate.d/rotatefile", "rotate": 5, "interval": "weekly"}, {}, ... ]

Mind the double quotes for the properties/values!

    Valid options for rotate: any integer value
    Valid options for interval: 'daily', 'weekly', 'monthly', 'yearly'

# Testing                                                                       
Unit tests have been developed to test return values from the charm helper class, while modifying pre-defined string entries with the logrotate syntax.

To run unit tests:                                                              
```bash
tox -e unit
```
Functional tests have been developed using python-libjuju, deploying a simple ubuntu charm and adding logortate as a subordinate.

To run tests using python-libjuju:
```bash
tox -e functional
```


# Contact Information
Diko Parvanov <diko.parvanov@canonical.com>

