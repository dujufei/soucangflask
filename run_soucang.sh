nohup gunicorn -c gun.py soucangflask:app > /mnt/data/soucangflask/error.log 2>&1 &
