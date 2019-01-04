The RIH CIRR
=========================

Derek Merck  
<derek_merck@brown.edu>  
Rhode Island Hospital and Brown University  
Providence, RI  

[![Build Status](https://travis-ci.org/derekmerck/diana2.svg?branch=master)](https://travis-ci.org/derekmerck/diana2)
[![Coverage Status](https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg)](https://codecov.io/gh/derekmerck/diana2)
[![Doc Status](https://readthedocs.org/projects/diana/badge/?version=latest)](https://diana.readthedocs.io/en/latest/?badge=latest)

Source: <https://www.github.com/derekmerck/diana2>  
Documentation: <https://diana.readthedocs.io>  
Image:  <https://cloud.docker.com/repository/docker/derekmerck/diana2>



The RIH CIRR
-------------------

The RIH Clinical Imaging Research Repository (CIRR) was the initial development site for all of these configurations.

### Overview

The RIH CIRR stack deploys multiple services to the Swarm cluster.

- A [Traefik][] reverse proxy
- A [Portainer][] agent network
- A [Postgres][] database with bind-mounted storage
- A [Splunk][] data aggregator with bind-mounted storage
- An [Orthanc][] DICOM archive
- An Orthanc instance configured as a simple DICOM ingress multiplexer to the archive and 3D workstations
- An Orthanc instance configured as a DICOM Q/R bridge to the PACS for external data pulls

The bridge service can be manipulated using DIANA watcher scripts to monitor and index the clinical PACS, and to exfiltrate and anonymize large data collections.




### Usage

#### Provision An Environment

- At RIH, the CIRR runs in production on a pair of 16-core Xeon servers with 200GB of RAM each.  One node has an attached iSCSI interface to a 45TB StorSimple.  The system handles around one hundred thousand image studies, or about 10 million image instances, per year.
- For staging, we use two disposable desktop-type machines with 8GB of RAM and about 1TB of disk.
- For testing, we use two disposable Atom-based cloud instances with 8GB of RAM and 10GB of disk.

1. Provision 2-3 nodes with Docker and `docker-compose`.

_Note: Requires Docker version >= 18 for ingress routing._

The node that supports storage-bound operations (PostgreSQL, Splunk) should have directories pre-created for Docker to use as persistent storage.

See cloud-init: <https://gist.github.com/derekmerck/7b55c34c91954e84aa155e487ffe2e8d>

```yaml
$ mkdir -p /data/{splunk,postgres}
```


#### Install the Administrative Backend

The admin stack only needs to be deployed once, and then all other stacks can share the same cluster and data management systems.  

4. Set variables for abstractions and secrets

Create a `cirr.env` file on the master and source it.

```yaml
export DATA_DIR=/data
export PORTAINER_PASSWORD=<hashed pw>
export SPLUNK_PASSWORD=<plain pw>
export SPLUNK_HEC_TOKEN=<TOKEN0-TOKEN0-TOKEN0-TOKEN0>
```

_Note: The Splunk password must be at least 8 characters long, or Splunk will fail to initialize properly._

5. Install the "admin" backend stack:

```bash
$ . cirr.env && docker stack deploy -c admin-stack.yml admin
```

Result:
 
- Adds a Portainer/Portainer-agent service for monitoring the stack on port 9000 
- Adds a Traefik reverse proxy service on ports 80, 433, and 8080
- Adds a Splunk data aggregation service (with a HEC ingress token enabled) on ports 8000 and 8088-89
- Adds a network overlay for Portainer-agent communication
- Adds a proxy network overlay for Traefik routing
  - Additional stacks should be connected to `admin_proxy_network` as an external network
  - Labels on participating services should be set for the Traefik network, i.e., `traefik.docker.network=admin_proxy_network`
  

TODO:

Currently have to manually do a bunch of things:

- add a dicom index 
- add a hec token
- enable hec
- switch off https for hec
- re-deploy with correct hec token

I did these all with an Ansible role previously.  Need to investigate implementing similar here.


#### Setup the CIRR Core

6. Set additional variables for abstractions and secrets

Addend `cirr.env` with service-specific secrets.

```yaml
export DATA_DIR=/data
export ORTHANC_PG_DATABASE=orthanc
export ORTHANC_PASSWORD=orthanc
export POSTGRES_PASSWORD=postgres
export MOD_PACS=PACS,10.0.0.1,11112  # aet, ip addr, port format
export MOD_WORKSTATION=TERARECON,10.0.0.2,11112
```

7. Start up the service stack

```bash
$ . cirr.env && docker stack deploy -c cirr-stack.yml cirr
```

Result:

- Adds the postgres backend for the cirr_service_network on port 5432
  - Additional stacks should be connected to `cirr_service_network` to use the shared postgres backend
- Adds a replicated Orthanc archive service on DICOM port 4242
- Adds the Orthanc ingress MUX on DICOM port 5252
- Adds the Orthanc bridge service on DICOM port 6262

TODO:

- Need to tweak postgres settings to use much more memory when available

_Note: if volumes are created on a node, they are not removed when the stack is removed.  They must manually be removed to clear errors about directories not being found._


#### Augmenting the CIRR with Additional Projects

The CIRR can have additional Orthanc and DIANA nodes attached to it for various tasks.  

- `derekmerck/orthanc-wbv` images can be used as research project mini-PACS servers.
- `derekmerck/diana` or `derekmerck/diana-ai` images can be used for automated post-processing and to drive continuous data monitoring tasks

8. Start up a projects stack

```bash
$ docker stack deploy --compose-file=projects-stack.yml projects
```

Result:

- Adds a project-specific Orthanc instance with the Osimis webviewer plugin
- Adds an indexing service that uses the bridge to watch a PACS and collect study metadata in Splunk (pointed at `mock` by default)


#### Testing

9. Add a mock pacs and random study header generator:

```bash
$ docker stack deploy -c mock-stack.yml mock
```

Result:

- Adds a mock PACS service on DICOM port 7272


#### Notes

Some points of potential failure here:

- The database backend is constrained to a single system with a large disk store.  This would benefit from a distributed storage system, like Rexray.
- The IP address for the bridge is hardcoded into the sending modalities and PACS.  They should be using a name with multiple IP's or an non-bound IP that can be reassigned across the cluster as necessary.
- With a setup of 3 machines, only fault tolerant against loss of a single manager node


## The SIREN CIRR

Differences:  
- SSL certficate validation
- Anonymization and compression on data ingress


## The OpenDose CIRR

Differences:
- Orthanc router ingress
- DIANA watcher for instance indexing
- Splunk dashboards


## Notes

Portainer showing multiple copies of the same container:

````bash
$ docker service rm admin_portainer-agent
$ docker service rm admin_portainer
$ docker stack deploy -c admin-stack.yml admin
````

Don't forget to turn off acknoweldgement in the HEC -- otherwise it will insist on a data channel and show up with 400's

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

## Verifying Files

md5 hashes for these scripts are published on the [DIANA Hashes Gist](https://gist.github.com/derekmerck/4b0bfbca0a415655d97f36489629e1cc) as `cirr_hashes.json`.

A simple hash verification utility will compare local file hashes to the public hashes:

```bash
pip install git+https://github.com/derekmerck/check-hashes
python3 -m check-hashes verify 4b0bfbca0a415655d97f36489629e1cc cirr_hashes RIH/cirr_stack.yml
```
