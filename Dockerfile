FROM library/python:3.6

# Stuff for building steem-python
ARG BUILD_ROOT=/buildroot

# Now we install the essentials
RUN \
    apt-get update && \
    apt-get install -y \
        build-essential \
        checkinstall \
        libssl-dev \
        libxml2-dev \
        libxslt-dev \
        make \
        wget \
        pandoc && \
        apt-get clean

RUN pip3.6 install --upgrade pip

COPY . ${BUILD_ROOT}

WORKDIR ${BUILD_ROOT}

RUN python3.6 setup.py install
RUN piston -h
RUN steempy -h
RUN steemtail -h

RUN python3.6 setup.py develop
RUN pip3 install -e .[dev]
RUN python3.6 setup.py pytest
RUN python3.6 setup.py build



