Unit Tests
==========

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |codecov|

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
.. |codecov| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
