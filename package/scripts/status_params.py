#!/usr/bin/env python
from resource_management import *
import sys, os

config = Script.get_config()
nifi_dirname = 'nifi-0.3.0-SNAPSHOT'

nifi_pid_dir = config['configurations']['nifi-env']['nifi_pid_dir']
nifi_user= config['configurations']['nifi-env']['nifi_user']
nifi_group= config['configurations']['nifi-env']['nifi_group']
nifi_log_dir = config['configurations']['nifi-env']['nifi_log_dir']

nifi_install_dir = config['configurations']['nifi-ambari-config']['nifi.install_dir']
nifi_dir = os.path.join(*[nifi_install_dir,nifi_dirname]) 

nifi_pid_dir = nifi_pid_dir.replace('{{nifi_dir}}',nifi_dir)
nifi_pid_file=nifi_pid_dir + '/nifi.pid'