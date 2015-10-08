#!/usr/bin/env python
from resource_management import *
import sys, os

config = Script.get_config()

nifi_pid_dir=config['configurations']['nifi-bootstrap-env']['nifi_pid_dir']
nifi_pid_file=nifi_pid_dir + '/nifi.pid'

