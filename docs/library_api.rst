Python API
====================================

.. contents::
   :local:

Dixel API
------------------------------------

.. autoclass:: diana.dixel.Dixel
   :members:

.. autoclass:: diana.dixel.DixelView
   :members:
   :undoc-members:

Dixels also implement the Serializable interface.

.. autoclass:: diana.utils.endpoint.Serializable
   :members:
   :undoc-members:


Full-Dixel Endpoint APIs
------------------------------------

All Dixel Endpoints implement the Serializable and Endpoint interfaces.

Diana-CLI provides shortcuts for calling basic endpoint functions (put, get, find, delete) on arbitrary services.

.. autoclass:: diana.utils.endpoint.Endpoint
   :members:
   :undoc-members:

Orthanc
...................

.. autoclass:: diana.apis.Orthanc
   :members:

Osimis-flavor Orthanc provides additional services including a webviewer and annotations.  Importing osimis_extras extends the Orthanc base-class.

.. automodule:: diana.apis.osimis_extras
   :members:

ProxiedDicom
...................

.. autoclass:: diana.apis.ProxiedDicom
   :members:

DcmDir
...................

.. autoclass:: diana.apis.DcmDir
   :members:

Dixel-Summary Endpoint APIs
------------------------------------

Montage
...................

.. autoclass:: diana.apis.Montage
   :members:


CsvFile
...................

.. autoclass:: diana.apis.CsvFile
   :members:

Redis
...................

.. autoclass:: diana.apis.Redis
   :members:

Splunk
...................

.. autoclass:: diana.apis.Splunk
   :members:


Daemon APIs
------------------------------------

Diana daemons are higher order constructs that combine multiple APIs into pipelines.

Routing
...................

A routing deamon may be created by instantiating a Watcher with ObservableEndpoitns and adding Dixel routing rules.

Diana-CLI provides a shortcut for creating a watcher service and attaching observables and triggers.

.. autoclass:: diana.utils.endpoint.Watcher
   :members:
   :undoc-members:

Observables implement the Observable API.

.. autoclass:: diana.utils.endpoint.ObservableMixin
   :members:
   :undoc-members:

.. autoclass:: diana.apis.ObservableOrthanc
   :members:
   :undoc-members:

.. autoclass:: diana.apis.ObservableProxiedDicom
   :members:
   :undoc-members:

.. autoclass:: diana.apis.ObservableDcmDir
   :members:
   :undoc-members:

Dixel routes are instantiated with (source, dest, handler) tuples and attached to the Watcher's routing table.

.. automodule:: diana.daemons.routes
   :members:
   :undoc-members:

Mock Data Generation
....................

Reasonably well-formed DICOM header data for mock studies can be generated on a site, service, or device basis.

Diana-CLI provides a shortcut for defining and running a mock service.

.. automodule:: diana.daemons.mock_site
   :members:
   :undoc-members:

.. automodule:: diana.dixel.mock_dixel
   :members:
   :undoc-members:


DICOM Utilities
------------------------------------

.. autoclass:: diana.utils.dicom.DicomLevel
   :members:
   :undoc-members:

.. autofunction:: diana.utils.dicom.dicom_simplify

.. autoclass:: diana.utils.dicom.DicomUIDMint
   :members:


GUID Utilities
------------------------------------

.. autoclass:: diana.utils.guid.GUIDMint
   :members:
   :undoc-members:



REST Gateway Utilities
------------------------------------

Orthanc
...................

.. autoclass:: diana.utils.gateways.Orthanc
   :members:
   :undoc-members:

.. autofunction:: diana.utils.gateways.orthanc_id

Montage
...................

.. autoclass:: diana.utils.gateways.Montage
   :members:
   :undoc-members:

Splunk
...................

.. autoclass:: diana.utils.gateways.Splunk
   :members:
   :undoc-members:


File Gateway Utilities
------------------------------------

.. autoclass:: diana.utils.gateways.DcmFileHandler
   :members:
   :undoc-members:

.. autoclass:: diana.utils.gateways.TextFileHandler
   :members:
   :undoc-members:

.. autoclass:: diana.utils.gateways.ImageFileHandler
   :members:
   :undoc-members:
