nohup gunicorn -c gun.py soucangflask:app > /mnt/logs/soucangflask/log/error.log 2>&1 &
