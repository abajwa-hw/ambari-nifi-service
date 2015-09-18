#### An Ambari Service for NiFi
Ambari service for easily installing and managing NiFi on HDP cluster and viewing metrics.

Features:

- By default, downloads a prebuilt version of 0.3.0, but also gives option to build Nifi from source instead
- Exposes nifi.properties, bootstrap.conf, logback.xml in Ambari UI (so you can configure port, memory, log dir etc)
- Sets up initial flow.xml.gz that sets up Ambari reporting task to send Ambari metrics
- Includes metrics widgets from [here](https://cwiki.apache.org/confluence/display/NIFI/Ambari+Metrics)

Authors: 
  - [Ali Bajwa](https://github.com/abajwa-hw): Nifi Install/start/stop via Ambari
  - [Bryan Bende](https://github.com/bbende): Ambari metrics integration
  
#### Setup

- Download HDP 2.3 sandbox VM image (Sandbox_HDP_2.3_VMware.ova) from [Hortonworks website](http://hortonworks.com/products/hortonworks-sandbox/)
- Import Sandbox_HDP_2.3_VMware.ova into VMWare and set the VM memory size to 8GB
- Now start the VM
- After it boots up, find the IP address of the VM and add an entry into your machines hosts file e.g.
```
192.168.191.241 sandbox.hortonworks.com sandbox    
```
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

- Create simple flow to read Tweets into HDFS and Solr. 
  - Pre-requisite 1: HDP sandbox comes LW HDP search. Follow the steps below to use it to start SolrCloud and create a collection
  ```
  su solr
  /opt/lucidworks-hdpsearch/solr/bin/solr start -c -z localhost:2181

  /opt/lucidworks-hdpsearch/solr/bin/solr create -c tweets \
     -d data_driven_schema_configs \
     -s 1 \
     -rf 1 
  ```  
  
    - If running on an Ambari installed HDP 2.3 cluster (instead of sandbox), run the below to install HDPsearch
  ```
  yum install -y lucidworks-hdpsearch
  sudo -u hdfs hadoop fs -mkdir /user/solr
  sudo -u hdfs hadoop fs -chown solr /user/solr
  ```    
  - Pre-requisite 2: Ensure the time on your sandbox is accurate or you will get errors using the GetTwitter processor. To fix the time, run the below:
  ```
  service ntpd stop
  ntpdate pool.ntp.org
  service ntpd start
  ```  
  - Now open Nifi webui and run the remaining steps there:    
  - Capture tweets from Twitter API
    - Drag processor (next to nifi icon in upper left) to canvas and search for GetTwitter and click Add to add to canvas.
    - Right click on it > Configure
      - Under Settings:
        - check failure and success 
      - Under Properties:
        - Add your Twitter key/secrets
        - change the 'Twitter Endpoint' to 'Filter Endpoint'
        - enter the search terms (e.g. hortonworks,hadoop) under 'Terms to Filter on'  
        
  - Write tweets to HDFS    
    - Drag processor to canvas and search for PutHDFS
    - Right click on it > Configure
      - Under Settings:
        - check failure and success
      - Under Properties:
        - Hadoop Configuration Resources: `/etc/hadoop/conf/core-site.xml`
        - Directory: `/tmp`
        
  - Connect the two processors:
    - By dragging the circle in the center of GetTwitter box to PutHDFS box and click Add to add to canvas.
    
  - Write tweets to Solr
    - Drag procesor to canvas and search for PutSolrContentStream
    - Right click on it > Configure
      - Under Settings:
        - check failure and success
      - Under Properties:
        - Solr Type: Cloud
        - Solr Location: sandbox.hortonworks.com:2181
        - Collection: labs  
      - Connect the two by dragging the circle in the center of GetTwitter box to PutSolrContentStream box and click Add  

  - If setup correctly, the top left hand of each processor on the canvas will show a red square (indicating the flow is stopped)
![Image](../master/screenshots/twitter-flow.png?raw=true)

  - Click the Start button (green triangle near top of screen) to start the flow
  - After few seconds you will see data flowing and 
    - tweets will appear under /tmp dir in HDFS. You can see this via Files view in Ambari:
    ![Image](../master/screenshots/Files-view.png?raw=true) 
    - tweets will appear in Solr: 
      - http://sandbox.hortonworks.com:8983/solr/tweets_shard1_replica1/select?q=*:*
      - http://sandbox.hortonworks.com:8983/solr/#/tweets_shard1_replica1/query
    ![Image](../master/screenshots/Solr-query.png?raw=true)  

  - Data provenance:
    - In Nifi home screen, click Provenance icon (5th icon from top right corner) to open Provenance page:
    ![Image](../master/screenshots/provenance-list-1.png?raw=true)
    - Click Show lineage icon (2nd icon from right) on any row
    ![Image](../master/screenshots/provenance-graph1.png?raw=true)    
    - Right click Send > View details > Content
    ![Image](../master/screenshots/provenance-event.png?raw=true)    
    - From here you can view the tweet itself by
      - Clicking Content > View > formatted
      ![Image](../master/screenshots/tweet.png?raw=true)
    - You can also replay the event by 
      - Replay > Submit      
    - Close the provenance window using x icon *on the inner window*
    - Notice the event was replayed
    ![Image](../master/screenshots/provenance-list-2.png?raw=true)
    - Re-open the the provenance window on the row you you had originally selected
    ![Image](../master/screenshots/provenance-graph2.png?raw=true)
    - Notice that by viewing the tweet, you changed the provenance graph of this event
    
- You should also see Nifi metrics in Ambari (assuming you started Ambari metrics earlier)
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