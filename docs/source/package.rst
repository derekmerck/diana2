``python-diana``
================

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |Coverage Status| |Doc Status|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io
| Image: https://cloud.docker.com/repository/docker/derekmerck/diana2

Installation
------------

.. code:: bash

   $ pip install git+https://github.com/derekmerck/diana2/diana2/package

The ``diana-plus`` extras package relies on scipy, tensorflow, keras,
and other computational packages.

.. code:: bash

   $ pip install git+https://github.com/derekmerck/diana2/diana2/package[plus]

Dependencies
------------

Vanilla
~~~~~~~

-  `attrs <http://www.attrs.org/en/stable/>`__
-  `bs4 <https://beautiful-soup-4.readthedocs.io/en/latest/>`__
-  `docker <https://docker-py.readthedocs.io/en/stable/>`__
-  `numpy <http://www.numpy.org>`__
-  `pydicom <https://pydicom.github.io>`__
-  `pyyaml <https://pyyaml.org>`__
-  `pillow <https://pillow.readthedocs.io/en/stable/>`__
-  `python-dateutil <https://dateutil.readthedocs.io/en/stable/>`__
-  `redis <https://github.com/andymccurdy/redis-py/>`__
-  `requests <http://docs.python-requests.org/en/master/>`__
-  `watchdog <https://pythonhosted.org/watchdog/>`__

Plus
~~~~

-  `cython <https://cython.org>`__
-  `keras <https://keras.io>`__
-  `scikit-learn <https://scikit-learn.org/stable/>`__
-  `scipy <https://www.scipy.org>`__
-  `tensorflow <https://www.tensorflow.org>`__

Notes
-----

See `guid <./guid.md>`__ for documentation of the GUID and pseudo-id
generation algorithm.

License
-------

MIT

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |Coverage Status| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
.. |Doc Status| image:: https://readthedocs.org/projects/diana/badge/?version=master
   :target: https://diana.readthedocs.io/en/master/?badge=master
