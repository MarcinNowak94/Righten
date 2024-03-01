#Based monstly on https://www.youtube.com/watch?v=9L77QExPmI0
import atexit
import json
import logging.config
import logging.handlers
import pathlib
from Resources.rightenlogger import RightenJSONFormatter

#logfile="/logs/righten/rightenlog.jsonl"

logger = logging.getLogger("righten") #Create non-rootlogger if not exists, 

def setup_logging():
    config_file = pathlib.Path("E:\Projects\Git\Righten\Sources\Web\Resources\logging_config.json")
    with open(config_file) as file:
        config=json.load(file)
    logging.config.dictConfig(config)

    queue_handler=logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)