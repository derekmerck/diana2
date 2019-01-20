DICOM Image Analysis and Archive
==================

Derek Merck  
<derek_merck@brown.edu>  
Rhode Island Hospital and Brown University  
Providence, RI  

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

It comes in two flavors: vanilla and "plus", which includes dependencies on scientific and machine learning packages.

### Installation

```bash
$ git clone git+https://github.com/derekmerck/diana2
$ pip3 install -e diana2/package
$ pip3 install -e diana2/package[plus]
```

Diana-CLI
-----------------

Diana-CLI provides a command-line interface to invoke several common pipelines.  It requires a service definition yaml file as input.

### Installation

```bash
$ pip3 install -e diana2/apps/diana-cli
$ diana-cli --version
2.0.11
```

Diana-Plus functions are available as well.
```bash
$ pip3 install -e diana2/apps/diana-cli[plus]
$ diana-plus --version
2.0.11
```

Docker-Image
----------------

The docker-image directory includes details on building diana2 and diana2-plus docker cross-platform docker images.  Current builds of these images from ci are available on docker hub.

```bash
$ docker run -it derekmerck/diana2 /bin/bash diana-cli --version
('diana-cli.py', 'python-diana'), version ('2.1.1', '2.0.12')
```


License
-------

MIT
