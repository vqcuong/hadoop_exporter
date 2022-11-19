#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket
import re
from typing import Dict, List, Optional
import requests
import logging
import yaml
import argparse

EXPORTER_LOGS_DIR = os.environ.get('EXPORTER_LOGS_DIR', '/tmp/exporter')


def get_logger(name, log_file="hadoop_exporter.log", level: str = "INFO") -> logging.Logger:
    '''
    define a common logger template to record log.
    @param name log module or object name.
    @return logger.
    '''

    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if not os.path.exists(EXPORTER_LOGS_DIR):
        os.makedirs(EXPORTER_LOGS_DIR)

    fh = logging.FileHandler(os.path.join(EXPORTER_LOGS_DIR, log_file))
    fh.setLevel(logging.INFO)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)

    fmt = logging.Formatter(
        fmt='%(asctime)s %(filename)s[line:%(lineno)d]-[%(levelname)s]: %(message)s')
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


logger = get_logger(__name__)


def get_metrics(url) -> List[Dict]:
    '''
    :param url: The jmx url, e.g. http://host1:9870/jmx, http://host1:8088/jmx, http://host2:19888/jmx...
    :return a dict of all metrics scraped in the jmx url.
    '''
    result = []
    try:
        s = requests.session()
        response = s.get(url, timeout=5)
    except Exception as e:
        logger.warning("error in func: get_metrics, error msg: %s" % e)
        result = []
    else:
        if response.status_code != requests.codes.ok:
            logger.warning("get {0} failed, response code is: {1}.".format(
                url, response.status_code))
            result = []
        rlt = response.json()
        logger.debug(rlt)
        if rlt and "beans" in rlt:
            result = rlt['beans']
        else:
            logger.warning("no metrics get in the {0}.".format(url))
            result = []
    finally:
        s.close()
    return result


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_hostname():
    '''
    get hostname via socket.
    @return a string of hostname
    '''
    try:
        host = socket.getfqdn()
    except Exception as e:
        logger.info("get hostname failed, error msg: {0}".format(e))
        return None
    else:
        return host


def read_yaml_file(file) -> Optional[Dict]:
    if os.path.exists(file):
        with open(file, 'r') as f:
            cfg = yaml.safe_load(f)
        return cfg
    return None

def parse_args():
    parser = argparse.ArgumentParser(
        description='hadoop node exporter args, including url, metrics_path, address, port and cluster.'
    )
    parser.add_argument(
        '-cfg',
        required=False,
        dest='config',
        help='Exporter config file (default: /exporter/config.yaml)',
        default=None
    )
    parser.add_argument(
        '-c',
        required=False,
        dest='cluster_name',
        help='Hadoop cluster labels. (default "hadoop_cluster")',
        default=None
    )
    parser.add_argument(
        '-nn',
        required=False,
        dest='namenode_jmx',
        help='List of HDFS namenode JMX url. (example "http://localhost:9870/jmx")',
        default=None
    )
    parser.add_argument(
        '-dn',
        required=False,
        dest='datanode_jmx',
        help='List of HDFS datanode JMX url. (example "http://localhost:9864/jmx")',
        default=None
    )
    parser.add_argument(
        '-jn',
        required=False,
        dest='journalnode_jmx',
        help='List of HDFS journalnode JMX url. (example "http://localhost:8480/jmx")',
        default=None
    )
    parser.add_argument(
        '-rm',
        required=False,
        dest='resourcemanager_jmx',
        help='List of YARN resourcemanager JMX url. (example "http://localhost:8088/jmx")',
        default=None
    )
    parser.add_argument(
        '-nm',
        required=False,
        dest='nodemanager_jmx',
        help='List of YARN nodemanager JMX url. (example "http://localhost:8042/jmx")',
        default=None
    )
    parser.add_argument(
        '-mrjh',
        required=False,
        dest='mapred_jobhistory_jmx',
        help='List of Mapreduce jobhistory JMX url. (example "http://localhost:19888/jmx")',
        default=None
    )
    parser.add_argument(
        '-hm',
        required=False,
        dest='hmaster_jmx',
        help='List of HBase master JMX url. (example "http://localhost:16010/jmx")',
        default=None
    )
    parser.add_argument(
        '-hr',
        required=False,
        dest='hregion_jmx',
        help='List of HBase regionserver JMX url. (example "http://localhost:16030/jmx")',
        default=None
    )
    parser.add_argument(
        '-hs2',
        required=False,
        dest='hiveserver2_jmx',
        help='List of HiveServer2 JMX url. (example "http://localhost:10002/jmx")',
        default=None
    )
    parser.add_argument(
        '-hllap',
        required=False,
        dest='hivellap_jmx',
        help='List of Hive LLAP JMX url. (example "http://localhost:15002/jmx")',
        default=None
    )
    parser.add_argument(
        '-ad',
        required=False,
        dest='auto_discovery',
        help='Enable auto discovery if set true else false. (example "--auto_discovery true") (default: false)',
        default=None
    )
    parser.add_argument(
        '-adw',
        required=False,
        dest='discovery_whitelist',
        help='List of shortnames of services (namenode: nn, datanode: dn, ...) that should be enable to auto discovery',
        default=None
    )
    parser.add_argument(
        '-addr',
        dest='address',
        required=False,
        help='Polling server on this address (hostname or ip). (default "0.0.0.0")',
        default=None
    )
    parser.add_argument(
        '-p',
        dest='port',
        required=False,
        type=int,
        help='Port to listen on. (default "9123")',
        default=None
    )
    parser.add_argument(
        '--path',
        dest='path',
        required=False,
        help='Path under which to expose metrics. (default "/metrics")',
        default=None
    )
    parser.add_argument(
        '--period',
        dest='period',
        required=False,
        type=int,
        help='Period (seconds) to consume jmx service. (default: 30)',
        default=None
    )
    parser.add_argument(
        '--log-level',
        required=False,
        dest='log_level',
        help='Log level, include: all, debug, info, warn, error (default: info)',
        default=None
    )
    return parser.parse_args()
