### Setup

install required packages
```python
pip install -r requirements.txt
```

run celery task pool
```shell
celery -A app.celery worker --loglevel=info 
```

run python project
```shell
python app.py
```

run python project code in productive mode
* Note: gunicorn and gevent are required
```shell
gunicorn -w 4 -b 0.0.0.0:8000 app:app --worker-class=gevent
```