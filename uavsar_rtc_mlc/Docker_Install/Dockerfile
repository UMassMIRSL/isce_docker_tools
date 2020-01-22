FROM ubuntu:18.04
LABEL MAINTAINER="Microwave Remote Sensing Laboratory at UMASS Amherst"

ENV WORKDIR=/opt/isce2-2.3.1
ENV PYTHONPATH=$WORKDIR/configuration
ENV SCONS_CONFIG_DIR=$WORKDIR
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y gfortran libmotif-dev libhdf5-dev libfftw3-dev libgdal-dev scons python3 cython3 python3-scipy python3-matplotlib python3-h5py python3-gdal python3-pip wget curl gdal-bin imagemagick git unzip vim && \
    rm /etc/ImageMagick-6/policy.xml && \
    pip3 install jinja2 requests boto3 lxml shapely pandas utm && \
    cd /opt && \
    wget --no-verbose https://github.com/isce-framework/isce2/archive/v2.3.1.tar.gz && \
    tar -xzf v2.3.1.tar.gz && \
    mkdir /work /output && \
    chmod 777 /work /output

COPY SConfigISCE $WORKDIR/SConfigISCE

RUN cd $WORKDIR && \
    scons install

ENV ISCE_ROOT=$WORKDIR/install
ENV ISCE_HOME=$ISCE_ROOT/isce
ENV PATH=$ISCE_HOME/bin:$ISCE_HOME/applications:$ISCE_HOME/share/stripmapStack:$PATH
ENV PYTHONPATH=$ISCE_ROOT:$ISCE_HOME/applications:$ISCE_HOME/component:/usr/local/etc/hyp3-lib/src
ENV HOME=/work

WORKDIR $HOME/uavsar_mlcproc/docker_new_runs
COPY share /opt/isce2-2.3.1/install/isce/share
COPY Image /opt/isce2-2.3.1/install/isce/components/isceobj/Image/
COPY Sensor /opt/isce2-2.3.1/install/isce/components/isceobj/Sensor/
ENTRYPOINT ["python3", "-u", "run_ctrl.py"]
