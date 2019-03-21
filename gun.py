import os
import gevent.monkey
gevent.monkey.patch_all()

import multiprocessing

debug = True
loglevel = 'debug'

#debug = False
bind = '172.26.26.131:8993'
#bind = '127.0.0.1:5000'
pidfile = '/mnt/logs/soucangflask/pid/gunicorn.pid'
logfile = '/mnt/logs/soucangflask/log/debug.log'

#启动的进程数
workers = multiprocessing.cpu_count() * 1 
worker_class = 'gunicorn.workers.ggevent.GeventWorker'
