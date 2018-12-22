Library API
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


Dixel Endpoint APIs
------------------------------------

Orthanc
...................

.. automodule:: diana.apis.orthanc
   :members:

Montage
...................

.. automodule:: diana.apis.montage
   :members:

DcmDir
...................

.. automodule:: diana.apis.dcmdir
   :members:

Redis
...................

.. automodule:: diana.apis.redis
   :members:


Daemon APIs
------------------------------------


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
