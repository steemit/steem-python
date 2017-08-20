FROM phusion/baseimage:0.9.19

# Standard stuff
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Stuff for building steem-python
ARG BUILD_ROOT=/buildroot
ARG BUILD_OUTPUT=${BUILD_ROOT}/build

# Now we install the essentials
RUN \
    apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        libffi-dev \
        libssl-dev \
        make \
        python3 \
        python3-dev \
        python3-pip \
        libxml2-dev \
        libxslt-dev \
        runit \
	wget \
        pandoc

# This updates the distro-provided pip and gives us pip3.5 binary
RUN python3.5 -m pip install --upgrade pip

# We use pipenv to setup stuff
RUN python3.5 -m pip install -U pipenv

WORKDIR ${BUILD_ROOT}

# Copy just enough to build python dependencies in pipenv
COPY ./Pipfile ${BUILD_ROOT}/Pipfile

# Install the dependencies found in the lockfile here
RUN cd ${BUILD_ROOT} && \
    python3.5 -m pipenv install --three --dev && \
    python3.5 -m pipenv lock --three --hashes && \
    pipenv run pip3.5 freeze --local --all >requirements.txt && \
    python3.5 -m pip -r requirements.txt

# Copy rest of the code into place
COPY ./*  ${BUILD_ROOT}/

# Do build+install
RUN make clean install-global

# Cleanup stuff
USER root

RUN rm -rf \
        /root/.cache \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /var/cache/* \
        /usr/include \
        /usr/local/include

