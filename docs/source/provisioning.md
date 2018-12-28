Provisioning
============

Setup the Swarm
---------------

.. code:: bash

::

    $ docker swarm init --advertise-addr <ip_addr>
    $ ssh host2
    > docker swarm join ... etc

Tag unique nodes for the scheduler
----------------------------------

| The ``storage`` node will be assigned the database backend and DICOM
  mass archive accessors.
| Any ``bridge`` nodes will be assigned DICOM ingress, routing, and
  bridging services (b/c typically modalities authorize endpoint access
  by specific IP address.)

.. code:: bash

::

    $ docker node update --label-add storage=true host1   # mounts mass storage
    $ docker node update --label-add bridge=true host2    # registered IP address for DICOM receipt
