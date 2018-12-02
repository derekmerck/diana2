DIANA Overview
=============

platform
-------------

- containers
  - orthanc-xarch
  - diana-xarch

- stacks
  - OpenDose
  - RIH-CIRR
  - RemoteDiana
  - SIREN-CIRR


apps
-------------

- diana-cli (click)
  - check eps
  - get ep id
  - find ep q
  - pull ep dest id/wk
  - index ep create ep/ls/put id ep
  - send ep id dest

- diana-server (flask)

- radcatr (tkl)

- trialist (flask)


package
-------------

- setup

- diana

  - Endpoints - map DIANA API actions to application APIs
    - ProxiedDicom, Orthanc, DicomFiles, Redis, Splunk, CSVFile, Montage
    - from_kwargs()

  - Daemon
    - Mock, Watcher
    - WatchableEndpoint
    - from_kwargs()
    - add_handler(ep, event, partial func)

  - Dixel (map)
    - DicomLevel
    - from_kwargs()
    - from_file()
    - from_montage() (remapping)
    - id(ep type)
    - set_shams()

  - Report

  - Worklist (set)
    - from_txt() (accession nums)
    - from_csv()
    - from_montage_csv()
    - from_inventory()

  - GUIDMint

  - utils
    - gateways - Expose application apis
      - Requester
      - Orthanc
      - Splunk
      - Montage
      - DicomFile
    - dicom
      - DicomStrings
      - DicomLevel
      - DicomJson
    - watcher


API Actions
-------------

- create
  - id = put(dx)
  - id/dx = anonymize(id, map)

- read
  - dx = get(id)
  - ids/dxs = find(q map)
  - ids/dxs = pfind(q map, proxy id)
  - exists(id/query map)

- update
  - put(id, dx)
  - patch(id, key, value)

- delete
  - delete(id)

- do
  - send(id, ep)
  - result = handle(id/dx, func)
  - check
  - inventory


tests
------------

- PackageTests
- PlatformTests
  - test vm
  - test stack
- AppTests


docs
------------

Sphinx





New study
Check Patient Identity Removed (0012,0062)
Yes -> end
No -> get study info
Create anon map
  -> including private tag for patient-data-code (PHI against fernet key)
Submit anon
---
sumbit to forward
remove source, remove forwarde

.diana

DIANA_SERVICES (json)
DIANA_SERVICES_PATH (yaml, dir)
DIANA_KEY (fernet)

diana <cmd> <services> {<key>: anon/info} {--dryrun}

  # Actions

  get {--info} {--key} oid source
  find query source
  pfind {--retreive} query proxied_source
  *pull query proxied_source

  put {--anon} file dest
  index dir kvdest
  iput dir kvsource dest

  handle oid source dest handler
  *anonymize oid source
  *send {--anon} oid source dest


  ## Daemons

  watch {--route source dest handler}
  mock  {params} dest


