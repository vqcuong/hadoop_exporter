#!/usr/bin/env python
# -*- coding: utf-8 -*-

from logging import Logger
import os
import re
import traceback
from typing import Any, List, Dict, Optional
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.metrics_core import Metric
from hadoop_exporter import utils

EXPORTER_METRICS_DIR = os.environ.get('EXPORTER_METRICS_DIR', 'metrics')


class MetricCollector(object):
    '''
    MetricCollector is a super class of all kinds of MetricsColleter classes. It setup common params like cluster, url, component and service.
    '''
    NON_METRIC_NAMES = ["name", "modelerType", "Name", "ObjectName"]

    def __init__(self, cluster, url, component, service, logger: Logger = None):
        '''
        @param cluster: Cluster name, registered in the config file or ran in the command-line.
        @param url: All metrics are scraped in the url, corresponding to each component. 
                    e.g. "hdfs" metrics can be scraped in http://ip:50070/jmx.
                         "resourcemanager" metrics can be scraped in http://ip:8088/jmx.
        @param component: Component name. e.g. "hdfs", "resourcemanager", "mapred", "hive", "hbase".
        @param service: Service name. e.g. "namenode", "resourcemanager", "hiveserver2".
        '''

        self._logger = logger or utils.get_logger()
        self._cluster = cluster
        self._component = component
        self._service = service
        self._url = url.rstrip('/')
        self._prefix = 'hadoop_{0}_{1}'.format(component, service)

        cfg = utils.read_yaml_file(os.path.join(EXPORTER_METRICS_DIR, component, f"{service}.yaml"))
        common_cfg = utils.read_yaml_file(os.path.join(EXPORTER_METRICS_DIR, 'common.yaml'))

        self._rules = cfg["rules"]
        self._rules.update(common_cfg["rules"])
        self._lower_name = cfg.get("lowercaseOutputName", True)
        self._lower_label = cfg.get("lowercaseOutputLabelNames", True)
        self._common_labels = {"names": [], "values": []}
        self._first_get_common_labels = True
        self._metrics = {}


    def collect(self):
        try:
            beans = utils.get_metrics(self._url)
        except:
            self._logger.info(
                "Can't scrape metrics from url: {0}".format(self._url))
            pass
        else:
            if self._first_get_common_labels:
                self._get_common_labels(beans)
            self._convert_metrics(beans)
            for group_metrics in self._metrics.values():
                for metric in group_metrics.values():
                    yield metric


    def _get_common_labels(self, beans: List[Dict]):
        self._first_get_common_labels = False
        self._common_labels["names"].append("cluster")
        self._common_labels["values"].append(self._cluster)

        bean = self._find_bean(beans, "Hadoop:service=.*,name=(JvmMetrics)$")
        if bean:
            self._common_labels["names"].append("hostname")
            self._common_labels["values"].append(bean["tag.Hostname"])


    def _convert_metrics(self, beans: List[Dict]):
        for group_pattern in self._rules:
            self._metrics[group_pattern] = {}
        # loop for each group metric
        for bean in beans:
            for group_pattern in self._rules:
                if not re.compile(group_pattern).match(bean["name"]):
                    continue
                for metric_name, value in bean.items():
                    if metric_name in self.NON_METRIC_NAMES:
                        continue
                    # loop for each metric defined in each group
                    for metric_def in self._rules[group_pattern]:
                        if metric_def["type"] != "GAUSE":
                            self._logger.warning(
                                "Metric type {} not supported currently".format(metric_def["type"]))
                            continue
                        if re.compile(metric_def["pattern"]).match(metric_name):
                            pattern = re.compile("{}<>{}".format(
                                group_pattern.rstrip("$"), metric_def["pattern"].lstrip("^")))
                            concat_str = "{}<>{}".format(bean["name"], metric_name)
                            sub_name = pattern.sub(metric_def["name"].replace("$", "\\"), concat_str)
                            sub_label_names = [label for label in metric_def["labels"].keys()]
                            metric_identifier = '_'.join([sub_name] + sorted(sub_label_names)).lower()
                            if metric_identifier not in self._metrics[group_pattern]:
                                name = "_".join([self._prefix, sub_name])
                                if self._lower_name: name = name.lower()
                                label_names = self._common_labels["names"] + sub_label_names
                                if self._lower_label: label_names = [label.lower() for label in label_names]
                                docs = name if "help" not in metric_def \
                                    else pattern.sub(metric_def["help"].replace("$", "\\"), concat_str)
                                try:
                                    metric = GaugeMetricFamily(name, docs, labels=label_names)
                                except:
                                    self._logger.warning("Error while create new metric")
                                    traceback.print_exc()
                                else:
                                    self._metrics[group_pattern][metric_identifier] = metric

                            if metric_identifier in self._metrics[group_pattern]:
                                label_values = self._common_labels["values"] + [pattern.sub(label.replace("$", "\\"), concat_str)
                                    for label in metric_def["labels"].values()]
                                resolved_value = self._resolve_value(value, metric_def.get("mapping", None))
                                self._metrics[group_pattern][metric_identifier].add_metric(label_values, resolved_value)
                            break


    def _resolve_value(self, value: Any, mapping: Optional[str]) -> Any:
        if mapping:
            import importlib
            mod_name, func_name = mapping.rsplit('.',1)
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name)
            return func(value)
        return value


    def _find_bean(self, beans: List[Dict], group_pattern: str) -> Optional[Dict]:
        regex = re.compile(group_pattern)
        for bean in beans:
            if regex.match(bean["name"]):
                return bean
        return None
