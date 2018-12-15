Manually run pytest with coverage and upload to codecov:

```
$ pip install pytest coverage codecov
$ PYTHONPATH="./apps/diana-cli" pytest --cov
$ codecov --token=XXXXXXXXXX
```