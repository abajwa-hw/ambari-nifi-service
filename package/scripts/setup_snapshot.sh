#!/bin/bash
set -e 
#e.g. /root/incubator-zeppelin
export INSTALL_DIR=$1

#e.g. sandbox.hortonworks.com
export HIVE_HOST=$2

#e.g. sandbox.hortonworks.com
export HIVE_METASTORE_HOST=$3

#e.g. 9083
export HIVE_METASTORE_PORT=$4

#e.g. FIRSTLAUNCH
export MODE=$5

#e.g. hdfs:///tmp/.zeppelin/zeppelin-spark-0.5.0-SNAPSHOT.jar
export SPARK_JAR=$6

export ZEPPELIN_HOST=$7

export ZEPPELIN_PORT=$8

export SETUP_VIEW=$9
SETUP_VIEW=${SETUP_VIEW,,}

echo "SETUP_VIEW is $SETUP_VIEW"

echo "Setting up zeppelin at $INSTALL_DIR"
cd $INSTALL_DIR

#Stop daemon if started
set +e
bin/zeppelin-daemon.sh status
STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "Stopping zeppelin daemon..."
	bin/zeppelin-daemon.sh stop
else
	echo "Zeppelin was not running."	
fi
set -e

if [ "$MODE" = "FIRSTLAUNCH" ]; then

	echo "Copying zeppelin-spark jar to HDFS"
	set +e 
	hadoop fs -rm $SPARK_JAR
	set -e 
	hadoop fs -put $INSTALL_DIR/interpreter/spark/zeppelin-spark-*.jar $SPARK_JAR

        rm -rf notebook/*

	#clean old notebooks
	if [ -d "notebook/2AHFKRNDZ" ]; then
		rm -rf notebook/2AHFKRNDZ
	fi	

	if [ -d "notebook/2AK7D7JNE" ]; then
		rm -rf notebook/2AK7D7JNE
	fi	


	if [ -d "notebook/2A94M5J1Z" ]; then
		rm -rf notebook/2A94M5J1Z
	fi

    if [[ $SETUP_VIEW == "true" ]]
    then
		echo "Importing notebooks"
		cd notebook
		wget https://www.dropbox.com/s/5eqztenz9ncm4jc/notebooks-150829.zip?dl=0 -O notebooks.zip
		unzip notebooks.zip
		cd ..
	fi
	
	echo "<configuration>" > conf/hive-site.xml
	echo "<property>" >> conf/hive-site.xml
	echo "   <name>hive.metastore.uris</name>" >> conf/hive-site.xml
	echo "   <value>thrift://$HIVE_METASTORE_HOST:$HIVE_METASTORE_PORT</value>" >> conf/hive-site.xml
	echo "</property>" >> conf/hive-site.xml		
	echo "</configuration>" >> conf/hive-site.xml		

	#setup view
	echo "Compiling Zeppelin view..."
	cd
	if [ -d iframe-view ] 
	then
		rm -rf iframe-view
	fi	
	if [ -d zeppelin-view ] 
	then
		rm -rf zeppelin-view
	fi	

    if [[ $SETUP_VIEW == "true" ]]
    then
		git clone https://github.com/abajwa-hw/iframe-view.git
		sed -i "s/iFrame View/Zeppelin/g" iframe-view/src/main/resources/view.xml	
		sed -i "s/IFRAME_VIEW/ZEPPELIN/g" iframe-view/src/main/resources/view.xml	
		sed -i "s/sandbox.hortonworks.com:6080/$ZEPPELIN_HOST:$ZEPPELIN_PORT/g" iframe-view/src/main/resources/index.html	
		sed -i "s/iframe-view/zeppelin-view/g" iframe-view/pom.xml	
		sed -i "s/Ambari iFrame View/Zeppelin View/g" iframe-view/pom.xml	
		mv iframe-view zeppelin-view
		cd zeppelin-view
		mvn clean package		
	fi	

	cd $INSTALL_DIR	
	
	#Start daemon to create the interpreter.json
	echo "Starting zeppelin to generate interpreter"
	bin/zeppelin-daemon.sh start	
	exit 0
	
else
	if [ ! -f conf/interpreter.json ]
	then
		echo 'Did not find interpreter so skipping rest of setup'
		exit 0
	fi	
fi



#archive old interpreter
if [ -f conf/interpreter.json ] 
then
	mv conf/interpreter.json conf/interpreter_$(date +%d-%m-%Y).json
#else
#    echo 'Did not find interpreter so exiting setup'
#	exit 0	
fi	



#Start daemon to re-create the interpreter.json
echo "Starting zeppelin..."
bin/zeppelin-daemon.sh start
while [ ! -f conf/interpreter.json ]
do
  sleep 2
  echo "Waiting for interpreter.json to be created...."
done

echo "Updating interpreter settings..."
#update interpreter.json with settings that can't be added via zeppelin_env.sh
HDP_VER=`hdp-select status hadoop-client | sed 's/hadoop-client - \(.*\)/\1/'`
export VER_STRING="-Dhdp.version=$HDP_VER"
echo "updating interpreter.json..."
sed -i "s/\"master\": \"yarn-client\",/\"master\": \"yarn-client\",\n\t\"spark.driver.extraJavaOptions\": \"$VER_STRING\",/g" conf/interpreter.json
sed -i "s/\"master\": \"yarn-client\",/\"master\": \"yarn-client\",\n\t\"spark.yarn.am.extraJavaOptions\": \"$VER_STRING\",/g" conf/interpreter.json
sed -i "s#\"hive.hiveserver2.url\": \"jdbc:hive2://localhost:10000\",#\"hive.hiveserver2.url\": \"jdbc:hive2://$HIVE_HOST:10000\",#g" conf/interpreter.json
#sed -i "s/\"spark.executor.memory\": \"512m\",/\"spark.executor.memory\": \"$EXECUTOR_MEM\",/g" conf/interpreter.json


echo "restarting daemon...."
bin/zeppelin-daemon.sh stop
sleep 10

echo "Setup complete"
