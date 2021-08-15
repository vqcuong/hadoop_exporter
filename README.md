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
                  [--path PATH] [--period PERIOD] [--log-level LOG_LEVEL]

hadoop node exporter args, including url, metrics_path, address, port and
cluster.

optional arguments:
  -h, --help            show this help message and exit
  -cfg CONFIG           Exporter config file (defautl: /exporter/config.yaml)
  -c CLUSTER_NAME       Hadoop cluster labels. (default "hadoop_cluster")
  -nn NAMENODE_JMX      List of HDFS namenode JMX url. (example
                        "http://localhost:9870/jmx")
  -dn DATANODE_JMX      List of HDFS datanode JMX url. (example
                        "http://localhost:9864/jmx")
  -jn JOURNALNODE_JMX   List of HDFS journalnode JMX url. (example
                        "http://localhost:8480/jmx")
  -rm RESOURCEMANAGER_JMX
                        List of YARN resourcemanager JMX url. (example
                        "http://localhost:8088/jmx")
  -nm NODEMANAGER_JMX   List of YARN nodemanager JMX url. (example
                        "http://localhost:8042/jmx")
  -mrjh MAPRED_JOBHISTORY_JMX
                        List of Mapreduce jobhistory JMX url. (example
                        "http://localhost:19888/jmx")
  -hm HMASTER_JMX       List of HBase master JMX url. (example
                        "http://localhost:16010/jmx")
  -hr HREGION_JMX       List of HBase regionserver JMX url. (example
                        "http://localhost:16030/jmx")
  -hs2 HIVESERVER2_JMX  List of HiveServer2 JMX url. (example
                        "http://localhost:10002/jmx")
  -hllap HIVELLAP_JMX   List of Hive LLAP JMX url. (example
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
  --period PERIOD       Period (seconds) to consume jmx service. (default: 10)
  --log-level LOG_LEVEL Log level, include: all, debug, info, warn, error (default: info)
```

You can use config file (yaml format) to replace commandline args. Example of config.yaml:
```
# exporter server config
server:
  address: 127.0.0.1 # address to run exporter
  port: 9123 # port to listen

# list of jmx service to scape metrics
jmx:
  - cluster: hadoop_prod
    services:
      namenode:
        - http://nn1:9870/jmx
      datanode:
        - http://dn1:9864/jmx
        - http://dn2:9864/jmx
        - http://dn3:9864/jmx
      resourcemanager:
        - http://rm1:8088/jmx
      nodemanager:
        - http://nm1:8042/jmx
        - http://nm2:8042/jmx
        - http://nm3:8042/jmx
      hiveserver2:
        - http://hs2:10002/jmx
      hmaster:
        - http://hmaster1:16010/jmx
        - http://hmaster2:16010/jmx
        - http://hmaster3:16010/jmx
      hregionserver:
        - http://hregion1:16030/jmx
        - http://hregion2:16030/jmx
        - http://hregion3:16030/jmx
  - cluster: hadoop_dev
    services:
      namenode:
        - http://dev:9870/jmx
      datanode:
        - http://dev:9864/jmx
      resourcemanager:
        - http://dev:8088/jmx
      nodemanager:
        - http://dev:8042/jmx
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
