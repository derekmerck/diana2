DIANA Docker Image
==================

| Derek Merck
| derek.merck@ufl.edu
| University of Florida and Shands Hospital
| Gainesville, FL

|Build Status| |Coverage Status| |Doc Status|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io
| Image: https://cloud.docker.com/repository/docker/derekmerck/diana2

Build multi-architecture Docker images for embedded systems.

Use It
------

These images are manifested per modern Docker.io guidelines so that an
appropriately architected image can be will automatically selected for a
given tag depending on the pulling architecture.

.. code:: bash

   $ docker run derekmerck/diana2      # (latest-amd64, latest-arm32v7, latest-arm64v8)
   $ docker run derekmerck/diana2-plus # (latest-amd64, latest-arm32v7)

Images for specific architectures images can be directly pulled from the
same namespace using the format ``derekmerck/diana2:${TAG}-${ARCH}``,
where ``$ARCH`` is one of ``amd64``, ``arm32v7``, or ``arm64v8``.
Explicit architecture specification is sometimes helpful when an
indirect build service shadows the production architecture.

Build It
--------

These images are based on the cross-platform
``resin/${ARCH}-debian:buster`` image. `Resin.io <http://resin.io>`__
base images include the `QEMU <https://www.qemu.org>`__ cross-compiler
to facilitate building Docker images for low-power single-board
computers while using more powerful Intel-architecture compute servers.

This supports builds for ``amd64``, ``armhf``/``arm32v7``, and
``aarch64``/``arm64v8`` architectures. Most low-power single board
computers such as the `Raspberry Pi <https://www.raspberrypi.org>`__ and
`Beagleboard <http://beagleboard.org>`__ are ``armhf``/``arm32v7``
devices. The `Pine64 <https://www.pine64.org>`__ and `NVIDIA
Jetson <https://developer.nvidia.com/embedded/buy/jetson-tx2>`__ are
``aarch64``/``arm64v8`` devices. Desktop computers/vms, `UP
boards <http://www.up-board.org/upcore/>`__, and the `Intel
NUC <https://www.intel.com/content/www/us/en/products/boards-kits/nuc.html>`__
are ``amd64`` devices.

``docker-compose.yml`` contains build recipes for each architecture for
a simple ``diana`` image with all requirements pre-installed.

To build all images:

1. Register the Docker QEMU cross-compilers
2. Get
   `docker-manifest <https://github.com/derekmerck/docker-manifest>`__
   from Github
3. Put Docker into “experimental mode” for manifest creation
4. Call ``docker-compose`` to build the ``diana2-base`` images
5. Call ``docker-manifest.py`` with an appropriate domain to retag and
   push the base images
6. Call ``docker-compose`` to build the ``diana2`` images
7. Call ``docker-manifest.py`` with an appropriate domain to retag and
   push the completed images

.. code:: bash

   $ docker run --rm --privileged multiarch/qemu-user-static:register --reset
   $ pip install git+https://github.com/derekmerck/docker-manifest
   $ mkdir -p $HOME/.docker && echo '{"experimental":"enabled"}' > "$HOME/.docker/config.json"
   $ git clone git+https://github.com/derekmerck/diana2
   $ cd diana2/platform/images/diana-docker
   $ docker-compose build diana2-base-amd64 diana2-base-arm32v7 diana2-base-arm64v8
   $ docker-manifest -s diana2-base $DOCKER_USERNAME
   $ docker-compose build diana2-amd64 diana2-arm32v7 diana2-arm64v8
   $ docker-manifest -s diana2 $DOCKER_USERNAME 

Because the base image rarely changes, but the latest Diana build is
still fluid, the `Travis <http://travis-ci.org>`__ automation pipeline
for git-push-triggered image creation only automates only steps 7 and 8.

.. code:: bash

   $ docker run derekmerck/diana2:2.1.x python3 -c "import diana; print(diana.__version__)"
   2.1.x

Build a DIANA-Plus Docker Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DIANA-Plus includes scientfic and machine learning packages for advanced
image processing on medical image data. It is currently only available
for ``amd64`` and ``arm32v7`` because tensorflow is hard to compile for
``arm64v8``. For ``amd64``, DIANA-Plus uses the ``tf-nightly`` package
(currently 1.13) and for ``arm32v7`` we compile our own wheel (currently
1.12, see `TF on arm32 note <./TF_on_arm32v7.md>`__)

The DIANA-Plus Docker image is much heavier at 700MB, compared to 300MB
for the vanilla image.

::

   $ cp ${WHEEL_DIR}/tensorflowXX-py37-arm23.whl .
   $ docker-compose build diana2-plus-base-amd64 diana2-plus-base-arm32v7
   $ docker-manifest -s diana-plus-base derekmerck
   $ docker-compose build diana2-plus-amd64 diana2-plus-arm32v7
   $ docker-manifest -s diana-plus derekmerck

::

   $ docker run derekmerck/diana2-plus:latest-arm32v7 python3 -c "import tensorflow; print(tensorflow.__version__)" 
   1.12.0

DIANA on ARM
~~~~~~~~~~~~

If you need access to an ARM device for development,
`Packet.net <https://packet.net>`__ rents bare-metal 96-core 128GB
``aarch64`` `Cavium
ThunderX <https://www.cavium.com/product-thunderx-arm-processors.html>`__
servers for $0.50/hour. Packet’s affiliated `Works On
Arm <https://www.worksonarm.com>`__ program provided compute time for
developing and testing these cross-platform images.

An ``arm64v8`` image can be built natively and pushed from Packet, using
a brief tenancy on a bare-metal Cavium ThunderX ARMv8 server.

.. code:: bash

   $ apt update && apt upgrade
   $ curl -fsSL get.docker.com -o get-docker.sh
   $ sh get-docker.sh 
   $ docker run hello-world
   $ apt install git python-pip
   $ pip install docker-compose
   $ git clone http://github.com/derekmerck/diana2 
   ... continue as above

Although `Resin uses Packet ARM servers to compile arm32
images <https://resin.io/blog/docker-builds-on-arm-servers-youre-not-crazy-your-builds-really-are-5x-faster/>`__,
the available ThunderX does not implement the arm32 instruction set, so
it `cannot compile natively for the Raspberry
Pi <https://gitlab.com/gitlab-org/omnibus-gitlab/issues/2544>`__.

Now pull the image without specifying the architecture tag. You can
confirm that the appropriate image has been pulled by starting a
container with the command ``arch``.

.. code:: bash

   $ docker run derekmerck/diana2 arch
   aarch64

You can also confirm the image architecture without running a container
by inspecting the value of ``.Config.Labels.architecture``. (This is a
creator-defined label that is *different* than the normal
``.Architecture`` key – which appears to *always* report as ``amd64``.)

.. code:: bash

   $ docker inspect derekmerck/diana2 --format "{{ .Config.Labels.architecture }}"
   arm64v8

License
-------

MIT

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |Coverage Status| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
.. |Doc Status| image:: https://readthedocs.org/projects/diana/badge/?version=master
   :target: https://diana.readthedocs.io/en/master/?badge=master
