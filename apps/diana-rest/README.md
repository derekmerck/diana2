Diana-REST
=================

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


Simple API-first REST server for Diana. 

Usage
-------------

```bash
$ export DIANA_SERVICES="${DIANA_DIR}/tests/resources/test_services.yml"
$ python3 diana-rest.py &
$ curl -X GET "http://localhost:8080/v1.0/endpoint"
{
  "orthanc": "Not Ready",
  "orthanc_bad": "Not Ready",
  "redis": "Not Ready",
  "redis_bad": "Not Ready",
  "redis_p": "Not Ready"
}
```

See <http://localhost:8080/ui> for a Swagger API dashboard.


Dependencies
-------------

- [Connexion](https://connexion.readthedocs.io/en/latest/index.html)


License
-------------

MIT


