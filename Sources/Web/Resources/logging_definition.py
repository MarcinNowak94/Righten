#Based monstly on https://www.youtube.com/watch?v=9L77QExPmI0
import logging.config
import logging.handlers
import atexit

logfile="E:\Projects\Git\Righten\Sources\Logs\rightenlog.log"
#logfile="/logs/righten/rightenlog.log"


logger = logging.getLogger("righten") #Create non-rootlogger if not exists, 

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    #Filters in case of sensitive data "filters": {},
    "formatters": {
        "simple": {
            "format": "%(actime)s, %(levelname)s, %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        },
        "detailed": {
            "format": "%(asctime)s, %(levelname)s, %(module)s, L%(lineno)d: %(message)s",
            #ISO-8601 timestamp with timezone
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        },
        "json": {
            #replaces 'class' tag
            #FIXME: not recognized
            "()": "RightenJSONFormatter",
            #pass fmt_keys as keyword argument
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
            "stream": "ext://sys.stdout",
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "detailed",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "class": "logging.handlers.FileHandler",
            "level": "Debug",
            #Dumps data as JSON lines file format
            "formatter": "json",
            
            "filename": logfile,
            #Append data to log
            "mode": "a",
            "encoding": "utf_8"
        },
        #For performance reasons - so application execution would not have to wait for log storage each time
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            #FIXME: Somehow 'key error'
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