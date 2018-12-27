``diana-cli``
=============

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |codecov|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io Image:
  https://cloud.docker.com/repository/docker/derekmerck/diana2

::

    Usage: diana-cli [OPTIONS] COMMAND [ARGS]...

      Run diana packages using a command-line interface.

    Options:
      --verbose / --no-verbose
      --version                 Show the version and exit.
      -s, --services TEXT       Diana service desc as yaml format string
      -S, --services_path PATH  Diana service desc as a yaml format file or
                                directory of files
      --help                    Show this message and exit.

    Commands:
      check         Check status of service ENDPOINTS
      dcm2im        Convert a DICOM format file or directory INPATH into pixels...
      index         Inventory dicom dir PATH with INDEX service for retrieval
      indexed-pull  Pull study by accession number from a PATH with INDEX service...
      mock          Create a mock site from DESC and send data to DEST service.
      ofind         Find studies matching yaml/json QUERY in SOURCE Orthanc...
      watch         Watch sources for events to handle based on ROUTES Usage: $...

Requires platform service endpoint description in yaml format.

.. code:: yaml

    ---
    orthanc:
      ctype: Orthanc
      port: 8042
      name: my_orthanc

    redis:
      ctype: Redis

check
-----

::

    Usage: diana-cli check [OPTIONS] [ENDPOINTS]...

      Check status of service ENDPOINTS

    Options:
      --help  Show this message and exit.

index
-----

::

    Usage: diana-cli index [OPTIONS] PATH INDEX

      Inventory dicom dir PATH with INDEX service for retrieval

    Options:
      --orthanc_db  Use subpath width/depth=2
      --help        Show this message and exit.

indexed-pull
------------

::

    Usage: diana-cli indexed-pull [OPTIONS] ACCESSION_NUMBER PATH INDEX DEST

      Pull study by accession number from a PATH with INDEX service and send to
      DEST

    Options:
      --orthanc_db  Use subpath width/depth=2
      --help        Show this message and exit.

dcm2im
------

::

    Usage: diana-cli dcm2im [OPTIONS] INPATH [OUTPATH]

      Convert a DICOM format file or directory INPATH into pixels and save in a
      standard image format (png, jpg) to OUTPATH.

    Options:
      --help  Show this message and exit.

mock
----

::

    Usage: diana-cli mock [OPTIONS] [DESC]

      Create a mock site from DESC and send data to DEST service.

    Options:
      --dest TEXT  Destination service
      --help       Show this message and exit.

ofind
-----

::

    Usage: diana-cli ofind [OPTIONS] QUERY SOURCE

      Find studies matching yaml/json QUERY in SOURCE Orthanc service {optionally
      with proxy DOMAIN}

    Options:
      --domain TEXT   Domain for proxied query
      -r, --retrieve
      --help          Show this message and exit.

watch
-----

::

    Usage: diana-cli watch [OPTIONS]

      Watch sources for events to handle based on ROUTES

      Usage:

      $ diana-cli watch -r move path:/incoming queue $ diana-cli watch -r
      move_anon queue archive $ diana-cli watch -r index_series archive splunk

      $ diana-cli watch -r classify_ba archive splunk

      $ diana-cli watch -r pindex_studies pacs splunk

      $ echo routes.yml --- - source: queue   dest: archive   handler: mv_anon
      level: instances - source: archive   dest: splunk   handler: index   level:
      studies ... $ diana-cli watch -R routes.yml

      Route Handlers (Triggers):

      - say - mv or mv_anon - upload - index

    Options:
      -r, --route TEXT...
      -R, --routes_path PATH
      --help                  Show this message and exit.

License
-------

MIT

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |codecov| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
