#### An Ambari Service for NiFi
Ambari service for easily installing and managing NiFi on HDP cluster and viewing metrics.

Features:

- By default, downloads a prebuilt version of 0.3.0 (to get around the Solr issue)
- But also gives option to build Nifi from source instead
- Exposes nifi.properties, bootstrap.conf in Ambari UI (so you can configure port, memory etc)
- Sets up initial flow.xml.gz that sets up Ambari reporting task to send Ambari metrics
- Includes metrics widgets from [here](https://cwiki.apache.org/confluence/display/NIFI/Ambari+Metrics)

Author: [Ali Bajwa](https://www.linkedin.com/in/aliabajwa)

#### Setup

- Download HDP 2.3 sandbox VM image (Sandbox_HDP_2.3_VMware.ova) from [Hortonworks website](http://hortonworks.com/products/hortonworks-sandbox/)
- Import Sandbox_HDP_2.3_VMware.ova into VMWare and set the VM memory size to 8GB
- Now start the VM
- After it boots up, find the IP address of the VM and add an entry into your machines hosts file e.g.
```
192.168.191.241 sandbox.hortonworks.com sandbox    
```
- Connect to the VM via SSH (password hadoop) and start Ambari server
```
ssh root@sandbox.hortonworks.com
/root/start_ambari.sh
```

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

  - By default:
    - Port is set to 9090
    - Max JVM memory size is 512mb
    - Run schedule for Nifi's Ambari reporting task is 1 min
  
- On successful deployment you will see the NiFi service as part of Ambari stack and will be able to start/stop the service from here:

- You can see the parameters you configured under 'Configs' tab
![Image](../master/screenshots/screenshot-nifi-stack-config.png?raw=true)

- One benefit to wrapping the component in Ambari service is that you can now monitor/manage this service remotely via REST API
```
export SERVICE=NIFI
export PASSWORD=admin
export AMBARI_HOST=localhost
export CLUSTER=Sandbox

#get service status
curl -u admin:$PASSWORD -i -H 'X-Requested-By: ambari' -X GET http://$AMBARI_HOST:8080/api/v1/clusters/$CLUSTER/services/$SERVICE

#start service
curl -u admin:$PASSWORD -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start $SERVICE via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$AMBARI_HOST:8080/api/v1/clusters/$CLUSTER/services/$SERVICE

#stop service
curl -u admin:$PASSWORD -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Stop $SERVICE via REST"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}' http://$AMBARI_HOST:8080/api/v1/clusters/$CLUSTER/services/$SERVICE
```

- ...and also install via Blueprint. See example [here](https://github.com/abajwa-hw/ambari-workshops/blob/master/blueprints-demo-security.md) on how to deploy custom services via Blueprints

#### Open NiFi webapp

- The NiFi webUI login page should come up at the below link: 
http://sandbox.hortonworks.com:9090/nifi

- You can also open it from within Ambari via [iFrame view](https://github.com/abajwa-hw/iframe-view)
![Image](../master/screenshots/screenshot-nifi-view.png?raw=true)

- Create simple flow to read Tweets into HDFS
  - Drag processor (next to nifi icon in upper left) to canvas and search for GetTwitter
  - Right click on it > Configure > Properties > Add your Twitter key/secrets
  - Drag processor to canvas and search for PutHDFS
  - Right click on it > Configure
    - Under Settings:
      - check failure and success
    - Under Properties:
      - Hadoop Configuration Resources: `/etc/hadoop/conf/core-site.xml`
      - Directory: `/tmp`
  - Connect the two by dragging the circle in the center of GetTwitter box to PutHDFS box and click Add
  - Click the Start button (green triangle near top of screen)

- You should also see Nifi metrics in Ambari  
![Image](../master/screenshots/screenshot-nifi-stack.png?raw=true)


#### Remove service

- To remove the Nifi service: 
  - Stop the service via Ambari
  - Unregister the service
  
    ```
export SERVICE=NIFI
export PASSWORD=admin
export AMBARI_HOST=localhost
export CLUSTER=Sandbox    
curl -u admin:$PASSWORD -i -H 'X-Requested-By: ambari' -X DELETE http://$AMBARI_HOST:8080/api/v1/clusters/$CLUSTER/services/$SERVICE

#if above errors out, run below first to fully stop the service
#curl -u admin:$PASSWORD -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Stop $SERVICE via REST"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}' http://$AMBARI_HOST:8080/api/v1/clusters/$CLUSTER/services/$SERVICE
    ```
   - Remove artifacts
    ```
    rm -rf /opt/nifi*
    rm /tmp/nifi-0.3.0-SNAPSHOT-bin.zip
    ```   