![logo](resources/images/diana_logo_sm.png)DICOM Image Analysis and Archive
==================

Derek Merck  
<derek.merck@ufl.edu>  
University of Florida and Shands Hospital  
Gainesville, FL  

[![Build Status](https://travis-ci.org/derekmerck/diana2.svg?branch=master)](https://travis-ci.org/derekmerck/diana2)
[![Coverage Status](https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg)](https://codecov.io/gh/derekmerck/diana2)
[![Doc Status](https://readthedocs.org/projects/diana/badge/?version=master)](https://diana.readthedocs.io/en/master/?badge=master)

Source: <https://www.github.com/derekmerck/diana2>  
Documentation: <https://diana.readthedocs.io>  
Image:  <https://cloud.docker.com/repository/docker/derekmerck/diana2>


Overview
----------------

Hospital picture archive and communications systems (PACS) are not well suited for "big data" analysis.  It is difficult to identify and extract datasets in bulk, and moreover, high resolution data is often not even stored in the clinical systems.

**DIANA** is a [DICOM][] imaging informatics platform that can be attached to the clinical systems with a very small footprint, and then tuned to support a range of tasks from high-resolution image archival to cohort discovery to radiation dose monitoring.  It provides DICOM services, image data indexing, REST endpoints for scripting, and user access control through an amalgamation of free and free and open source (FOSS) systems.

[DICOM]: http://www.dicomstandard.org/


Python-Diana
----------------

The Python-Diana package for Python >= 3.6 provides an api for a network of DICOM-file related services including PACS query, local archive, anonymization, file access, and study indexing.

It comes in two flavors: vanilla and "plus," which includes dependencies on scientific and machine learning packages.

### Installation

```bash
$ pip3 install git+https://github.com/derekmerck/diana2#subdirectory=package
```

Or install as locally editable:

```bash
$ git clone git+https://github.com/derekmerck/diana2
$ pip3 install -e diana2/package
$ pip3 install -e diana2/package[plus]
```

Refer to the [package docs](package/README.md) for details about dependencies.


`diana-cli`
-----------------

`diana-cli` provides command-line bindings for "service-level" tasks.  Specifically, given a service description file (endpoint kwargs as yaml), an endpoint can be created and methods (get, put, etc) called on it via command-line. 

```bash
$ diana-cli --version
2.1.x
```

Diana-Plus functions are available as well.
```bash
$ pip3 install diana2/package[plus]
$ diana-cli --version
2.1.x++
```

DIANA package hashes by version number are publicly posted at <https://gist.github.com/derekmerck/4b0bfbca0a415655d97f36489629e1cc> and can be easily validated through `diana-cli`.

```bash
$ diana-cli verify
Package signature python-diana:2.1.x:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx is valid.
Package signature python-crud:1.0.x:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx is valid.
Package signature python-wuphf:1.0.x:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx is valid.
```

Of course, users should never trust a package to validate itself, so see [gistsig][] for details on the algorithm and how to perform a simple external audit.

[gistsig]: https://github.com/derekmerck/gistsig

Refer to the [diana-cli docs](diana-cli.md) or `diana-cli --help` for more documentation.

Docker-Image
----------------

The docker-image directory includes details on building diana2 and diana2-plus docker cross-platform docker images.  Current builds of these images from ci are available on docker hub.

```bash
$ docker run -it derekmerck/diana2 /bin/bash diana-cli --version
2.1.x
```

Refer to the [container docs](platform/docker-image/README.md) for build resources and the [stack docs](platform/docker-stacks/README.md) for service stacks.


GUID Mint
----------------

Refer to the [guid docs](guid.md) for details of the GUID and pseudo-id generation algorithm.


Python-CRUD and Python-WUPHF
---------------

DIANA provides a generic python framework for implementing CRUD (create, retrieve, update, delete) service endpoints and management daemons.  Python-CRUD also supports distributed task management with [celery][].

[celery]: http://www.celeryproject.org

Endpoints provide an abstraction layer between application specific logic and technical implementations of specific services such a file directories or servers (generically called Gateways here).  Method syntax generally follows standard KV nomenclature (get, put, find, etc.)

*Endpoints* handle *Items*, which may include metadata, data, and other attributes.  *Items* may be referenced by an *ItemID* for *Get* or *Delete* requests.  *Put* requests require an *Item* type argument.  *Find* requests describe *Items* with a mapping *Query*.

Python-Diana provides DICOM item type and endpoints, Python-[WUPHF][] provides interoperable messenging items and endpoints (email, sms, twillo).

[WUPHF]: https://en.wikipedia.org/wiki/WUPHF.com


Testing
-------

Manually run pytest with coverage and upload to codecov:

```bash
$ pip install pytest interruptingcow codecov pytest-cov
$ pytest --cov
$ codecov --token=$CODCOV_TOK
```

Citing
-------

For citation reference:
Thomas Yi, Ian Pan, Scott Collins, Fiona Chen, Robert Cueto, Ben Hsieh, Celina Hsieh, Jessica L. Smith, Li Yang, Wei-hua Liao, Lisa H. Merck, Harrison Bai, Derek Merck. DICOM Image ANalysis and Archive (DIANA): an Open-Source System for Clinical AI Applications. Journal of Digital Imaging (JDI). Nov 2021. https://doi.org/10.1007/s10278-021-00488-5

License
-------

MIT
