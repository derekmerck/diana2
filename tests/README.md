Diana Tests
==================

Derek Merck  
<derek_merck@brown.edu>  
Rhode Island Hospital and Brown University  
Providence, RI  

[![Build Status](https://travis-ci.org/derekmerck/diana2.svg?branch=master)](https://travis-ci.org/derekmerck/diana2)
[![codecov](https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg)](https://codecov.io/gh/derekmerck/diana2)

Source: <https://www.github.com/derekmerck/diana2>  
Documentation: <https://diana.readthedocs.io>

Manually run pytest with coverage and upload to codecov:

```
$ pip install pytest coverage codecov
$ PYTHONPATH="./apps/diana-cli" pytest --cov
$ codecov --token=XXXXXXXXXX
```