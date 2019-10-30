# DIANA SIREN Receiver

Derek Merck  
<derek.merck@ufl.edu>  
University of Florida and Shands Hospital  
Gainesville, FL  

[SIREN][] is an NIH-funded multi-center clinical trial network for neuroemergency and resuscitation trials.  As patients are enrolled at participating sites, imaging studies must be submitted for central review, archival, and secondary analysis.


## Purposes

1. Receive semi-anonymized image data from enrolling sites
2. Anonymize it completely and add sham id's
3. Move study to review site
4. Send receipt for submission to enrolling site and notify coordinators
5. Index imaging data for dashboards


## Setup

Create and source an `config.env` file with some required secrets:
  
  - `DATA_DIR` - Base data path on host
  - `ORTHANC_PASSWORD` - Admin password for Orthanc
  - `SPLUNK_PASSWORD`  - Admin password for Splunk
  - `SPLUNK_HEC_TOKEN` - A Splunk token (or create one later)
  - `DIANA_FKEY` - Fernet key for encoding a study signature 
  - `DIANA_ANON_SALT` - Anonymization "salt" to create a unique sham namespace
  - `SMTP_HOST` - For local email server, if applicable
  - `GMAIL_USER` - For using gmail as an email server, if applicable
  - `GMAIL_APP_PASSWORD` - Requires creating a special "app password" in the gmail user security panel

Use Docker to setup administrative services such as [Traefik][] and [Splunk][].  Setting up the baseline administration network and services is documented in `diana.platform.docker-stacks`.  A one-off Splunk container can be created with a command like this:

```bash
$ docker run -d --rm \
           -e SPLUNK_START_ARGS="--accept-license" \
           -e SPLUNK_PASSWORD=$SPLUNK_PASSWORD \
           -e SPLUNK_HEC_TOKEN=$SPLUNK_HEC_TOKEN \
           -e TZ="America/New_York" \
           -p 8000:8000 \
           -p 8088:8088 \
           -p 8089:8089 \
           splunk/splunk
```

Setup an [Orthanc][] instance for each trial.  Configure it to create the metadata field `signature`, usually by passing an env variables like `ORTHANC_META_0=signature,1025` to the `derekmerck/orthanc-wbv` container image.  The `docker-compose.yaml` for the University of Michigan SIREN Receiver can be found in `diana.platform.examples.umich-siren`.  A one-off Orthanc container can be created with a command like this:

```bash
$ docker run -d --rm \
           -e ORTHANC_METADATA_0="signature,1025" \
           -e ORTHANC_PASSWORD=$ORTHANC_PASSWORD \
           -e TZ="America/New_York" \
           -p 8042:8042 \
           derekmerck/orthanc-wbv:latest-amd64
```

Setup an incoming data directory `/incoming/hobit/site_xxx` for each submitting site.  Data from each enrolling site should be uploaded to a unique directory for processing.  The directory structure `/incoming/{trial}/{site}` is used to infer the notification channel `#{trial}-{site}` for each incoming study.

Create configuration files:
  - `services.yaml` with DIANA service descriptions for orthanc, splunk, local_smtp
  - `notifications.yaml` with channels (i.e., `#hobit-site_xxx`) and subscribers
  - `notify.txt.j2` with text for receipt message and `jinja2` template markup

Create a DIANA Docker container with appropriate config file and variable mappings.

```bash
$ docker run -it \
        -v $DATA_DIR/incoming:/incoming \
        -v $PWD/services.yaml:/services.yaml \
        -v $PWD/subscriptions.yaml:/subscriptions.yaml \
        -v $PWD/notify.txt.j2:/notify.txt.j2 \
        -e DIANA_SERVICES=@/services.yaml \
        --env-file $PWD/config.env \
        derekmerck/diana2 /bin/bash
```

Finally, interact with the `siren.py` script from the command-line.

```bash
/opt/diana$ python3 apps/siren/cli.py --version
diana-siren, version 2.1.x
```

## CLI Usage

Upload a study from the incoming directory to the appropriate archive, anonymize and tag with meta:

```bash
$ python3 siren.py upload_dir path:/incoming/hobit/site_xxx mystudy.zip orthanc:
```

Similar functionality using `diana-cli`:

```bash
$ diana-cli dgetall -b path:/incoming/hobit/site_xxx \
            setmeta "{trial:hobit,site:site_xxx}" \
            oput --anonymize -salt $DIANA_SALT \
                 --sign "signature:[AccessionNumber,StudyDateTime,PatientName,trial,site]" \
                 -f $DIANA_FKEY \
                 orthanc:
```

Upload a study in zip format to the appropriate archive, anonymize, and tag with meta:

```bash
$ python3 siren.py upload_zip path:/incoming/hobit/site_xxx mystudy.zip orthanc:
```

Get study with meta tags from orthanc, dispatch to trial-site channels and send meta to indexer:

```bash
$ python3 siren.py notify_study orthanc: xano-nxst-udyx-oid \
                   -S @/subscriptions -E gmail: -T @/receipt.txt.j2 -I splunk:
```

And similar functionalty using `diana-cli`:

```bash
$ diana-cli oget -m signature -f $DIANA_FKEY orthanc: xano-nxst-udyx-oidx \
            dispatch --subsciptions @/subscriptions.yaml \
                     --email-messenger gmail: \
                     --msg_t @/notify.txt.tmpl \
                     --channel_tmpl='$trial-$site' \
            put splunk:
```

### Start The Watcher

Start the automated watcher service.

```bash
$ python3 siren.py start-watcher \
                   path:/incoming \
                   orthanc: \
                   -S @/subscriptions.yaml \
                   -E gmail: \
                   -T @/notify.txt.j2 \
                   -I splunk:
```

This can also be passed directly to the DIANA service container as the command (call `apps/siren/siren.py`, or set the working directory with the additional argument `-w /opt/diana/apps/siren`).

[SIREN]: https://siren.network
[Traefik]: https://traefik.io
[Splunk]:  https://www.splunk.com
[Orthanc]: https://www.orthanc-server.com

License
-------------

MIT
