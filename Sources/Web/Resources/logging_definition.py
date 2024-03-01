#Based monstly on https://www.youtube.com/watch?v=9L77QExPmI0
import atexit
import json
import logging.config
import logging.handlers
from logging import FileHandler
import pathlib
from Resources.rightenlogger import RightenJSONFormatter

#logfile="/logs/righten/rightenlog.jsonl"

logger = logging.getLogger("righten") #Create non-rootlogger if not exists, 

logging_config={
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(actime)s, %(levelname)s, %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        },
        "detailed": {
            "format": "%(asctime)s, %(levelname)s, %(module)s, L%(lineno)d: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "stream": "ext://sys.stdout"
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "detailed",
            "stream": "ext://sys.stderr"
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": [
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