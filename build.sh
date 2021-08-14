#!/bin/bash

base_repo=${1}
version=${2:-"latest"}
docker build -t ${base_repo}hadoop_exporter:${version} .
