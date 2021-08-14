import os
from re import split
import time
import traceback
from typing import Callable, Dict, List, Optional, Union
from prometheus_client.core import REGISTRY
from prometheus_client import start_http_server
import yaml
from hadoop_exporter import utils
from hadoop_exporter.common import MetricCollector
from hadoop_exporter import (
    HDFSNameNodeMetricCollector,
    HDFSDataNodeMetricCollector,
    HDFSJournalNodeMetricCollector,
    YARNResourceManagerMetricCollector,
    YARNNodeManagerMetricCollector,
    HiveServer2MetricCollector
    # MapredJobHistoryMetricCollector, \
    # HBaseMasterMetricCollector, \
    # HBaseRegionServerMetricCollector, \
    # HiveServer2MetricCollector, \
    # HiveLlapDaemonMetricCollector
)

logger = utils.get_logger(__name__)

EXPORTER_CLUSTER_NAME_DEFAULT = 'hadoop_cluster'
EXPORTER_ADDRESS_DEFAULT = '0.0.0.0'
EXPORTER_PORT_DEFAULT = 9123
EXPORTER_PATH_DEFAULT = '/metrics'
EXPORTER_PERIOD_DEFAULT=30
EXPORTER_CONFIG_DEFAULT='/exporter/config.yaml'
EXPORTER_LOG_LEVEL_DEFAULT='info'


class ExporterEnv:
    EXPORTER_CONFIG = os.environ.get('EXPORTER_CONFIG', EXPORTER_CONFIG_DEFAULT)
    EXPORTER_CLUSTER_NAME = os.environ.get(
        'EXPORTER_CLUSTER_NAME', EXPORTER_CLUSTER_NAME_DEFAULT)
    EXPORTER_NAMENODE_JMX = os.environ.get('EXPORTER_NAMENODE_JMX', None)
    EXPORTER_DATANODE_JMX = os.environ.get('EXPORTER_DATANODE_JMX', None)
    EXPORTER_JOURNALNODE_JMX = os.environ.get('EXPORTER_JOURNALNODE_JMX', None)
    EXPORTER_RESOURCEMANAGER_JMX = os.environ.get(
        'EXPORTER_RESOURCEMANAGER_JMX', None)
    EXPORTER_NODEMANAGER_JMX = os.environ.get('EXPORTER_NODEMANAGER_JMX', None)
    EXPORTER_MAPRED_JOBHISTORY_JMX = os.environ.get(
        'EXPORTER_MAPRED_JOBHISTORY_JMX', None)
    EXPORTER_HMASTER_JMX = os.environ.get('EXPORTER_HMASTER_JMX', None)
    EXPORTER_HREGION_JMX = os.environ.get('EXPORTER_HREGION_JMX', None)
    EXPORTER_HIVESERVER2_JMX = os.environ.get('EXPORTER_HIVESERVER2_JMX', None)
    EXPORTER_HIVELLAP_JMX = os.environ.get('EXPORTER_HIVELLAP_JMX', None)
    EXPORTER_AUTO_DISCOVERY = os.environ.get(
        'EXPORTER_AUTO_DISCOVERY', 'false')
    EXPORTER_DISCOVERY_WHITELIST = os.environ.get(
        'EXPORTER_DISCOVERY_WHITELIST', None)
    EXPORTER_ADDRESS = os.environ.get(
        'EXPORTER_ADDRESS', EXPORTER_ADDRESS_DEFAULT)
    EXPORTER_PORT = os.environ.get('EXPORTER_PORT', EXPORTER_PORT_DEFAULT)
    EXPORTER_PATH = os.environ.get('EXPORTER_PATH', EXPORTER_PATH_DEFAULT)
    EXPORTER_PERIOD = os.environ.get('EXPORTER_PERIOD', EXPORTER_PERIOD_DEFAULT)
    EXPORTER_LOG_LEVEL = os.environ.get('EXPORTER_LOG_LEVEL', EXPORTER_LOG_LEVEL_DEFAULT)


class Service:
    def __init__(self, cluster: str, urls: List[str], collector: Callable = MetricCollector, name: Optional[str] = None) -> None:
        self.collector = collector
        self.urls = urls
        self.cluster = cluster
        self.flag = True
        self.name = name

    def register(self):
        if self.flag:
            logger.info("register new {} listen from {}".format(
                self.collector.__name__, self.urls))
            REGISTRY.register(self.collector(
                cluster=self.cluster, urls=self.urls))
            self.flag = not self.flag

    def __str__(self) -> str:
        return "(cluster: {}, url: {}, collector: {}{})".format(
            self.cluster, self.urls, self.collector.__name__, f', name: {self.name}' if self.name else '')


class Exporter:
    COLLECTOR_MAPPING = {
        'hdfs': {
            'namenode': HDFSNameNodeMetricCollector,
            'datanode': HDFSDataNodeMetricCollector,
            'journalnode': HDFSJournalNodeMetricCollector,
        },
        'yarn': {
            'resourcemanager': YARNResourceManagerMetricCollector,
            'nodemanager': YARNNodeManagerMetricCollector,
        },
        'hive': {
            'hiveserver2': HiveServer2MetricCollector,
            # 'llapdaemon': HiveLlapDaemonMetricCollector,
        },
        # 'hbase': {
        #     'master': HBaseMasterMetricCollector,
        #     'regionserver': HBaseRegionServerMetricCollector
        # }
    }

    def __init__(self) -> None:
        args = utils.parse_args()
        self.log_level = (args.log_level or ExporterEnv.EXPORTER_LOG_LEVEL).upper()
        self.config = args.config or ExporterEnv.EXPORTER_CONFIG
        self.auto_discovery = False
        self.discovery_whitelist = []
        if os.path.exists(self.config):
            logger.info("Use provided config: {}".format(self.config))
            try:
                with open(self.config, 'r') as f:
                    cfg = yaml.safe_load(f)
            except:
                logger.error("Something wrong when load config file")
                traceback.print_exc()
            else:
                server = cfg.get('server', {})
                self.address = server.get('address', EXPORTER_ADDRESS_DEFAULT)
                self.port = int(server.get('port', EXPORTER_PORT_DEFAULT))
                self.path = server.get('path', ExporterEnv.EXPORTER_PATH)
                self.period = int(server.get('period', ExporterEnv.EXPORTER_PERIOD))
                self.sevices: List[Service] = []

                jmx = cfg.get('jmx', [])
                for js in jmx:
                    try:
                        services = self._build_service_from_config(js)
                        if services:
                            self.sevices.extend(services)
                    except:
                        logger.warning(f'Error when parse jmx_service: {js}')
                        traceback.print_exc()
        else:
            logger.info("Config file: {} doesn't existed. Ignore".format(self.config))
            self.address = args.address or ExporterEnv.EXPORTER_ADDRESS
            self.port = int(args.port or ExporterEnv.EXPORTER_PORT)
            self.path = args.path or ExporterEnv.EXPORTER_PATH
            self.period = int(args.period or ExporterEnv.EXPORTER_PERIOD)
            self.sevices: List[Service] = []

            if (args.auto_discovery or ExporterEnv.EXPORTER_AUTO_DISCOVERY).lower() == 'true':
                self.auto_discovery = True

            self.discovery_whitelist = args.discovery_whitelist or ExporterEnv.EXPORTER_DISCOVERY_WHITELIST

            cluster_name = args.cluster_name or ExporterEnv.EXPORTER_CLUSTER_NAME
            namenode_jmx = args.namenode_jmx or ExporterEnv.EXPORTER_NAMENODE_JMX
            datanode_jmx = args.datanode_jmx or ExporterEnv.EXPORTER_DATANODE_JMX
            journalnode_jmx = args.journalnode_jmx or ExporterEnv.EXPORTER_JOURNALNODE_JMX
            resourcemanager_jmx = args.resourcemanager_jmx or ExporterEnv.EXPORTER_RESOURCEMANAGER_JMX
            nodemanager_jmx = args.nodemanager_jmx or ExporterEnv.EXPORTER_NODEMANAGER_JMX
            mapred_jobhistory_jmx = args.mapred_jobhistory_jmx or ExporterEnv.EXPORTER_MAPRED_JOBHISTORY_JMX
            hmaster_jmx = args.hmaster_jmx or ExporterEnv.EXPORTER_HMASTER_JMX
            hregion_jmx = args.hregion_jmx or ExporterEnv.EXPORTER_HREGION_JMX
            hiveserver2_jmx = args.hiveserver2_jmx or ExporterEnv.EXPORTER_HIVESERVER2_JMX
            hivellap_jmx = args.hivellap_jmx or ExporterEnv.EXPORTER_HIVELLAP_JMX

            if self.auto_discovery:
                namenode_jmx = namenode_jmx or 'http://localhost:9870/jmx'
                datanode_jmx = datanode_jmx or 'http://localhost:9864/jmx'
                journalnode_jmx = journalnode_jmx or 'http://localhost:8480/jmx'
                resourcemanager_jmx = resourcemanager_jmx or 'http://localhost:8088/jmx'
                nodemanager_jmx = nodemanager_jmx or 'http://localhost:8042/jmx'
                mapred_jobhistory_jmx = mapred_jobhistory_jmx or 'http://localhost:19888/jmx'
                hmaster_jmx = hmaster_jmx or 'http://localhost:16010/jmx'
                hregion_jmx = hregion_jmx or 'http://localhost:16030/jmx'
                hiveserver2_jmx = hiveserver2_jmx or 'http://localhost:10002/jmx'
                hivellap_jmx = hivellap_jmx or 'http://localhost:15002/jmx'

            if self.auto_discovery:
                logger.info("Enable service auto discovery mode")

            if namenode_jmx and self._check_whitelist('nn'):
                self.sevices.append(self._build_service(
                    cluster_name, namenode_jmx, HDFSNameNodeMetricCollector))
            if datanode_jmx and self._check_whitelist('dn'):
                self.sevices.append(self._build_service(
                    cluster_name, datanode_jmx, HDFSDataNodeMetricCollector))
            if journalnode_jmx and self._check_whitelist('jn'):
                self.sevices.append(self._build_service(
                    cluster_name, journalnode_jmx, HDFSJournalNodeMetricCollector))
            if resourcemanager_jmx and self._check_whitelist('rm'):
                self.sevices.append(self._build_service(
                    cluster_name, resourcemanager_jmx, YARNResourceManagerMetricCollector))
            if nodemanager_jmx and self._check_whitelist('nm'):
                self.sevices.append(self._build_service(
                    cluster_name, nodemanager_jmx, YARNNodeManagerMetricCollector))
            # if mapred_jobhistory_jmx and self._check_whitelist('mrjh'):
            #     self.sevices.append(self._build_service(
            #         cluster_name, mapred_jobhistory_jmx, MapredJobHistoryMetricCollector))
            if hiveserver2_jmx and self._check_whitelist('hs2'):
                self.sevices.append(self._build_service(
                    cluster_name, hiveserver2_jmx, HiveServer2MetricCollector))
            # if hivellap_jmx and self._check_whitelist('hllap'):
            #     self.sevices.append(self._build_service(
            #         cluster_name, hivellap_jmx, HiveLlapDaemonMetricCollector))
            # if hmaster_jmx and self._check_whitelist('hm'):
            #     self.sevices.append(self._build_service(
            #         cluster_name, hmaster_jmx, HBaseMasterMetricCollector))
            # if hregion_jmx and self._check_whitelist('hr'):
            #     self.sevices.append(self._build_service(
            #         cluster_name, hregion_jmx, HBaseRegionServerMetricCollector))

    def _build_service_from_config(self, js: Dict) -> List[Service]:
        if "component" not in js or "services" not in js:
            logger.error("component and services field must provided")
            return None

        cluster=js.get("cluster", EXPORTER_CLUSTER_NAME_DEFAULT)
        component_name = js.get("component", None)
        services= []
        for service_name, urls in js["services"].items():
            collector = self.COLLECTOR_MAPPING.get(component_name, {}).get(service_name, None)
            if collector:
                service = Service(
                    cluster=cluster,
                    urls=urls,
                    collector=collector
                )
                services.append(service)
                logger.info("Added service: {}".format(service))
            else:
                logger.warning("Can't mapping collector with component/service: {}/{}".format(component_name, service_name))
        return services

    def _build_service(self, cluster_name: str, urls: Union[str, List[str]], collector: Callable) -> Service:
        service = Service(
            cluster=cluster_name,
            urls=urls,
            collector=collector,
        )
        logger.info("Added service: {}".format(service))
        return service

    def _check_whitelist(self, service) -> bool:
        if self.discovery_whitelist is None:
            return True
        else:
            whilelist = self.discovery_whitelist.split(',')
            if service in whilelist:
                return True
            else:
                return False

    def register_consul(self):
        start_http_server(self.port, addr=self.address)
        logger.info(
            f"Exporter start listening on http://{self.address}:{self.port}")
        logger.info(f"Scraping metrics every {self.period}s ...")
        logger.info(f"Set log level = {self.log_level}")
        logger.setLevel(self.log_level)

    def register_prometheus(self):
        self.logging_threshold = 60 #seconds
        counter = self.logging_threshold
        try:
            while True:
                for service in self.sevices:
                    service.register()
                if counter >= self.logging_threshold:
                    logger.info(f"Continue scraping metrics every {self.period}s ...")
                    counter = 0
                counter += 1
                time.sleep(self.period)

        except KeyboardInterrupt:
            logger.info("Interrupted")
            exit(0)
        except:
            traceback.print_exc()
