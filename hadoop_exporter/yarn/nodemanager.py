#!/usr/bin/env python
# -*- coding: utf-8 -*-

from hadoop_exporter import utils
from hadoop_exporter.common import MetricCollector


class YARNNodeManagerMetricCollector(MetricCollector):
    COMPONENT = "yarn"
    SERVICE = "nodemanager"

    def __init__(self, cluster, url):
        logger = utils.get_logger(

            __name__, log_file=f"{self.COMPONENT}_{self.SERVICE}.log")
        MetricCollector.__init__(
            self, cluster, url, self.COMPONENT, self.SERVICE, logger)
