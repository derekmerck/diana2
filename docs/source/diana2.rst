DICOM Image Analysis and Archive
================================

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |Coverage Status| |Doc Status|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io
| Image: https://cloud.docker.com/repository/docker/derekmerck/diana2

Overview
--------

Hospital picture archive and communications systems (PACS) are not well
suited for “big data” analysis. It is difficult to identify and extract
datasets in bulk, and moreover, high resolution data is often not even
stored in the clinical systems.

**DIANA** is a `DICOM <http://www.dicomstandard.org/>`__ imaging
informatics platform that can be attached to the clinical systems with a
very small footprint, and then tuned to support a range of tasks from
high-resolution image archival to cohort discovery to radiation dose
monitoring. It provides DICOM services, image data indexing, REST
endpoints for scripting, and user access control through an amalgamation
of free and free and open source (FOSS) systems.

License
-------

MIT

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |Coverage Status| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
.. |Doc Status| image:: https://readthedocs.org/projects/diana/badge/?version=master
   :target: https://diana.readthedocs.io/en/master/?badge=master
