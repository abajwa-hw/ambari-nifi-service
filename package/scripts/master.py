import sys, os, pwd, grp, signal, time, glob
from resource_management import *
from subprocess import call

class Master(Script):
  def install(self, env):

    import params
    import status_params
      

    #location of prebuilt package from 9/3   
    snapshot_package='https://www.dropbox.com/s/la1c25xq9zd8w5g/nifi-0.3.0-SNAPSHOT-bin.zip'

        
    #e.g. /var/lib/ambari-agent/cache/stacks/HDP/2.3/services/NIFI/package
    service_packagedir = os.path.realpath(__file__).split('/scripts')[0] 
            
    Execute('find '+service_packagedir+' -iname "*.sh" | xargs chmod +x')

    #Create user and group if they don't exist
    self.create_linux_user(params.nifi_user, params.nifi_group)
    Execute('cp /etc/sudoers /etc/sudoers.bak')        
    Execute('echo "'+params.nifi_user+'    ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers')
    Execute('echo Creating ' +  params.nifi_log_dir +  ' ' +  params.nifi_pid_dir)    


            
    #create the log dir if it not already present
    Directory([params.nifi_pid_dir, params.nifi_log_dir],
            owner=params.nifi_user,
            group=params.nifi_group,
            recursive=True
    )   
         
    Execute('touch ' +  params.nifi_log_file, user=params.nifi_user)    
    Execute('rm -rf ' + params.nifi_dir, ignore_failures=True)
    Execute('mkdir -p '+params.nifi_dir)
    Execute('chown -R ' + params.nifi_user + ':' + params.nifi_group + ' ' + params.nifi_dir)
    
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
      #Execute('mv '+params.nifi_dir+'/*/* ' + params.nifi_dir, user=params.nifi_user)
          
      
      #update the configs specified by user
      self.configure(env)

      
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
        #self.install_packages(env)    
    
      Execute('yum -y install java-1.7.0-openjdk-devel >> ' + params.nifi_log_file)
      
      Execute('echo Compiling nifi from source')
      Execute('cd '+params.nifi_install_dir+'; git clone https://git-wip-us.apache.org/repos/asf/nifi.git '+params.nifi_dir+' >> ' + params.nifi_log_file)
      Execute('chown -R ' + params.nifi_user + ':' + params.nifi_group + ' ' + params.nifi_dir)
                  
      Execute('cd '+params.nifi_dir+'; mvn -T C2.0 clean install -DskipTests >> ' + params.nifi_log_file, user=params.nifi_user)
      
      #update the configs specified by user
      self.configure(env)
            
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

  

  def configure(self, env):
    import params
    import status_params
    env.set_params(params)
    env.set_params(status_params)
    
    #write out nifi-env.sh
    env_content=InlineTemplate(params.nifi_env_content)
    File(format("{params.conf_dir}/nifi.properties"), content=env_content, owner=params.nifi_user, group=params.nifi_group) # , mode=0777)    
    
  def stop(self, env):
    import params
    import status_params    
    Execute (params.bin_dir+'/nifi.sh stop >> ' + params.nifi_log_file, user=params.nifi_user)
    Execute ('rm /var/run/nifi.pid')
 
      
  def start(self, env):
    import params
    import status_params
    self.configure(env) 
    Execute('echo pid file ' + status_params.nifi_pid_file)
    Execute (params.bin_dir+'/nifi.sh start >> ' + params.nifi_log_file, user=params.nifi_user)

    Execute("cat "+status_params.nifi_pid_file+" | grep pid | sed 's/pid=\(\.*\)/\\1/' > /var/run/nifi.pid")
    Execute('chown '+params.nifi_user+':'+params.nifi_group+' /var/run/nifi.pid')
    
  def status(self, env):       
    check_process_status('/var/run/nifi.pid')

  def install_mvn_repo(self):
    #for centos/RHEL 6/7 maven repo needs to be installed
    distribution = platform.linux_distribution()[0].lower()
    if distribution in ['centos', 'redhat'] and not os.path.exists('/etc/yum.repos.d/epel-apache-maven.repo'):
      Execute('curl -o /etc/yum.repos.d/epel-apache-maven.repo https://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo')

      
if __name__ == "__main__":
  Master().execute()
