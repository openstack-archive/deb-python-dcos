# This image is used to run the CCM commands

FROM ubuntu:16.04
MAINTAINER support@mesosphere.com

RUN apt-get update && apt-get install -y \
  httpie \
  jq

ENV LC_CTYPE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US
ENV LC_ALL ""

ADD ccm /ccm
WORKDIR /ccm

ENV PATH="/ccm:${PATH}"
