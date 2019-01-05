Unit Tests
==========

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |Coverage Status| |Doc Status|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io

Usage
-----

Manually run pytest with coverage and upload to codecov:

::

    $ pip install pytest coverage codecov
    $ PYTHONPATH="./apps/diana-cli" pytest --cov
    $ codecov --token=XXXXXXXXXX

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |Coverage Status| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
.. |Doc Status| image:: https://readthedocs.org/projects/diana/badge/?version=master
   :target: https://diana.readthedocs.io/en/master/?badge=master
