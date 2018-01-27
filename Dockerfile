FROM phusion/baseimage:0.9.19

# Standard stuff
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Stuff for building steem-python
ARG BUILD_ROOT=/build

# Now we install the essentials
RUN \
    apt-get update && \
    apt-get install -y python3-pip libssl-dev build-essential

# This updates the distro-provided pip
RUN pip3 install --upgrade pip

COPY . ${BUILD_ROOT}

WORKDIR ${BUILD_ROOT}

# run tests
RUN make test
