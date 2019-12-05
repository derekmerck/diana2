DIANA SIREN Receiver
====================

| Derek Merck
| derek.merck@ufl.edu
| University of Florida and Shands Hospital
| Gainesville, FL

`SIREN <https://siren.network>`__ is an NIH-funded multi-center clinical
trial network for neuroemergency and resuscitation trials. As patients
are enrolled at participating sites, imaging studies must be submitted
for central review, archival, and secondary analysis.

Purposes
--------

1. Receive semi-anonymized medical image studies from enrolling sites
2. Anonymize each study completely and add sham id’s
3. Move each study to review site
4. Send receipt for submission to enrolling site and notify coordinators
5. Index imaging data for dashboards

.. figure:: siren_im_review.png
   :alt: SIREN image review schema

   SIREN image review schema

Setup
-----

Create and source an ``config.env`` file with some required secrets:

-  ``DATA_DIR`` - Base data path on host
-  ``ORTHANC_PASSWORD`` - Admin password for Orthanc
-  ``SPLUNK_PASSWORD`` - Admin password for Splunk
-  ``SPLUNK_HEC_TOKEN`` - A Splunk token (or create one later)
-  ``DIANA_FKEY`` - Fernet key for encoding a study signature
-  ``DIANA_ANON_SALT`` - Anonymization “salt” to create a unique sham
   namespace
-  ``SMTP_HOST`` - For local email server, *if applicable*
-  ``GMAIL_USER`` - For using gmail as an email server, *if applicable*
-  ``GMAIL_APP_PASSWORD`` - Requires creating a special “app password”
   in the gmail user security panel, *if applicable*

Use Docker to setup administrative services such as
`Traefik <https://traefik.io>`__ and
`Splunk <https://www.splunk.com>`__. Setting up the baseline
administration network and services is documented in
``diana.platform.docker-stacks``. A one-off Splunk container for testing
can be created with a command like this:

.. code:: bash

   $ docker run -d --rm \
              --name splunk \
              -e SPLUNK_START_ARGS="--accept-license" \
              -e SPLUNK_PASSWORD=$SPLUNK_PASSWORD \
              -e SPLUNK_HEC_TOKEN=$SPLUNK_HEC_TOKEN \
              -e TZ="America/New_York" \
              -p 8000:8000 \
              -p 8088:8088 \
              -p 8089:8089 \
              splunk/splunk

Setup an `Orthanc <https://www.orthanc-server.com>`__ instance for each
trial. Configure it to add users and to create the metadata field
``signature``, usually by passing an env variables like
``ORTHANC_META_0=signature,1025`` to the ``derekmerck/orthanc-wbv``
container image. The ``docker-compose.yaml`` for the University of
Michigan SIREN Receiver can be found in
``diana.platform.examples.umich-siren``. A one-off Orthanc container for
testing can be created with a command like this:

.. code:: bash

   $ docker run -d --rm \
              --name orthanc \
              -e ORTHANC_METADATA_0="signature,1025" \
              -e ORTHANC_PASSWORD=$ORTHANC_PASSWORD \
              -e TZ="America/New_York" \
              -p 8042:8042 \
              derekmerck/orthanc-wbv:latest-amd64

Setup an incoming data directory ``/incoming/hobit/site_xxx`` for each
submitting site. Data from each enrolling site should be uploaded to a
unique directory for processing. The directory structure
``/incoming/{trial}/{site}`` is used to infer the notification channel
``f"{trial}-{site}"`` for each incoming study.

Create configuration files: - ```services.yaml`` <services.yaml>`__ with
DIANA service descriptions for orthanc, splunk, local_smtp -
```subscriptions.yaml`` <subscriptions.yaml>`__ with two documents: one
with channel tag to name mappings (i.e., ``site_xxx: My Site Hospital``)
and one with subscribers, including affiliation and subscribed channels
- ```notify.txt.j2`` <notify.txt.j2>`__ with text for receipt message
and ``jinja2`` template markup. I soft-link this from the
diana/apps/siren directory.

Create a DIANA Docker container with appropriate config file and
variable mappings. (In this case, I added the SIREN platform service and
logging networks to resolve the hobit and splunk container names).

.. code:: bash

   $ docker run -it --rm \
           -v $DATA_DIR/incoming:/incoming/hobit \
           -v $PWD/services.yaml:/services.yaml \
           -v $PWD/subscriptions.yaml:/subscriptions.yaml \
           -v $PWD/notify.txt.j2:/notify.txt.j2 \
           -e DIANA_SERVICES=@/services.yaml \
           --env-file $PWD/config.env \
           --network siren_service_network \
           --network admin_logging_network \
           derekmerck/diana2 /bin/bash

Then interact with the ```siren.py`` <siren.py>`__ script from the
container command-line.

.. code:: bash

   /opt/diana$ python3 apps/siren/siren.py --version
   diana-siren, version 2.1.x

CLI Usage
---------

Upload a study from the incoming directory to the appropriate archive,
anonymize and tag with meta:

.. code:: bash

   $ python3 siren.py upload-dir path:/incoming/hobit/site_xxx orthanc:

Similar functionality using ``diana-cli`` explicitly:

.. code:: bash

   $ diana-cli dgetall -b path:/incoming/hobit/site_xxx \
               setmeta "{trial:hobit,site:site_xxx}" \
               oput --anonymize -salt $DIANA_SALT \
                    --sign "signature:[AccessionNumber,StudyDateTime,PatientName,trial,site]" \
                    -f $DIANA_FKEY \
                    orthanc:

Upload a study in zip format to the appropriate archive, anonymize, and
tag with meta:

.. code:: bash

   $ python3 siren.py upload-zip path:/incoming/hobit/site_xxx mystudy.zip orthanc:

Get study with meta tags from orthanc, dispatch to trial-site channels
and send meta to indexer:

.. code:: bash

   $ python3 siren.py notify-study orthanc: xano-nxst-udyx-oid \
                      -S @/subscriptions.yaml -E gmail: -T @/receipt.txt.j2 -I splunk:

And similar functionalty using ``diana-cli`` explicitly:

.. code:: bash

   $ diana-cli oget -m signature -f $DIANA_FKEY orthanc: xano-nxst-udyx-oidx \
               dispatch --subsciptions @/subscriptions.yaml \
                        --email-messenger gmail: \
                        --msg_t @/notify.txt.tmpl \
                        --channel_tmpl='$trial-$site' \
               put splunk:

Start The Watcher
~~~~~~~~~~~~~~~~~

Start the automated watcher service:

.. code:: bash

   $ python3 siren.py start-watcher \
                      path:/incoming \
                      orthanc: \
                      -S @/subscriptions.yaml \
                      -E gmail: \
                      -T @/notify.txt.j2 \
                      -I splunk:

This can also be passed directly to a DIANA service container as the
command (use the full path to the script
``/opt/diana/apps/siren/siren.py``, or set the working directory with
the additional argument ``-w /opt/diana/apps/siren``).

Default Shamming
----------------

This shamming and anonymization system works best when fully identified
DICOM metadata is provided as input.

If the patient name (or patient id, if name is missing) and birth date
tags are consistent, the sham id will always send new studies into the
same sham subject jacket and maintain strict temporal offsets. If
patient name and patient id are both missing, the study will be added to
a default subject jacket.

Submitting multiple studies (or indeed multiple series within a study)
with sequential date/times will result in a similarly offset sequence of
sham date/times. The temporal offset is randomized *per patient*, so any
studies added to the default patient jacket will also share the same
offset. The date/time offset is computed in two parts: a long term
offset of months/days, and a short term offset of minutes/seconds. The
sham study *date* will be within +/- 90 days of input date of service,
to preserve approximate patient age and time of year. The study *time*
will be within +/- 90 minutes of service time, to preserve approximate
time of day.

A given accession number (or DICOM UID, if accession number is missing)
will be hashed reproducibly to a unique new sham accession number.
However, if an input accession number is an obviously non-unique string,
like “study 1”, all other studies using that non-unique string will be
assigned to the same sham accession number. In this case, it is
important to add the images to unique sham subject id rather than to the
default subject.

The default shamming and anonymization schema can be modified to meet
specific needs by providing a different replacement map in
```handlers.py`` <handlers.py>`__.

License
-------

MIT
