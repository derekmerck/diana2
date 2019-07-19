diana-cli
=========

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |Coverage Status| |Doc Status|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io
| Image: https://cloud.docker.com/repository/docker/derekmerck/diana2

``diana-cli`` provides a command-line interface to DIANA endpoints.

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
     check     Check endpoint status
     collect   Collect and handle studies
     collect2  Collect and handle studies v2
     dcm2im    Convert DICOM to image
     dcm2json  Convert DICOM header to json
     epdo      Call endpoint method
     findex    Create a persistent DICOM file index
     fiup      Upload indexed DICOM files
     guid      Generate a GUID
     mfind     Find item in Montage by query
     mock      Generate mock DICOM traffic
     ofind     Find item in Orthanc by query
     verify    Verify DIANA source code against public gist signature
     watch     Watch sources and route events

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

   Usage: diana-cli collect [OPTIONS] PROJECT DATA_PATH SOURCE DOMAIN [DEST]

     Create a PROJECT key at DATA_PATH, then pull data from SOURCE and send to
     DEST.

   Options:
     -a, --anonymize
     -b, --subpath_depth INTEGER  Number of sub-directories to use  (if dest is
                                  directory)
     --help                       Show this message and exit.

collect2
--------

::

   Usage: diana-cli collect2 [OPTIONS] SOURCE DEST [WORKLIST]...

     Pull data from SOURCE and save/send to DEST.  If source is a service, a
     QUERY must be provided, and a time range can be optionally provided for
     retrospective data collection (otherwise defaulting to real-time
     monitoring).

   Options:
     -W, --worklist_source TEXT      file or service
     -q, --query TEXT                worklist query (json)
     -Q, --query_source TEXT         json file with worklist query
     -t, --time_range TEXT           run query over time range
     -a, --anonymize
     -i, --image_dest TEXT           Specify image dest
     -m, --meta_dest TEXT            Specify meta dest
     -r, --report_dest TEXT          Specify report dest
     -I, --image_format [d|i|c|o|m]  Convert images to format
     -M, --meta_format [c|s|v]
     -R, --report_format [i|n|l|i|n|e]
     -b, --subfolders <INTEGER INTEGER>...
     -B, --split_meta INTEGER
     -p, --pool INTEGER              Pool size for multi-threading
     -P, --pause FLOAT               Pause between threads
     -d, --dryrun                    Process worklist and create keys without PACS
                                     pulls
     --help                          Show this message and exit.

     $ diana-cli -S /services.yml collect pacs path:/data 9999999 ...

dcm2im
------

::

   Usage: diana-cli dcm2im [OPTIONS] INPATH [OUTPATH]

     Convert a DICOM file or directory of files at INPATH into pixels and save
     result in a standard image format (png, jpg) at OUTPATH.

   Options:
     --help  Show this message and exit.

dcm2json
--------

::

   Usage: diana-cli dcm2json [OPTIONS] INPATH [OUTPATH]

     Convert a DICOM file or directory of files at INPATH into dictionaries and
     save result in json format at OUTPATH.

   Options:
     --help  Show this message and exit.

epdo
----

::

   Usage: diana-cli epdo [OPTIONS] ENDPOINT METHOD

     Call ENDPOINT METHOD with *args and **kwargs. Use "path:" for a DcmDir ep
     and "ipath:" for an ImageDir epp.

       $ diana-cli epdo orthanc info
       $ diana-cli epdo ipath:/data/images exists my_file_name
       $ diana-cli epdo montage find --map_arg '{"q": "<accession_number>"}'

   Options:
     -g, --args TEXT
     -m, --map_arg TEXT
     -k, --kwargs TEXT
     -a, --anonymize              (ImageDir only)
     -b, --subpath_depth INTEGER  Number of sub-directories to use (*Dir Only)
     --help                       Show this message and exit.

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

     Collect files in a study by COLLECTION (accession number or "ALL") using a
     PATH REGISTRY, and send to DEST.

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

mfind
-----

::

   Usage: diana-cli mfind [OPTIONS] SOURCE

     Find studies matching QUERY string in SOURCE Montage service.

   Options:
     -a, --accession_number TEXT     Link multiple a/ns with ' | ', requires PHI
                                     privileges on Montage
     -A, --accessions_path TEXT      Path to text file with study ids
     --start_date TEXT               Starting date query bound
     --end_date TEXT                 Ending date query bound
     --today
     -q, --query TEXT                Query string
     -e, --extraction [radcat|lungrads]
                                     Perform a data extraction on each report
     -j, --json                      Output as json
     --help                          Show this message and exit.

ofind
-----

::

   Usage: diana-cli ofind [OPTIONS] SOURCE

     Find studies matching yaml/json QUERY in SOURCE Orthanc or ProxiedDicom
     service. The optional proxy DOMAIN issues a remote-find to a manually
     proxied DICOM endpoint.

   Options:
     -a, --accession_number TEXT
     --today
     -q, --query TEXT             Query in json format
     -l, --level TEXT
     -d, --domain TEXT            Domain for proxied query when using Orthanc
                                  source
     -r, --retrieve
     --help                       Show this message and exit.

verify
------

::

   Usage: diana-cli verify [OPTIONS]

     Verify DIANA source code against public gist signature.

     This function is a convenience only; if the package has been altered, it
     could easily be altered to return correct hashes or check the wrong gist.
     The paranoid should refer to <https://github.com/derekmerck/gistsig> for
     instructions on finding performing an external manual audit.

   Options:
     --help  Show this message and exit.

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

diana-plus
==========

``diana-plus`` provides additional commands for pixel-processing.

::

   Usage: diana-plus [OPTIONS] COMMAND [ARGS]...

     Run diana and diana-plus packages using a command-line interface.

   Options:
     --verbose / --no-verbose
     --version                 Show the version and exit.
     --help                    Show this message and exit.

   Commands:
     check     Check endpoint status
     classify  Classify DICOM files
     collect   Collect and handle studies
     collect2  Collect and handle studies v2
     dcm2im    Convert DICOM to image
     dcm2json  Convert DICOM header to json
     epdo      Call endpoint method
     findex    Create a persistent DICOM file index
     fiup      Upload indexed DICOM files
     guid      Generate a GUID
     mfind     Find item in Montage by query
     mock      Generate mock DICOM traffic
     ofind     Find item in Orthanc by query
     ssde      Estimate patient size from localizer
     verify    Verify DIANA source code against public gist signature
     watch     Watch sources and route events

ssde
----

::

classify
--------

::

License
-------

MIT

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |Coverage Status| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
.. |Doc Status| image:: https://readthedocs.org/projects/diana/badge/?version=master
   :target: https://diana.readthedocs.io/en/master/?badge=master
