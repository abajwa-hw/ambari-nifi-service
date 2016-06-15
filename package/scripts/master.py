# encoding=utf8

import sys, os, pwd, grp, signal, time, glob
from resource_management import *
from subprocess import call

reload(sys)
sys.setdefaultencoding('utf8')

class Master(Script):
  def install(self, env):

    import params
    import status_params
      

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
    snapshot_package='http://public-repo-1.hortonworks.com/HDF/centos6/1.x/updates/1.2.0.1/HDF-1.2.0.1-1.zip'

    #e.g. /var/lib/ambari-agent/cache/stacks/HDP/2.3/services/NIFI/package
    service_packagedir = os.path.realpath(__file__).split('/scripts')[0] 
            
    #Execute('find '+service_packagedir+' -iname "*.sh" | xargs chmod +x')

    #Create user and group if they don't exist
    self.create_linux_user(params.nifi_user, params.nifi_group)
    if params.nifi_user != 'root':
      Execute('cp /etc/sudoers /etc/sudoers.bak')        
      Execute('echo "'+params.nifi_user+'    ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers')
      Execute('echo Creating ' +  params.nifi_log_dir +  ' ' +  status_params.nifi_pid_dir)    


            
    #create the log dir if it not already present
    Directory([status_params.nifi_pid_dir, params.nifi_log_dir],
            owner=params.nifi_user,
            group=params.nifi_group,
            recursive=True
    )   
         
    Execute('touch ' +  params.nifi_log_file, user=params.nifi_user)    
    Execute('rm -rf ' + params.nifi_dir, ignore_failures=True)
    #Execute('mkdir -p '+params.nifi_dir)
    #Execute('chown -R ' + params.nifi_user + ':' + params.nifi_group + ' ' + params.nifi_dir)

    Directory([params.nifi_dir],
            owner=params.nifi_user,
            group=params.nifi_group,
            recursive=True
    )  
        
    #User selected option to use prebuilt nifi package 
    if params.setup_prebuilt:

      Execute('echo Installing packages')
        
      #Install maven repo if needed      
      #self.install_mvn_repo()
      # Install packages listed in metainfo.xml
      #self.install_packages(env)    



      #Fetch and unzip snapshot build, if no cached nifi tar package exists on Ambari server node
      if not os.path.exists(params.temp_file):
        Execute('wget '+snapshot_package+' -O '+params.temp_file+' -a '  + params.nifi_log_file, user=params.nifi_user)
      Execute('unzip '+params.temp_file+' -d ' + params.nifi_install_dir + ' >> ' + params.nifi_log_file, user=params.nifi_user)
      Execute('mv '+params.nifi_dir+'/*/* ' + params.nifi_dir, user=params.nifi_user)
          

      #params.conf_dir = os.path.join(*[params.nifi_install_dir,params.nifi_dirname,'conf'])
      #params.bin_dir = os.path.join(*[params.nifi_install_dir,params.nifi_dirname,'bin'])
      
      #update the configs specified by user
      self.configure(env, True)

      #Execute('wget https://www.dropbox.com/s/n82hxkeg8ri0z70/flow.xml.gz -O '+params.conf_dir+'/flow.xml.gz',user=params.nifi_user)
      
      #run setup_snapshot.sh in FIRSTLAUNCH mode
      #Execute(service_packagedir + '/scripts/setup_snapshot.sh '+params.nifi_dir+' '+params.hive_server_host+' '+params.hive_metastore_host+' '+params.hive_metastore_port+' FIRSTLAUNCH ' + params.spark_jar + ' ' + params.nifi_host + ' ' + str(params.nifi_port) + ' '+ str(params.setup_view) + ' >> ' + params.nifi_log_file, user=params.nifi_user)

      #if nifi installed on ambari server, copy view jar into ambari views dir
      #if params.setup_view:
      #  if params.ambari_host == params.nifi_internalhost and not os.path.exists('/var/lib/ambari-server/resources/views/nifi-view-1.0-SNAPSHOT.jar'):
      #    Execute('echo "Copying nifi view jar to ambari views dir"')      
      #    Execute('cp /home/'+params.nifi_user+'/nifi-view/target/*.jar /var/lib/ambari-server/resources/views')
      
    else:
      #User selected option to build nifi from source
       
      #if params.setup_view:
        #Install maven repo if needed
      self.install_mvn_repo()      
      # Install packages listed in metainfo.xml
      self.install_packages(env)    
    
      # Execute('yum -y install java-1.7.0-openjdk-devel >> ' + params.nifi_log_file)
      
      Execute('echo Compiling nifi from source')
      Execute('cd '+params.nifi_install_dir+'; git clone https://git-wip-us.apache.org/repos/asf/nifi.git '+params.nifi_dir+' >> ' + params.nifi_log_file)
      Execute('chown -R ' + params.nifi_user + ':' + params.nifi_group + ' ' + params.nifi_dir)
                  
      Execute('cd '+params.nifi_dir+'; mvn -T C2.0 clean install -DskipTests >> ' + params.nifi_log_file, user=params.nifi_user)
      
      #params.conf_dir =  glob.glob(params.nifi_install_dir + '/' + params.nifi_dirname + '/nifi-assembly/target/nifi-*/nifi-*/conf')[0]
      #params.bin_dir =  glob.glob(params.nifi_install_dir + '/' + params.nifi_dirname + '/nifi-assembly/target/nifi-*/nifi-*/bin')[0]

      #update the configs specified by user
      self.configure(env, True)
      #Execute('wget https://www.dropbox.com/s/n82hxkeg8ri0z70/flow.xml.gz -O '+params.conf_dir+'/flow.xml.gz',user=params.nifi_user)
      
      #if nifi installed on ambari server, copy view jar into ambari views dir
      #if params.setup_view:
      #  if params.ambari_host == params.nifi_internalhost and not os.path.exists('/var/lib/ambari-server/resources/views/nifi-view-1.0-SNAPSHOT.jar'):
      #    Execute('echo "Copying nifi view jar to ambari views dir"')      
      #    Execute('cp /home/'+params.nifi_user+'/nifi-view/target/*.jar /var/lib/ambari-server/resources/views')


    
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
    
    self.set_conf_bin(env)
    
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
    logback_content=InlineTemplate(params.nifi_logback_content)
    File(format("{params.conf_dir}/logback.xml"), content=logback_content, owner=params.nifi_user, group=params.nifi_group) 
    
    
    
  def stop(self, env):
    import params
    import status_params    
    self.set_conf_bin(env)    
    Execute (params.bin_dir+'/nifi.sh stop >> ' + params.nifi_log_file, user=params.nifi_user)
    Execute ('rm ' + status_params.nifi_pid_file)
 
      
  def start(self, env):
    import params
    import status_params
    self.configure(env) 
    self.set_conf_bin(env)    
    Execute('echo pid file ' + status_params.nifi_pid_file)
    Execute('echo JAVA_HOME=' + params.jdk64_home)

    Execute ('export JAVA_HOME='+params.jdk64_home+';'+params.bin_dir+'/nifi.sh start >> ' + params.nifi_log_file, user=params.nifi_user)

    Execute('cat '+params.bin_dir+'/nifi.pid'+" | grep pid | sed 's/pid=\(\.*\)/\\1/' > " + status_params.nifi_pid_file)
    Execute('chown '+params.nifi_user+':'+params.nifi_group+' ' + status_params.nifi_pid_file)
    
  def status(self, env):
    import status_params       
    check_process_status(status_params.nifi_pid_file)

  def install_mvn_repo(self):
    #for centos/RHEL 6/7 maven repo needs to be installed
    distribution = platform.linux_distribution()[0].lower()
    if distribution in ['centos', 'redhat'] and not os.path.exists('/etc/yum.repos.d/epel-apache-maven.repo'):
      Execute('curl -o /etc/yum.repos.d/epel-apache-maven.repo https://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo')

  def set_conf_bin(self, env):
    import params
  
    if params.setup_prebuilt:
      params.conf_dir = os.path.join(*[params.nifi_install_dir,params.nifi_dirname,'conf'])
      params.bin_dir = os.path.join(*[params.nifi_install_dir,params.nifi_dirname,'bin'])
    else:
      params.conf_dir =  glob.glob(params.nifi_install_dir + '/' + params.nifi_dirname + '/nifi-assembly/target/nifi-*/nifi-*/conf')[0]
      params.bin_dir =  glob.glob(params.nifi_install_dir + '/' + params.nifi_dirname + '/nifi-assembly/target/nifi-*/nifi-*/bin')[0]

      
if __name__ == "__main__":
  Master().execute()
