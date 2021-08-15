#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Union, Dict
from hadoop_exporter import utils
from hadoop_exporter.common import MetricCollector


class HiveServer2MetricCollector(MetricCollector):
    COMPONENT = "hive"
    SERVICE = "hiveserver2"

    def __init__(self, cluster, urls: Union[str, List[str]]):
        logger = utils.get_logger(__name__, log_file=f"{self.COMPONENT}_{self.SERVICE}.log")
        MetricCollector.__init__(
            self, cluster, urls, self.COMPONENT, self.SERVICE, logger)

    def _get_common_labels(self, beans: List[Dict], url: str):
        super()._get_common_labels(beans, url)

        bean = self._find_bean(beans, "org.apache.logging.log4j2:type=AsyncContext@(\w{8})$")
        if bean:
            import re
            matched = re.compile(".*hostName=(.+),.*").match(bean["ConfigProperties"])
            print(matched)
            self._common_labels[url]["names"].append("host")
            self._common_labels[url]["values"].append(matched.groups()[0])
