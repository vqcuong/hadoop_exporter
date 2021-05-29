#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Union
from hadoop_exporter import utils
from hadoop_exporter.common import MetricCollector


class YARNResourceManagerMetricCollector(MetricCollector):
    COMPONENT = "yarn"
    SERVICE = "resourcemanager"

    def __init__(self, cluster, urls: Union[str, List[str]]):
        logger = utils.get_logger(
            __name__, log_file=f"{self.COMPONENT}_{self.SERVICE}.log")
        MetricCollector.__init__(
            self, cluster, urls, self.COMPONENT, self.SERVICE, logger)
