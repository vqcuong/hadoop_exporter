#!/bin/bash

basedir=$(dirname "$0")

base_repo=${1}
version=${2:-"latest"}
docker build -f ${basedir}/Dockerfile -t ${base_repo}hadoop_exporter:${version} ${basedir}/..
