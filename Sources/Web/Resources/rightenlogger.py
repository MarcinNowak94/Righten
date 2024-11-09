import datetime as dt
import json
import logging
#from typing import override

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName"
}

class RightenJSONFormatter(logging.Formatter):
    """Righten log formatter, processess data into JSON.   

    Arguments:
        :logging.Formatter: -- base class
    """

    def __init__(
            self,
            *,
            fmt_keys: dict[str, str] | None=None
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}
    
    #@override
    def format(self, record: logging.LogRecord) -> str:
        """Formats record into JSON formatted string"""

        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)
    
    def _prepare_log_dict(self, record: logging.LogRecord):
        """Prepares log dictionary

        Arguments:
            :record: -- log record to process 

        Returns:
            Message formatted as JSON dictionary
        """

        basic_fields={
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
            "message": record.getMessage()
        }
        
        if record.exc_info is not None:
            basic_fields["exc_info"]=self.formatException(record.exc_info)
        
        if record.stack_info is not None:
            basic_fields["stack_info"]=self.formatStack(record.stack_info)
        
        message = {
            key: msg_val
            if (msg_val := basic_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(basic_fields)

        #Service added superflous fields 
        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key]=val

        return message

class NonErrorFilter(logging.Filter):
    """Custom filter, returns true if message should be processed
    
    Extra stuff, unused but can be in future - can be used for sanitizing, censoring and altering data 

    Arguments:
        :logging.Filter: -- base class

    Returns:
        :true: -- if log should be processed
        :false: -- if record should be dropped
    """
    #@override
    
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        """Returns all log records except ERROR

        Arguments:
            :record: -- log record to process

        Returns:
            :true: -- if log should be processed
            :false: -- if record should be dropped
        """
        return record.levelno <=logging.INFO