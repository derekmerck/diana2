The RIH CIRR
=========================

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
-------------------

The RIH Clinical Imaging Research Repository (CIRR) was the initial development site for all of these configurations.

The Admin stack provides

- A [Traefik][] http reverse-proxy
  - http://host:8080
- A [Portainer][] swarm manager (and Portainer-agent on worker nodes)
  - http://host:9000
- A [Redis][] in-memory kv store
  - redis://host:6324
- A [Splunk][] data aggregator with bind-mounted storage
  - http://host:8000,8088-9
- A Portainer-agent network
- An attachable proxy network ("admin_proxy_network")

The RIH CIRR stack provides:

- An [Orthanc][] DICOM archive
  - http://host/archive
  - dicom://CIRRARCH@host:4242
- An Orthanc instance configured as a simple DICOM ingress multiplexer to the archive and 3D workstations
  - http://host/router
  - dicom://CIRRMUX@host:4243
- An Orthanc instance configured as a DICOM Q/R bridge to the PACS for external data pulls
  - http://host/bridge
  - dicom://CIRR1@host:11112
- An Orthanc "MockPacs" for testing
  - http://host/mock
  - dicom://MOCK@host:2424
- A [Postgres][] database with bind-mounted storage
- An attachable service network ("cirr_service_network")

The bridge service can be manipulated using DIANA watcher scripts to monitor and index the clinical PACS, and to exfiltrate and anonymize large data collections.

Additional project repositories can be added in the "projects" stack.

- A legacy CIRR v1 stack is also available and publishes on:
  - http://host/archive-old
  - dicom://CIRRV1@host:14242

[Traefik]:()
[Portaier]:()
[Redis]:()
[Splunk]:()
[Orthanc]:()
[Postgres]:()

Usage
-------------

### Provisioning

- At RIH, the CIRR runs in production on a pair of 16-core Xeon servers with 200GB of RAM each.  One node has an attached iSCSI interface to a 45TB StorSimple.  The system handles around one hundred thousand image studies, or about 10 million image instances, per year.
- For staging, we use two disposable desktop-type machines with 8GB of RAM and about 1TB of disk.
- For some testing, we use two disposable Atom-based cloud instances with 8GB of RAM and 10GB of disk.

1. Install Docker-ce and `docker-compose`. 
_Note: Requires Docker version >= 18 for ingress routing._

2. Create directories for persistent storage on the node that will support storage-bound operations (PostgreSQL, Splunk). 
See cloud-init: <https://gist.github.com/derekmerck/7b55c34c91954e84aa155e487ffe2e8d> 

```yaml
$ mkdir -p /data/{splunk,postgres}
```

### Install the admin stack

3. Set variables for abstractions and secrets.  Create a `cirr.env` file on the master and source it.
_Note: The Splunk password must be at least 8 characters long, or Splunk will fail to initialize properly._

```yaml
export DATA_DIR=/data
export PORTAINER_PASSWORD=<hashed pw>
export SPLUNK_PASSWORD=<plain pw>
export SPLUNK_HEC_TOKEN=<TOKEN0-TOKEN0-TOKEN0-TOKEN0>
```

4. Install the administrative backend.  The admin stack only needs to be deployed once, and then all other stacks can share the same cluster and data management systems.  

```bash
$ . cirr.env && docker stack deploy -c docker-stacks/admin/admin-stack.yml admin
$ . cirr.env && docker stack deploy -c docker-stacks/admin/splunk-service.yml admin
```

### Install the CIRR service stack

5. Set additional variables for abstractions and secrets

```yaml
export DATA_DIR=/data
export ORTHANC_PG_DATABASE=orthanc
export ORTHANC_PASSWORD=orthanc
export POSTGRES_PASSWORD=postgres
export MOD_PACS=PACS,10.0.0.1,11112  # aet, ip addr, port format
export MOD_WORKSTATION=TERARECON,10.0.0.2,11112
```

6. Start up the service stack

```bash
$ . cirr.env && docker stack deploy -c examples/rih-cirr/cirr_v2.yml cirr
```

7. Start up a projects stack.  The CIRR can have additional Orthanc and DIANA nodes attached to it for DICOM review and automated post-processing tasks.  

```bash
$ . cirr.env && docker stack deploy -c examples/rih-cirr/projects projects
```

8. To access legacy data, a CIRRv1 stack is also available.  (Skip this on new servers and testing.)

```bash
$ docker stack deploy -c examples/rih-cirr/cirr_v1.yml cirr1
```

### Install a Test Service

9. Add a mock pacs and random study header generator:

```bash
$ docker stack deploy -c docker-stacks/diana-workers/mock-stack.yml mock
```


Notes
----------------

### Reset Volumes

_Note: if volumes are created on a node, they are not removed when the stack is removed.  They must manually be removed to clear errors about directories not being found._

### Points of Potential Failure

- The database backend is constrained to a single system with a large disk store.  This would benefit from a distributed storage system, like Rexray.
- The IP address for the bridge is hard-coded into the sending modalities and PACS.  They should be using a name with multiple IP's or an non-bound IP that can be reassigned across the cluster as necessary.
- With a setup of 3 machines, the system only fault tolerant against loss of a single manager node


### Postgresql Config

See <http://pgtune.leopard.in.ua> for simple config tool.  For our servers w 200GB of RAM I used the following:

```
max_connections = 200
shared_buffers = 25GB
effective_cache_size = 75GB
work_mem = 128MB
maintenance_work_mem = 2GB
min_wal_size = 1GB
max_wal_size = 2GB
checkpoint_completion_target = 0.7
wal_buffers = 16MB
default_statistics_target = 100
```

Although it did not seem to make much of a difference in performance.

### Portainer Reset

Fix Portainer showing multiple copies of the same container:

````bash
$ docker service rm admin_portainer-agent
$ docker service rm admin_portainer
$ docker stack deploy -c docker-stacks/admin/admin-stack.yml admin
````

### Splunk Config

Don't forget to turn off acknowledgement in the HEC -- otherwise it will insist on a data channel and show up with 400's

Testing:
```bash
curl -k http://splunk:8088/services/collector -H "Authorization: Splunk $SPLUNK_HEC_TOKEN" -d '{"event":"Hello, World!"}'
```

Increase length for `_json` sources:

`/opt/splunk/etc/system/local/props.conf`

```toml
[_json]
TRUNCATE = 500000
```

Currently have to manually do a bunch of things:

- add a dicom index 
- add a hec token
- enable hec
- switch off https for hec
- re-deploy with correct hec token

I did these all with an Ansible role previously.  Need to investigate implementing similar here.



