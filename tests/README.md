Unit Tests
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

Usage
------------------

Manually run pytest with coverage and upload to codecov:

```
$ pip install pytest coverage codecov
$ PYTHONPATH="./apps/diana-cli" pytest --cov
$ codecov --token=XXXXXXXXXX
```