# encoding=utf8

import sys, os, pwd, grp, signal, time, glob
from resource_management import *
from subprocess import call
from resource_management.core.logger import Logger

reload(sys)
sys.setdefaultencoding('utf8')

class Master(Script):
  def install(self, env):

    import params
    import status_params
      

    #e.g. /var/lib/ambari-agent/cache/stacks/HDP/2.3/services/NIFI/package
    service_packagedir = os.path.realpath(__file__).split('/scripts')[0] 
            
    #Execute('find '+service_packagedir+' -iname "*.sh" | xargs chmod +x')

    #Create user and group if they don't exist
    self.create_linux_user(params.nifi_user, params.nifi_group)

            
    #create the log dir if it not already present - the below won't work on both Ambari 2.4 so re-writing
    
    Directory([status_params.nifi_pid_dir, params.nifi_log_dir],
            owner=params.nifi_user,
            group=params.nifi_group
    )
    
         
    Execute('touch ' +  params.nifi_log_file, user=params.nifi_user)    


    #Fetch and unzip snapshot build, if no cached nifi tar package exists on Ambari server node
    if not os.path.exists(params.temp_file):
      Execute('wget '+params.snapshot_package+' -O '+params.temp_file+' -a '  + params.nifi_log_file, user=params.nifi_user)

    Logger.info("Creating " + params.nifi_dir)
    Execute('rm -rf ' + params.nifi_dir, ignore_failures=True)
    Directory([params.nifi_dir],
            owner=params.nifi_user,
            group=params.nifi_group,
    )  

    #Execute('unzip '+params.temp_file+' -d ' + params.nifi_install_dir + ' >> ' + params.nifi_log_file, user=params.nifi_user)
    Execute('tar -xf '+params.temp_file+' -C '+ params.nifi_dir +' >> ' + params.nifi_log_file, user=params.nifi_user)
    #Execute('mv '+params.nifi_dir+'/*/*/* ' + params.nifi_dir, user=params.nifi_user)
    Execute('mv '+params.nifi_dir+'/*/* ' + params.nifi_dir, user=params.nifi_user)    
    Execute('find '+params.nifi_dir+' -type d -empty -delete', user=params.nifi_user) 

    self.configure(env, True)  
      

    
  def create_linux_user(self, user, group):
    try: pwd.getpwnam(user)
    except KeyError: Execute('adduser ' + user)
    try: grp.getgrnam(group)
    except KeyError: Execute('groupadd ' + group)

  

  def configure(self, env, isInstall=False):
    import params
    import status_params
    env.set_params(params)
    env.set_params(status_params)
    
    #write out nifi.properties
    properties_content=InlineTemplate(params.nifi_properties_content)
    File(format("{params.conf_dir}/nifi.properties"), content=properties_content, owner=params.nifi_user, group=params.nifi_group) # , mode=0777)    

    #write out flow.xml.gz only during install
    if isInstall:
      Execute('echo "First time setup so generating flow.xml.gz" >> ' + params.nifi_log_file)    
      flow_content=InlineTemplate(params.nifi_flow_content)
      File(format("{params.conf_dir}/flow.xml"), content=flow_content, owner=params.nifi_user, group=params.nifi_group)
      Execute(format("cd {params.conf_dir}; mv flow.xml.gz flow_$(date +%d-%m-%Y).xml.gz ;"),user=params.nifi_user,ignore_failures=True)
      Execute(format("cd {params.conf_dir}; gzip flow.xml;"), user=params.nifi_user)

    #write out boostrap.conf
    bootstrap_content=InlineTemplate(params.nifi_boostrap_content)
    File(format("{params.conf_dir}/bootstrap.conf"), content=bootstrap_content, owner=params.nifi_user, group=params.nifi_group) 

    #write out logback.xml
    #logback_content=InlineTemplate(params.nifi_logback_content)
    #File(format("{params.conf_dir}/logback.xml"), content=logback_content, owner=params.nifi_user, group=params.nifi_group) 
 
    #write out nifi-env in bin as 0755
    env_content=InlineTemplate(params.nifi_env_content)
    File(format("{params.bin_dir}/nifi-env.sh"), content=env_content, owner=params.nifi_user, group=params.nifi_group, mode=0755)    
    
    
  def stop(self, env):
    import params
    import status_params    

    Execute ('export JAVA_HOME='+params.jdk64_home+';'+params.bin_dir+'/nifi.sh stop >> ' + params.nifi_log_file, user=params.nifi_user)
    if os.path.isfile(status_params.nifi_node_pid_file):
      sudo.unlink(status_params.nifi_node_pid_file) 
      
  def start(self, env):
    import params
    import status_params
    self.configure(env) 
    Execute('echo pid file ' + status_params.nifi_pid_file)
    Execute('echo JAVA_HOME=' + params.jdk64_home)

    Execute ('export JAVA_HOME='+params.jdk64_home+';'+params.bin_dir+'/nifi.sh start >> ' + params.nifi_log_file, user=params.nifi_user)
    #If nifi pid file not created yet, wait a bit
    if not os.path.isfile(status_params.nifi_pid_dir+'/nifi.pid'):
      Execute ('sleep 5')
    
  def status(self, env):
    import status_params       
    check_process_status(status_params.nifi_node_pid_file)

  def install_mvn_repo(self):
    #for centos/RHEL 6/7 maven repo needs to be installed
    distribution = platform.linux_distribution()[0].lower()
    if distribution in ['centos', 'redhat'] and not os.path.exists('/etc/yum.repos.d/epel-apache-maven.repo'):
      Execute('curl -o /etc/yum.repos.d/epel-apache-maven.repo https://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo')


      
if __name__ == "__main__":
  Master().execute()
