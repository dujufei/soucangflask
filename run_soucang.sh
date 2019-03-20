nohup gunicorn -c gun.py soucangflask:app > err.log 2>&1 &
