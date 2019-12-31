#using neurodebian runtime as parent image
FROM neurodebian:xenial-non-free
MAINTAINER Unmaintained

RUN apt-get update

# Install Ubuntu dependencies and utilities
RUN apt-get install -y \
      build-essential \
      cmake \
      git \
      graphviz \
      graphviz-dev \
      gsl-bin \
      libcanberra-gtk-module \
      libexpat1-dev \
      libgiftiio-dev \
      libglib2.0-dev \
      libglu1-mesa \
      libglu1-mesa-dev \
      libjpeg-progs \
      libgl1-mesa-dri \
      libglw1-mesa \
      libxml2 \
      libxml2-dev \
      libxext-dev \
      libxft2 \
      libxft-dev \
      libxi-dev \
      libxmu-headers \
      libxmu-dev \
      libxpm-dev \
      libxslt1-dev \
      m4 \
      make \
      mesa-common-dev \
      mesa-utils \
      netpbm \
      pkg-config \
      tcsh \
      unzip \
      vim \
      xvfb \
      xauth \
      zlib1g-dev

# Install 16.04 dependencies
RUN apt-get install -y \
      dh-autoreconf \
      libgsl-dev \
      libmotif-dev \
      libtool \
      libx11-dev \
      libxext-dev \
      python3-pip \
      x11proto-xext-dev \
      x11proto-print-dev \
      xutils-dev

# Compiles libxp- this is necessary for some newer versions of Ubuntu
# where the is no Debian package available.
RUN git clone git://anongit.freedesktop.org/xorg/lib/libXp /tmp/libXp && \
    cd /tmp/libXp && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install && \
    cd - && \
    rm -rf /tmp/libXp

# Installing and setting up c3d
RUN mkdir -p /opt/c3d && \
    curl -sSL "http://downloads.sourceforge.net/project/c3d/c3d/1.0.0/c3d-1.0.0-Linux-x86_64.tar.gz" \
    | tar -xzC /opt/c3d --strip-components 1
ENV C3DPATH /opt/c3d/
ENV PATH $C3DPATH/bin:$PATH

# install AFNI
RUN libs_path=/usr/lib/x86_64-linux-gnu && \
    if [ -f $libs_path/libgsl.so.19 ]; then \
        ln $libs_path/libgsl.so.19 $libs_path/libgsl.so.0; \
    fi && \
    mkdir -p /opt/afni && \
    curl -sO http://s3.amazonaws.com/fcp-indi/resources/linux_openmp_64.zip && \
    unzip -nj linux_openmp_64.zip -d /opt/afni && \
    rm -rf linux_openmp_64.zip

# set up AFNI
ENV PATH=/opt/afni:$PATH

# install FSL
RUN apt-get install -y --no-install-recommends \
      fsl-core \
      fsl-atlases \
      fsl-mni152-templates

# setup FSL environment
ENV FSLDIR=/usr/share/fsl/5.0 \
    FSLOUTPUTTYPE=NIFTI_GZ \
    FSLMULTIFILEQUIT=TRUE \
    POSSUMDIR=/usr/share/fsl/5.0 \
    LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH \
    FSLTCLSH=/usr/bin/tclsh \
    FSLWISH=/usr/bin/wish \
    PATH=/usr/lib/fsl/5.0:$PATH

# download OASIS templates for niworkflows-ants skullstripping
RUN mkdir /ants_template && \
    curl -sL https://s3-eu-west-1.amazonaws.com/pfigshare-u-files/3133832/Oasis.zip -o /tmp/Oasis.zip && \
    unzip /tmp/Oasis.zip -d /tmp &&\
    mv /tmp/MICCAI2012-Multi-Atlas-Challenge-Data /ants_template/oasis && \
    rm -rf /tmp/Oasis.zip /tmp/MICCAI2012-Multi-Atlas-Challenge-Data

# install ANTs
ENV PATH=/usr/lib/ants:$PATH
RUN apt-get install -y ants

# install miniconda
RUN curl -sO https://repo.continuum.io/miniconda/Miniconda-3.8.3-Linux-x86_64.sh && \
    bash Miniconda-3.8.3-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda-3.8.3-Linux-x86_64.sh

# update path to include conda
ENV PATH=/usr/local/miniconda/bin:$PATH

# install blas dependency first
RUN conda install -y \
        blas

# install conda dependencies
RUN conda install -y  \
        cython==0.26 \
        matplotlib=2.0.2 \
        networkx==1.11 \
        nose==1.3.7 \
        numpy==1.13.0 \
        pandas==0.23.4 \
        scipy==1.2.1 \
        traits==4.6.0 \
        wxpython==3.0.0.0 \
        pip

# install python dependencies
#COPY requirements.txt /opt/requirements.txt
#RUN pip install -r /opt/requirements.txt
RUN pip install xvfbwrapper

COPY PEER_eye_2mm_r30.nii.gz /cpac_resources/PEER_eye_2mm_r30.nii.gz

RUN pwd
RUN pip3 install git+https://github.com/cbin-cnl/minimal_preprocessing.git

ENTRYPOINT ["/usr/local/bin/preprocess_peer"]

RUN apt-get clean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
