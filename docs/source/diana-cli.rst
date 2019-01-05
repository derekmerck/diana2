``diana-cli``
=============

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |codecov| |Doc Status|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io
| Image: https://cloud.docker.com/repository/docker/derekmerck/diana2

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
      check    Check endpoint status
      collect  Collect and handle studies
      dcm2im   Convert DICOM to image
      findex   Create a persistent DICOM file index
      fiup     Upload indexed DICOM files
      guid     Generate a GUID
      mock     Generate mock DICOM traffic
      ofind    Find in Orthanc node
      watch    Watch sources and route events

      SERVICES is a required platform endpoint description in yaml format.

      ---
      orthanc:
        ctype: Orthanc
        port: 8042
        host: my_orthanc
      redis:
        ctype: Redis
      ...

check
-----

::

    Usage: diana-cli check [OPTIONS] [ENDPOINTS]...

      Survey status of service ENDPOINTS

    Options:
      --help  Show this message and exit.

collect
-------

::

    Usage: diana-cli collect [OPTIONS] PROJECT DATA_PATH SOURCE DEST

      Create a PROJECT key at DATA_PATH, then pull data from SOURCE and send to
      DEST.

    Options:
      --help  Show this message and exit.

dcm2im
------

::

    Usage: diana-cli dcm2im [OPTIONS] INPATH [OUTPATH]

      Convert a DICOM file or directory of files at INPATH into pixels and save
      result in a standard image format (png, jpg) at OUTPATH.

    Options:
      --help  Show this message and exit.

findex
------

::

    Usage: diana-cli findex [OPTIONS] PATH REGISTRY

      Inventory collections of files by accession number with a PATH REGISTRY for
      retrieval

    Options:
      -o, --orthanc_db         Use subpath width/depth=2
      -r, --regex TEXT         Glob regular expression
      -p, --pool_size INTEGER  Worker threads
      --help                   Show this message and exit.

fiup
----

::

    Usage: diana-cli fiup [OPTIONS] COLLECTION PATH REGISTRY DEST

      Collect files in a study by COLLECTION (accession number) using a PATH
      REGISTRY, and send to DEST.

    Options:
      -p, --pool_size INTEGER  Worker threads
      --help                   Show this message and exit.

guid
----

::

    Usage: diana-cli guid [OPTIONS] NAME [[%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d
                          %H:%M:%S]] [GENDER]

      Generate a globally unique sham ID from NAME, DOB, and GENDER.

    Options:
      --age INTEGER                   Substitute age and ref date for DOB
      --reference_date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                      Reference date for AGE
      --help                          Show this message and exit.

      $ python3 diana-cli.py guid "MERCK^DEREK^L" --age 30
      Generating GUID
      ------------------------
      WARNING:GUIDMint:Creating non-reproducible GUID using current date
      {'BirthDate': datetime.date(1988, 11, 20),
       'ID': 'VXNQHHN523ZQNJFIY3TXJM4YXABTL6SL',
       'Name': ['VANWASSENHOVE', 'XAVIER', 'N'],
       'TimeOffset': datetime.timedelta(-47, 82822)}

mock
----

::

    Usage: diana-cli mock [OPTIONS] [DESC]

      Generate synthetic studies on a schedule according to a site description
      DESC.  Studies are optionally forwarded to an endpoint DEST.

    Options:
      --dest TEXT  Destination DICOM service
      --help       Show this message and exit.

      DESC must be a mock-site description in yaml format.

      ---
      - name: Example Hospital
        services:
        - name: Main CT
          modality: CT
          devices: 3
          studies_per_hour: 15
        - name: Main MR
          modality: MR
          devices: 2
          studies_per_hour: 4
      ...

ofind
-----

::

    Usage: diana-cli ofind [OPTIONS] QUERY SOURCE

      Find studies matching yaml/json QUERY in SOURCE Orthanc service.  The
      optional proxy DOMAIN issues a remote-find to a proxied DICOM endpoint.

    Options:
      --domain TEXT   Domain for proxied query
      -r, --retrieve
      --help          Show this message and exit.

watch
-----

::

    Usage: diana-cli watch [OPTIONS]

      Watch sources for events to handle based on ROUTES

    Options:
      -r, --route TEXT...
      -R, --routes_path PATH
      --help                  Show this message and exit.

      Examples:

      $ diana-cli watch -r upload_files path:/incoming queue
      $ diana-cli watch -r anon_and_send_instances queue archive
      $ diana-cli watch -r index_studies pacs splunk
      $ diana-cli watch -r classify_ba archive splunk
      $ diana-cli watch -R routes.yml

      Multiple ROUTES file format:

      ---
      - handler: upload_files
        source: "path:/incoming"
        dest: queue
      - handler: anon_and_send_instances
        source: queue
        dest: archive
      - handler: index_studies
        source: pacs
        dest: splunk
      ...

      Provided route handlers:

      - say_dlvl
      - send_dlvl or anon_and_send_dlvl
      - upload_files
      - index_dlvl

License
-------

MIT

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |codecov| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
.. |Doc Status| image:: https://readthedocs.org/projects/diana/badge/?version=latest
   :target: https://diana.readthedocs.io/en/latest/?badge=latest
