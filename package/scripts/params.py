#!/usr/bin/env python
from resource_management import *
from resource_management.libraries.script.script import Script
import sys, os, glob, socket
from resource_management.libraries.functions.default import default


    
# server configurations
config = Script.get_config()

#location of prebuilt package from 9/3
#snapshot_package='https://www.dropbox.com/s/la1c25xq9zd8w5g/nifi-0.3.0-SNAPSHOT-bin.zip'

#official 0.3
#snapshot_package='http://apache.arvixe.com/nifi/0.3.0/nifi-0.3.0-bin.zip'

#official HDF 1.0 package (same as apache 0.3.0)
#snapshot_package='http://public-repo-1.hortonworks.com/HDF/1.0.0.0/nifi-1.0.0.0-7-bin.zip'

#official HDF 1.1.1 package (nifi 0.4.1)
#snapshot_package='http://public-repo-1.hortonworks.com/HDF/1.1.1.0/nifi-1.1.1.0-12-bin.zip'

#official HDF 1.1.2 package
#snapshot_package='http://public-repo-1.hortonworks.com/HDF/1.1.2.0/nifi-0.5.1.1.1.2.0-32-bin.zip'

#official HDF 1.2 package (nifi 0.6.0)
#snapshot_package='http://public-repo-1.hortonworks.com/HDF/centos6/1.x/updates/1.2.0.0/HDF-1.2.0.0-91.zip'

# HDF 1.2.0.1
# snapshot_package='http://public-repo-1.hortonworks.com/HDF/centos6/1.x/updates/1.2.0.1/HDF-1.2.0.1-1.zip'

# HDF 2.0
# snapshot_package='http://public-repo-1.hortonworks.com/HDF/2.0.0.0/HDF-2.0.0.0-579.tar.gz'

# HDF 2.1
#snapshot_package='http://public-repo-1.hortonworks.com/HDF/centos6/2.x/updates/2.1.0.0/tars/nifi/nifi-1.1.0.2.1.0.0-165-bin.tar.gz'

# HDF 2.1.2.0
snapshot_package='https://public-repo-1.hortonworks.com/HDF/2.1.2.0/nifi-1.1.0.2.1.2.0-10-bin.tar.gz'
        
# params from nifi-ambari-config
nifi_install_dir = config['configurations']['nifi-ambari-config']['nifi.install_dir']
nifi_port = config['configurations']['nifi-ambari-config']['nifi.port']
setup_prebuilt = config['configurations']['nifi-ambari-config']['nifi.setup_prebuilt']
nifi_initial_mem = config['configurations']['nifi-ambari-config']['nifi.initial_mem']
nifi_max_mem = config['configurations']['nifi-ambari-config']['nifi.max_mem']
nifi_ambari_reporting_frequency = config['configurations']['nifi-ambari-config']['nifi.ambari_reporting_frequency']
nifi_node_protocol_port = config['configurations']['nifi-ambari-config']['nifi.node.protocol.port']
filename = os.path.basename(snapshot_package)
nifi_dirname = os.path.splitext(filename)[0]
nifi_dirname = os.path.splitext(nifi_dirname)[0]

nifi_dir = os.path.join(*[nifi_install_dir,nifi_dirname])

conf_dir = os.path.join(*[nifi_dir,'conf'])
bin_dir = os.path.join(*[nifi_dir,'bin'])

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
# params from nifi-env
nifi_env_content = config['configurations']['nifi-env']['content']


#autodetect jdk home
jdk64_home=config['hostLevelParams']['java_home']

#hack for current sandbox where ambari still uses java 7
sandbox_jdk8_loc = '/usr/lib/jvm/jre-1.8.0-openjdk.x86_64'
if os.path.isfile(sandbox_jdk8_loc + '/bin/java'):
  jdk64_home = sandbox_jdk8_loc

#autodetect ambari server for metrics
if 'metrics_collector_hosts' in config['clusterHostInfo']:
  metrics_collector_host = str(config['clusterHostInfo']['metrics_collector_hosts'][0])
  metrics_collector_port = str(get_port_from_url(config['configurations']['ams-site']['timeline.metrics.service.webapp.address']))
else:
  metrics_collector_host = ''
  metrics_collector_port = ''

master_configs = config['clusterHostInfo']
nifi_master_hosts = master_configs['nifi_master_hosts']
# kafka_broker_host = str(master_configs['kafka_broker_hosts'][0])

# detect if running in single (sandbox) box
nifi_num_nodes = len(master_configs['nifi_master_hosts'])
nifi_node_host = socket.getfqdn()

if nifi_num_nodes > 1:
  nifi_is_node='true'
else:
  nifi_is_node='false'

#detect zookeeper_quorum
zookeeper_port=default('/configurations/zoo.cfg/clientPort', None)
#get comma separated list of zookeeper hosts from clusterHostInfo
index = 0
zookeeper_quorum=""
for host in config['clusterHostInfo']['zookeeper_hosts']:
  zookeeper_quorum += host + ":"+str(zookeeper_port)
  index += 1
  if index < len(config['clusterHostInfo']['zookeeper_hosts']):
    zookeeper_quorum += ","

temp_file='/tmp/'+nifi_dirname+'.tar.gz'
