#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hadoop_exporter.exporter import Exporter
from hadoop_exporter import utils


def main():
    exporter = Exporter()
    exporter.register_consul()
    exporter.register_prometheus()

if __name__ == '__main__':
    main()
