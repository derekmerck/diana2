
`diana-cli`
==================

Derek Merck  
<derek_merck@brown.edu>  
Rhode Island Hospital and Brown University  
Providence, RI  

[![Build Status](https://travis-ci.org/derekmerck/diana2.svg?branch=master)](https://travis-ci.org/derekmerck/diana2)
[![codecov](https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg)](https://codecov.io/gh/derekmerck/diana2)

Source: <https://www.github.com/derekmerck/diana2>  
Documentation: <https://diana.readthedocs.io>

```
Usage: diana-cli [OPTIONS] COMMAND [ARGS]...

  Run diana packages using a command-line interface.

Options:
  --verbose / --no-verbose
  -s, --services TEXT
  -S, --services_path PATH
  --help                    Show this message and exit.

Commands:
  check         Check status of service ENDPOINTS
  index         Inventory dicom dir PATH with INDEX service for retrieval
  indexed-pull  Pull study by accession number from a PATH with INDEX service...
  mock          Create a mock site from DESC and send data to DEST service.
  ofind         Find studies matching yaml/json QUERY in SOURCE Orthanc...
```

Requires platform service endpoint description in yaml format.

```yaml
---
orthanc:
  ctype: Orthanc
  port: 8042
  name: my_orthanc

redis:
  ctype: Redis
```
## check

```
Usage: diana-cli check [OPTIONS] [ENDPOINTS]...

  Check status of service ENDPOINTS

Options:
  --help  Show this message and exit.
```
## index

```
Usage: diana-cli index [OPTIONS] PATH INDEX

  Inventory dicom dir PATH with INDEX service for retrieval

Options:
  --orthanc_db  Use subpath width/depth = 2
  --help        Show this message and exit.
```
## indexed-pull

```
Usage: diana-cli indexed-pull [OPTIONS] ACCESSION_NUMBER PATH INDEX DEST

  Pull study by accession number from a PATH with INDEX service and send to
  DEST

Options:
  --orthanc_db  Use subpath width/depth = 2
  --help        Show this message and exit.
```
## mock

```
Usage: diana-cli mock [OPTIONS] [DESC]

  Create a mock site from DESC and send data to DEST service.

Options:
  --dest TEXT  Destination service
  --help       Show this message and exit.
```
## ofind

```
Usage: diana-cli ofind [OPTIONS] QUERY SOURCE

  Find studies matching yaml/json QUERY in SOURCE Orthanc service {optionally
  with proxy DOMAIN}

Options:
  --domain TEXT   Domain for proxied query
  -r, --retrieve
  --help          Show this message and exit.
```


License
-------------

MIT

