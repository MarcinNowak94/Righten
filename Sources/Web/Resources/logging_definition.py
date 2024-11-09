#Based monstly on https://www.youtube.com/watch?v=9L77QExPmI0
import atexit
import json
import logging          #FileHandler lives here
import logging.config
import logging.handlers
import pathlib
from Resources.rightenlogger import RightenJSONFormatter

     
logger = logging.getLogger("righten") #Create non-rootlogger if not exists, 

def setup_logging(logfile: str) -> None:
    """Setup logging configuration with loggers, handlers and filters

    Arguments:
        :logfile: -- logfile destination
    """
    
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

    logging.config.dictConfig(config=logging_config)
    queue_handler=logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

def setup_logging_JSON_config(config_file_path: str):
    """Setup logging configuration with loggers, handlers and filters from json config file

    Arguments:
        :logfile: -- logfile destination
    # FIXME: loading config from file produces error - RightenJSONFormatter is not recognized
    #current file: E:\Projects\Git\Righten\Sources\Web\Resources\logging_config.json
    """
    
    config_file = pathlib.Path(config_file_path)
    
    with open(config_file) as file:
        config=json.load(file)
    logging.config.dictConfig(config)

    queue_handler=logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)