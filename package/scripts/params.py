#!/usr/bin/env python
from resource_management import *
from resource_management.libraries.script.script import Script
import sys, os, glob
from resource_management.libraries.functions.version import format_hdp_stack_version
from resource_management.libraries.functions.default import default


    
# server configurations
config = Script.get_config()

#nifi_dirname = 'nifi-0.3.0-SNAPSHOT'
#nifi_dirname = 'nifi-0.3.0'
#nifi_dirname = 'nifi-1.1.1.0-12'
nifi_dirname = 'HDF-1.2.0.1-1' 
    
# params from nifi-ambari-config
nifi_install_dir = config['configurations']['nifi-ambari-config']['nifi.install_dir']
nifi_port = config['configurations']['nifi-ambari-config']['nifi.port']
setup_prebuilt = config['configurations']['nifi-ambari-config']['nifi.setup_prebuilt']
nifi_initial_mem = config['configurations']['nifi-ambari-config']['nifi.initial_mem']
nifi_max_mem = config['configurations']['nifi-ambari-config']['nifi.max_mem']
nifi_ambari_reporting_frequency = config['configurations']['nifi-ambari-config']['nifi.ambari_reporting_frequency']


nifi_dir = os.path.join(*[nifi_install_dir,nifi_dirname]) 
conf_dir=''
bin_dir=''

# params from nifi-boostrap
nifi_boostrap_content = config['configurations']['nifi-bootstrap-env']['content']
nifi_user = config['configurations']['nifi-bootstrap-env']['nifi_user']
nifi_group = config['configurations']['nifi-bootstrap-env']['nifi_group']
nifi_log_dir = config['configurations']['nifi-bootstrap-env']['nifi_log_dir']
nifi_log_file = os.path.join(nifi_log_dir,'nifi-setup.log')

# params from nifi-logback
nifi_logback_content = config['configurations']['nifi-logback-env']['content']

# params from nifi-properties-env
nifi_properties_content = config['configurations']['nifi-properties-env']['content']
  
# params from nifi-flow
nifi_flow_content = config['configurations']['nifi-flow-env']['content']




#autodetect jdk home
jdk64_home=config['hostLevelParams']['java_home']

#autodetect ambari server for metrics
if 'metrics_collector_hosts' in config['clusterHostInfo']:
  metrics_collector_host = str(config['clusterHostInfo']['metrics_collector_hosts'][0])
  metrics_collector_port = str(get_port_from_url(config['configurations']['ams-site']['timeline.metrics.service.webapp.address']))
else:
  metrics_collector_host = ''
  metrics_collector_port = ''

temp_file='/tmp/'+nifi_dirname+'.zip'
