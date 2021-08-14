#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Union
from hadoop_exporter import utils
from hadoop_exporter.common import MetricCollector


class YARNNodeManagerMetricCollector(MetricCollector):
    COMPONENT = "yarn"
    SERVICE = "nodemanager"

    def __init__(self, cluster, urls: Union[str, List[str]]):
        logger = utils.get_logger(

            __name__, log_file=f"{self.COMPONENT}_{self.SERVICE}.log")
        MetricCollector.__init__(
            self, cluster, urls, self.COMPONENT, self.SERVICE, logger)

    def _get_common_labels(self, beans: List[Dict], url: str):
        super()._get_common_labels(beans, url)

        bean = self._find_bean(beans, "Hadoop:service=NodeManager,name=JvmMetrics")
        if bean:
            self._common_labels[url]["names"].append("host")
            self._common_labels[url]["values"].append(bean["tag.Hostname"])
