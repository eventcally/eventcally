import multiprocessing
import os

# Bind
port = os.getenv(
    "PORT", "5000"
)  # No Prefix here because some hosting provider use 'PORT'
bind = os.getenv("GUNICORN_BIND", f"0.0.0.0:{port}")

# Workers
workers = multiprocessing.cpu_count() * 2 + 1

# Logging
capture_output = True
accesslog = os.getenv("GUNICORN_ACCESS_LOG", None)
access_log_format = os.getenv(
    "GUNICORN_ACCESS_LOG_FORMAT",
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"',
)
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
logconfig = os.getenv("GUNICORN_LOG_CONFIG", None)
