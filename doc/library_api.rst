Python-Diana API
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

.. autoclass:: diana.utils.endpoint.Endpoint
   :members:
   :undoc-members:

Orthanc
...................

.. autoclass:: diana.apis.Orthanc
   :members:

.. automodule:: diana.apis.osimis_extras
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

.. autoclass:: diana.apis.ObservableDcmDir
   :members:
   :undoc-members:

.. automodule:: diana.daemons.routes
   :members:
   :undoc-members:

Mock Data Generation
....................

.. automodule:: diana.daemons.mock_site
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



Gateway Utilities
------------------------------------

Pythonic interfaces to REST APIs and file structures.

Orthanc
...................

.. autoclass:: diana.utils.gateways.requesters.orthanc.Orthanc
   :members:
   :undoc-members:

.. autofunction:: diana.utils.gateways.requesters.orthanc.orthanc_id

Montage
...................

.. autoclass:: diana.utils.gateways.requesters.montage.Montage
   :members:
   :undoc-members:
