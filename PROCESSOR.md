## Getting started with ELs and custom Nifi processors on HDP

This tutorial is part of a webinar on Hortonworks DataFlow.
- http://hortonworks.com/partners/learn/

#### Background

Tcpdump is a common packet analyzer that runs under the command line. It allows the user to display TCP/IP and other packets being transmitted or received over a network to which the computer is attached. 

#### Goals 
- Build Nifi flow to run tcpdump. Use Expression Language to filter out source/target IPs 
- Build and use custom tcpdump processor to filter source/target IPs


#### Steps

##### Install Nifi on sandbox

- Download HDP 2.3 sandbox VM image (Sandbox_HDP_2.3_VMware.ova) from [Hortonworks website](http://hortonworks.com/products/hortonworks-sandbox/)
- Import Sandbox_HDP_2.3_VMware.ova into VMWare and set the VM memory size to 8GB
- Now start the VM
- After it boots up, find the IP address of the VM and add an entry into your machines hosts file. For example:
```
192.168.191.241 sandbox.hortonworks.com sandbox    
```
  - Note that you will need to replace the above with the IP for your own VM
  
- Connect to the VM via SSH (password hadoop)
```
ssh root@sandbox.hortonworks.com
```

- (Optional) To see Nifi metrics in Ambari, login to Ambari (admin/admin) and start Ambari Metrics service 
http://sandbox.hortonworks.com:8080

- To download the NiFi service folder, run below
```
VERSION=`hdp-select status hadoop-client | sed 's/hadoop-client - \([0-9]\.[0-9]\).*/\1/'`
sudo git clone https://github.com/abajwa-hw/ambari-nifi-service.git   /var/lib/ambari-server/resources/stacks/HDP/$VERSION/services/NIFI   
```

- Restart Ambari
```
#sandbox
service ambari restart

#non sandbox
sudo service ambari-server restart
```

- Then you can click on 'Add Service' from the 'Actions' dropdown menu in the bottom left of the Ambari dashboard:

On bottom left -> Actions -> Add service -> check NiFi server -> Next -> Next -> Change any config you like (e.g. install dir, port, setup_prebuilt or values in nifi.properties) -> Next -> Deploy

#####  Build tcpdump flow using ExecuteProcess and EL

- install tcdump
```
yum install -y tcpdump
```

- import template for flow that uses ExecuteProcess/EL to parse tcpdump flow
```
wget https://www.dropbox.com/s/2c19wdmay9k9lxh/network-analysis.zip
```

- Run the flow and note what each component is doing
  - TODO: add details

#####  Build custom processor for tcpdump

- setup sandbox for development by using [VNC Ambari service](https://github.com/hortonworks-gallery/ambari-vnc-service) to install VNC/eclipse/maven
  - Download Ambari service for VNC (details below)
```  
VERSION=`hdp-select status hadoop-client | sed 's/hadoop-client - \([0-9]\.[0-9]\).*/\1/'`
sudo git clone https://github.com/hortonworks-gallery/ambari-vnc-service.git   /var/lib/ambari-server/resources/stacks/HDP/$VERSION/services/VNCSERVER   
service ambari restart
```

- Once the status of HDFS/YARN has changed from a yellow question mark to a green check mark...
- Setup Eclipse on the sandbox VM and remote desktop into it using an Ambari service for VNC
- In Ambari open, Admin > Stacks and Services tab. You can access this via http://sandbox.hortonworks.com:8080/#/main/admin/stack/services
- Deploy the service by selecting:
  - VNC Server -> Add service -> Next -> Next -> Enter password (e.g. hadoop) -> Next -> Proceed Anyway -> Deploy
  - Make sure the password is at least 6 characters or install will fail
- Connect to VNC from local laptop using a VNC viewer software (e.g. Tight VNC viewer or Chicken of the VNC or just your browser). Detailed steps [here](https://github.com/hortonworks-gallery/ambari-vnc-service)

- mvn archetype to setup project
- import sample code to eclipse
- code walk through
- Build nar and deploy: copy into Nifi lib dir and restart Nifi
- import template for flow that uses custom processor to parse tcpdump
- run the flow

