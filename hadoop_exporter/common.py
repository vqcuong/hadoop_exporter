#!/usr/bin/env python
# -*- coding: utf-8 -*-

from logging import Logger
import os
import re
import traceback
from typing import Any, List, Dict, Optional, Union
from prometheus_client.core import GaugeMetricFamily
from hadoop_exporter import utils

EXPORTER_METRICS_DIR = os.environ.get('EXPORTER_METRICS_DIR', 'metrics')


class MetricCollector(object):
    '''
    MetricCollector is a super class of all kinds of MetricsColleter classes. It setup common params like cluster, url, component and service.
    '''
    NON_METRIC_NAMES = ["name", "modelerType", "Name", "ObjectName"]

    def __init__(self, cluster: str, urls: Union[str, List[str]], component: str, service: str, logger: Logger = None):
        '''
        @param cluster: Cluster name, registered in the config file or ran in the command-line.
        @param urls: List of JMX url of each unique serivce corresponding to each component 
                    e.g. hdfs namenode metrics can be scraped in list: [http://namenode1:9870/jmx. http://namenode2:9870/jmx]
        @param component: Component name. e.g. "hdfs", "resourcemanager"
        @param service: Service name. e.g. "namenode", "datanode", "resourcemanager", "nodemanager"
        '''

        self._logger = logger or utils.get_logger()
        self._cluster = cluster
        self._component = component
        self._service = service
        self._urls = list(map(lambda url: url.rstrip('/'), urls.split(",") if isinstance(urls, str) else urls))
        self._prefix = 'hadoop_{0}_{1}'.format(component, service)

        cfg = utils.read_yaml_file(os.path.join(EXPORTER_METRICS_DIR, component, f"{service}.yaml"))
        common_cfg = utils.read_yaml_file(os.path.join(EXPORTER_METRICS_DIR, 'common.yaml'))

        self._rules = cfg.get("rules", {}) if cfg is not None else {}
        if common_cfg is not None:
            self._rules.update(common_cfg.get("rules", {}))
        self._lower_name = cfg.get("lowercaseOutputName", True)
        self._lower_label = cfg.get("lowercaseOutputLabel", True)
        self._common_labels = {}
        self._first_get_common_labels = {}
        for url in self._urls:
            self._first_get_common_labels[url] = True
        self._metrics = {}


    def collect(self):
        for group_pattern in self._rules:
            self._metrics[group_pattern] = {}
        for url in self._urls:
            try:
                beans = utils.get_metrics(url)
            except:
                self._logger.info(
                    "Can't scrape metrics from url: {0}".format(url))
                pass
            else:
                if self._first_get_common_labels[url]:
                    self._common_labels[url] = {"names": [], "values": []} 
                    self._get_common_labels(beans, url)
            self._convert_metrics(beans, url)

        for group_metrics in self._metrics.values():
            for metric in group_metrics.values():
                yield metric


    def _get_common_labels(self, beans: List[Dict], url: str):
        self._first_get_common_labels[url] = False
        self._common_labels[url]["names"].append("cluster")
        self._common_labels[url]["values"].append(self._cluster)


    def _convert_metrics(self, beans: List[Dict], url: str):
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
                            sub_label_names = [label for label in metric_def["labels"].keys()] \
                                if "labels" in metric_def else []
                            metric_identifier = '_'.join([sub_name] + sorted(sub_label_names)).lower()
                            if metric_identifier not in self._metrics[group_pattern]:
                                name = "_".join([self._prefix, sub_name])
                                if self._lower_name: name = name.lower()
                                label_names = self._common_labels[url]["names"] + sub_label_names
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
                                sub_label_values = [pattern.sub(label.replace("$", "\\"), concat_str)
                                    for label in metric_def["labels"].values()] if "labels" in metric_def else []
                                label_values = self._common_labels[url]["values"] + sub_label_values
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
