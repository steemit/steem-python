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
	wget

# This updates the distro-provided pip and gives us pip3.5 binary
RUN python3.5 -m pip install --upgrade pip

# Here we install pipenv for both default python3 and python3.5
RUN pip3 install pipenv
RUN pip3.5 install pipenv

WORKDIR ${BUILD_ROOT}

# Copy just enough to build python dependencies in pipenv
COPY ./Pipfile ${BUILD_ROOT}/Pipfile

# Install python dependencies - we do this here to avoid invalidating docker cache when rest of codebase changes
RUN cd ${BUILD_ROOT} && \
    python3.5 -m pipenv install --three --dev

# Copy rest of the code into place
COPY ./Makefile  ${BUILD_ROOT}/Makefile
COPY ./steem     ${BUILD_ROOT}/steem
COPY ./steembase ${BUILD_ROOT}/steembase
COPY ./tests     ${BUILD_ROOT}/tests
COPY ./scripts   ${BUILD_ROOT}/scripts
COPY ./docs      ${BUILD_ROOT}/docs

# Run the test suite
RUN PYTHONPATH=${BUILD_ROOT} python3.5 -m pipenv run py.test tests

# Build wheel and place it in the right place
COPY ./README.md ./README.md
RUN python3.5 -m pipenv run python3.5 scripts/doc_rst_convert.py
RUN python3.5 -m pipenv run pip3.5 wheel -w ${BUILD_OUTPUT}  

# Create a tarball we can grab after build
RUN cd ${BUILD_ROOT} && \
    tar cvf ${BUILD_ROOT}/dist.tar ${BUILD_OUTPUT}/* && \
    echo "Build distribution is in container at ${BUILD_ROOT}/dist.tar"

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

