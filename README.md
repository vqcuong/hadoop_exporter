# Hadoop Exporter for Prometheus

## How it works
- Consume metrics from JMX http, convert and export hadoop metrics via HTTP for Prometheus consumption.
- Underlyring, I used regex template to parse and map config name as well as label before exporting it via promethues http server. You can see my templates in folder [metrics](./metrics)

## How to run
```
python service.py
```

Help on flags of hadoop_exporter:
```
$ python service.py -h
usage: service.py [-h] [-cfg CONFIG] [-c CLUSTER_NAME] [-nn NAMENODE_JMX]
                  [-dn DATANODE_JMX] [-jn JOURNALNODE_JMX]
                  [-rm RESOURCEMANAGER_JMX] [-nm NODEMANAGER_JMX]
                  [-mrjh MAPRED_JOBHISTORY_JMX] [-hm HMASTER_JMX]
                  [-hr HREGION_JMX] [-hs2 HIVESERVER2_JMX]
                  [-hllap HIVELLAP_JMX] [-ad AUTO_DISCOVERY]
                  [-adw DISCOVERY_WHITELIST] [-addr ADDRESS] [-p PORT]
                  [--path PATH] [--period PERIOD]
hadoop node exporter args, including url, metrics_path, address, port and
cluster.

optional arguments:
  -h, --help            show this help message and exit
  -cfg CONFIG           Exporter config file (defautl: None)
  -c CLUSTER_NAME       Hadoop cluster labels. (default "hadoop_cluster")
  -nn NAMENODE_JMX      Hadoop hdfs metrics URL. (example
                        "http://localhost:9870/jmx")
  -dn DATANODE_JMX      Hadoop datanode metrics URL. (example
                        "http://localhost:9864/jmx")
  -jn JOURNALNODE_JMX   Hadoop journalnode metrics URL. (example
                        "http://localhost:8480/jmx")
  -rm RESOURCEMANAGER_JMX
                        Hadoop resourcemanager metrics URL. (example
                        "http://localhost:8088/jmx")
  -nm NODEMANAGER_JMX   Hadoop nodemanager metrics URL. (example
                        "http://localhost:8042/jmx")
  -mrjh MAPRED_JOBHISTORY_JMX
                        Hadoop mapred history metrics URL. (example
                        "http://localhost:19888/jmx")
  -hm HMASTER_JMX       HBase masterserver metrics URL. (example
                        "http://localhost:16010/jmx")
  -hr HREGION_JMX       HBase regionserver metrics URL. (example
                        "http://localhost:16030/jmx")
  -hs2 HIVESERVER2_JMX  hive metrics URL. (example
                        "http://localhost:10002/jmx")
  -hllap HIVELLAP_JMX   Hadoop llap metrics URL. (example
                        "http://localhost:15002/jmx")
  -ad AUTO_DISCOVERY    Enable auto discovery if set true else false. (example
                        "--auto true") (default: false)
  -adw DISCOVERY_WHITELIST
                        Enable auto discovery if set true else false. (example
                        "--auto true") (default: false)
  -addr ADDRESS         Polling server on this address. (default "127.0.0.1")
  -p PORT               Listen to this port. (default "9123")
  --path PATH           Path under which to expose metrics. (default
                        "/metrics")
  --period PERIOD       Period (seconds) to consume jmx service. (default: 30)
```

You can use config file (yaml format) to replace commandline args. Example of config.yaml:
```
# exporter server config
server:
  address: 127.0.0.1 # address to run exporter
  port: 9123 # port to listen

# list of jmx service to scape metrics
jmx:
  - cluster: hadoop_cluster
    component: hdfs
    service: namenode
    url: http://localhost:9870/jmx

  - cluster: hadoop_cluster
    component: yarn
    service: resourcemanager
    url: http://localhost:8088/jmx

```

Tested on Apache Hadoop 2.7.3, 3.3.0

## Docker deployment

Run container:
```
docker run -d \
  --name hadoop-exporter \
  vqcuong96/hadoop_exporter \
  -nn http://localhost:9870/jmx \
  -rm http://localhost:8088/jmx
```

You can also mount config to docker container:
```
docker run -d \
  --name hadoop_exporter \
  --mount type=bind,source=/path/to/config.yaml,target=/tmp/config.yaml \
  vqcuong96/hadoop_exporter \
  -cfg /tmp/config.yaml
```

To build your own images, run:
```
./docker/build.sh [your_repo] [your_version_tag]
```

Example:
```
./docker/build.sh mydockerhub/ latest 
#your image like that: mydockerhub/hadoop_exporter:latest
```
