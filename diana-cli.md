diana-cli
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

`diana-cli` provides a command-line interface to DIANA endpoints.

## Parameter Types

- MAPPING parameters may be json or yaml format strings, or an `@/file.yaml` path to a json or yaml formatted file.
- ARRAY parameters may be json or yaml format strings, or an `@/file.txt` path to a newline separated list of items.
- ENDPOINT parameters must either exist in the services description, or be a prefixed shortcut such as `path:/data/my_dir`, which would create a DcmDir with `basepath=/data/my_dir`.

## Usage

```
Usage: diana-cli [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Run DIANA packages using a command-line interface.

  $ python3 -m diana.cli.cli --version
  diana-cli, version 2.1.x

  $ pip3 install python-diana
  $ diana-cli --version
  diana-cli, version 2.1.x

  Also supports chained operations on dixels.  For example, to read a
  directory and put all instances in a local orthanc:

  $ diana-cli dgetall path:/data/dcm oput orthanc:

Options:
  --version               Show the version and exit.
  -v, --verbose
  -s, --services MAPPING  Services dict as yaml/json format string or @file.yaml
  --help                  Show this message and exit.

Commands:
  check       Check endpoint status
  delete      Delete items in endpoint
  dgetall     Get all instances from DcmDir for chaining
  do          Call endpoint method
  fdump       Convert and save chained DICOM image data in png format
  findex      Index items by accession number
  findex-get  Put indexed files in a destination node by accession number  $...
  get         Get items from endpoint for chaining
  guid        Generate a GUID
  ls          List all services and health
  mfind       Find items in Montage by query for chaining
  mock        Generate mock DICOM traffic
  ofind       Find item in Orthanc by query for chaining
  oget        Get studies from Orthanc
  ogetm       Get study-level item metadata from Orthanc
  oput        Put chained instances in Orthanc
  oputm       Set study-level item metadata in Orthanc
  print       Print chained items to stdout
  put         Put chained items in endpoint
  setmeta     Set metadata kvs for chained items
  verify      Verify DIANA source code against public gist signature
  wsend       Send items via Messenger endpoint

  SERVICES is a required platform endpoint description in json/yaml format.

  ---
  orthanc:
    ctype: Orthanc
    port: 8042
    host: my_orthanc
  redis:
    ctype: Redis
  ...
```
## check

```
Usage: diana-cli check [OPTIONS] ENDPOINT

  Check endpoint status

  $ crud-cli check redis

Options:
  --help  Show this message and exit.
```
## delete

```
Usage: diana-cli delete [OPTIONS] SOURCE [ITEMS]

  Remove items from endpoint

Options:
  --help  Show this message and exit.
```
## dgetall

```
Usage: diana-cli dgetall [OPTIONS] SOURCE

  Get all instances from DcmDir for chaining

Options:
  -b, --binary  Get binary file as well as data
  --help        Show this message and exit.
```
## do

```
Usage: diana-cli do [OPTIONS] ENDPOINT METHOD

  Call an arbitrary endpoint method with *args, *mapargs, and **kwargs

  $ crud-cli do redis check
  $ crud-cli do redis find -m '{"data":"test"}'
  $ crud-cli do redis get -g my_key print
  $ crud-cli do orthanc get xxxx-xxxx... -k '{"level":"series"}'

Options:
  -g, --args ARRAY       Arguments as comma or newline separated or @file.txt
                         format
  -m, --mapargs MAPPING  Mapping-type arguments as json or @file.yaml format
  -k, --kwargs MAPPING   Keyword arguments as json or @file.yaml format
  --help                 Show this message and exit.
```
## fdump

```
Usage: diana-cli fdump [OPTIONS] [[png]] [OUTPATH]

  Convert and save chained DICOM image data in png format

  /b $ diana-cli get path:/data/dcm IM0001.dcm fdump $ ls IM0001.png

Options:
  --help  Show this message and exit.
```
## findex

```
Usage: diana-cli findex [OPTIONS] INDEX

  Index files by accession number

  $ diana-cli findex path:/data redis:

Options:
  --help  Show this message and exit.
```
## findex-get

```
Usage: diana-cli findex-get [OPTIONS] SOURCE INDEX COLLECTION_IDS

  Put indexed files in a destination node by accession number

  $ diana-cli findex-get path:/data redis: all print
  $ diana-cli findex-get -b path:/data redis: CT3456789 oput orthanc:

Options:
  -b, --binary  Get binary file as well as data
  --help        Show this message and exit.
```
## get

```
Usage: diana-cli get [OPTIONS] SOURCE ITEMS

  Get items from endpoint for chaining

Options:
  -k, --kwargs MAPPING  kwargs dict as yaml/json format string or @file.yaml,
                        i.e., '{"level": "series"}'
  -b, --binary          Get binary file as well as data
  --help                Show this message and exit.
```
## guid

```
Usage: diana-cli guid [OPTIONS] NAME [[%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d
                      %H:%M:%S]] [GENDER]

  Generate a globally unique sham ID from NAME, DOB, and GENDER.

Options:
  --age INTEGER                   Substitute age and ref date for DOB
  --reference_date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  Reference date for AGE
  --salt TEXT                     Anonymization salt
  --help                          Show this message and exit.

  $ python3 diana-cli.py guid --age 40 "MERCK^DEREK^L"
  Generating GUID
  ------------------------
  WARNING:GUIDMint:Creating non-reproducible GUID using current date
  {'birth_date': '19891023',
   'id': 'TJEIRJJ2MK5HBVHLQCB5YDPXMU64LDPM',
   'name': 'THURMER^JONAS^E',
   'time_offset': '-3 days, 0:22:08'}
```
## ls

```
Usage: diana-cli ls [OPTIONS]

  List all services and health

  $ crud-cli ls

Options:
  -h, --health-check / -k, --skip-health-check
                                  Skip health
  --help                          Show this message and exit.
```
## mfind

```
Usage: diana-cli mfind [OPTIONS] SOURCE

  Find items in Montage by query for chaining.

  $ diana-cli mfind -a 520xxxxx montage print
  { "AccesssionNumber": 520xxxxx, "PatientID": abcdef, ... }

  $ diana-cli mfind -a @my_accessions.txt -e lungrads -e radcat montage print
  jsonl > output.jsonl $ cat output.jsonl { ... lungrads='2',
  current_smoker=False, pack_years=15, radcat=(3,true) ... }

Options:
  -a, --accession_numbers ARRAY   Requires PHI privileges on Montage
  --start_date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  Starting date query bound
  --end_date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  Ending date query bound
  --today
  -q, --query MAPPING             Query string
  -e, --extraction [radcat|lungrads]
                                  Perform a data extraction on each report
  --help                          Show this message and exit.
```
## mock

```
Usage: diana-cli mock [OPTIONS] [DESC]

  Generate synthetic studies on a schedule according to a site description
  DESC.  Studies are optionally forwarded to an endpoint DEST.

Options:
  --dest ENDPOINT  Destination DICOM service
  --help           Show this message and exit.

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
```
## ofind

```
Usage: diana-cli ofind [OPTIONS] SOURCE

  Find studies matching yaml/json QUERY in SOURCE Orthanc or ProxiedDicom
  service. The optional proxy DOMAIN issues a remote-find to a manually
  proxied DICOM endpoint.

Options:
  -a, --accession_numbers ARRAY   Requires PHI privileges on Montage
  --today
  -q, --query MAPPING             Query string
  -l, --level [studies|series|instances]
  -d, --domain TEXT               Remote domain for proxied query
  -r, --retrieve                  Retrieve from remote for proxied query
  --help                          Show this message and exit.
```
## oget

```
Usage: diana-cli oget [OPTIONS] SOURCE ITEMS

  Get studies from Orthanc

Options:
  -m, --metakeys ARRAY  Meta key(s) to retrieve
  --fkey TEXT           Fernet key for encrypting metadata
  -k, --kwargs MAPPING  kwargs dict as yaml/json format string or @file.yaml,
                        i.e., '{"level": "series"}'
  -b, --binary          Get binary file as well as data
  --help                Show this message and exit.
```
## ogetm

```
Usage: diana-cli ogetm [OPTIONS] SOURCE ITEM KEY

  Get study-level item metadata from Orthanc

Options:
  --fkey TEXT  Fernet key for decrypting metadata
  --help       Show this message and exit.
```
## oput

```
Usage: diana-cli oput [OPTIONS] DEST

  Put chained instances in Orthanc

Options:
  -a, --anonymize   Anonymize instances as they are uploaded
  --anon-salt TEXT  Anonymization salt
  --sign MAPPING    Signature key(s) and elements
  --fkey TEXT       Fernet key for encrypting metadata
  --help            Show this message and exit.
```
## oputm

```
Usage: diana-cli oputm [OPTIONS] SOURCE ITEM UPDATES

  Set study-level item metadata in Orthanc

Options:
  --help  Show this message and exit.
```
## print

```
Usage: diana-cli print [OPTIONS] [[plain|jsonl|csv]]

  Print chained items to stdout

Options:
  --help  Show this message and exit.
```
## put

```
Usage: diana-cli put [OPTIONS] DEST

  Put chained items in endpoint

Options:
  -k, --kwargs MAPPING  kwargs dict as yaml/json format string or @file.yaml,
                        i.e., '{"level": "series"}'
  --help                Show this message and exit.
```
## setmeta

```
Usage: diana-cli setmeta [OPTIONS] UPDATE_DICT

  Set metadata kvs for chained items

Options:
  --help  Show this message and exit.
```
## verify

```
Usage: diana-cli verify [OPTIONS]

  Verify DIANA source code against public gist signature.

  This function is a convenience only; if the package has been altered, it
  could easily be altered to return correct hashes or check the wrong gist.
  The paranoid should refer to <https://github.com/derekmerck/gistsig> for
  instructions on finding performing an external manual audit.

Options:
  --help  Show this message and exit.
```
## wsend

```
Usage: diana-cli wsend [OPTIONS] MESSENGER

  Send data or chained items via Messenger endpoint

  $ wuphf-cli send -t test@example.com gmail:user:pword "msg_text: Hello 123"

Options:
  --data MAPPING
  -t, --target TEXT  Optional target, if not using a dedicated messenger
  -m, --msg_t TEXT   Optional message template
  --help             Show this message and exit.
```
