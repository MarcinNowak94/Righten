#Based monstly on https://www.youtube.com/watch?v=9L77QExPmI0
import atexit
import json
import logging          #FileHandler lives here
import logging.config
import logging.handlers
import pathlib
from Resources.rightenlogger import RightenJSONFormatter

#logfile="/logs/righten/rightenlog.jsonl"
logfile="E:\\Projects\\Git\\Righten\\Sources\\Logs\\rightenlog.jsonl"
            
logger = logging.getLogger("righten") #Create non-rootlogger if not exists, 

logging_config={
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s, %(levelname)s, %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        },
        "detailed": {
            "format": "%(asctime)s, %(levelname)s, %(module)s, L%(lineno)d: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        },
        "json": {
            "()": RightenJSONFormatter,
            "fmt_keys": {
                "level": "levelname",
                "message": "message",
                "timestamp": "timestamp",
                "logger": "name",
                "module": "module",
                "function": "funcName",
                "line": "lineno",
                "thread_name": "threadName"
            }
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "detailed",
            "stream": "ext://sys.stderr"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "json",            
            "filename": logfile,
            "mode": "a",
            "encoding": "utf_8"
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": [
                "file",
                "stdout"
            ],
            "respect_handler_level": True
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["queue_handler"]
        }
    }
}

def setup_logging():
    logging.config.dictConfig(config=logging_config)
    queue_handler=logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

def setup_logging_v2():
    config_file = pathlib.Path("E:\Projects\Git\Righten\Sources\Web\Resources\logging_config.json")
    with open(config_file) as file:
        config=json.load(file)
    logging.config.dictConfig(config)

    queue_handler=logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)