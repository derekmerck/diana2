`python-diana`
==================

Derek Merck  
<derek.merck@ufl.edu>  
University of Florida and Shands Hospital
Gainesville, FL  

[![Build Status](https://travis-ci.org/derekmerck/diana2.svg?branch=master)](https://travis-ci.org/derekmerck/diana2)
[![Coverage Status](https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg)](https://codecov.io/gh/derekmerck/diana2)
[![Doc Status](https://readthedocs.org/projects/diana/badge/?version=master)](https://diana.readthedocs.io/en/master/?badge=master)

Source: <https://www.github.com/derekmerck/diana2>  
Documentation: <https://diana.readthedocs.io>  
Image:  <https://cloud.docker.com/repository/docker/derekmerck/diana2>


Installation
---------------

```bash
$ pip install git+https://github.com/derekmerck/diana2/diana2/package
```

The `diana-plus` extras package relies on scipy, tensorflow, keras, and other computational packages.

```bash
$ pip install git+https://github.com/derekmerck/diana2/diana2/package[plus]
```


Dependencies
-------------

### Vanilla

- [attrs](http://www.attrs.org/en/stable/)
- [bs4](https://beautiful-soup-4.readthedocs.io/en/latest/)
- [docker](https://docker-py.readthedocs.io/en/stable/)
- [numpy](http://www.numpy.org)
- [pydicom](https://pydicom.github.io)
- [pyyaml](https://pyyaml.org)
- [pillow](https://pillow.readthedocs.io/en/stable/)
- [python-dateutil](https://dateutil.readthedocs.io/en/stable/)
- [redis](https://github.com/andymccurdy/redis-py/)
- [requests](http://docs.python-requests.org/en/master/)
- [watchdog](https://pythonhosted.org/watchdog/)

### Plus

- [cython](https://cython.org)
- [keras](https://keras.io)
- [scikit-learn](https://scikit-learn.org/stable/)
- [scipy](https://www.scipy.org)
- [tensorflow](https://www.tensorflow.org)


License
---------------

MIT