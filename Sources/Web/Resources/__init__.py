#TODO: check https://github.com/BombaMateusz/Remember-NoteAll/blob/main/RINA/__init__.py

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

from Resources.logging_definition import logger, setup_logging
from Resources.rightenlogger import RightenJSONFormatter
#Secure config as per https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure

app=Flask(__name__)

# As per https://www.youtube.com/watch?v=L1h5gRxh8w8
basepath = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basepath, ".env"))

app.config.from_prefixed_env() #Reads FLASK_* from .env and .flaskenv
version="debug_local"
if version=="debug_local":
    app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///E:\\Projects\\Git\\Righten\\Sources\\Database\\Righten_mock.sqlite3' #Local SQLite3

db=SQLAlchemy(app)
bcrypt=Bcrypt(app)

if not app.config['SECRET_KEY']:
    logger.ERROR("No SECRET_KEY set for Flask application!", extra={"action": "Application configuration error", "config": app.config.items()})
    raise ValueError("No SECRET_KEY set for Flask application")

#logfile="/logs/righten/rightenlog.jsonl"

logfile_tmp="E:\\Projects\\Git\\Righten\\Sources\\Logs\\rightenlog.jsonl"
app.config["LOG_FILE"] = "E:\\Projects\\Git\\Righten\\Sources\\Logs\\rightenlog.jsonl" if version=="debug_local" else "/logs/rightenlog.jsonl"
setup_logging(app.config["LOG_FILE"])
# Print all variables if in debug mode
logger.debug("Righten Application started", extra={"action": "Application started", "config": app.config.items()})

from Resources import routes