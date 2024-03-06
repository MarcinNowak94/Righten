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
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///E:\\Projects\\Git\\Righten\\Sources\\Database\\Righten_mock.sqlite3"
    if app.config["ENV"] == "development"
    else "postgresql+psycopg2://postgres:postgres@rightendb:5432/RightenDB"
    )

db=SQLAlchemy(app)
bcrypt=Bcrypt(app)

if not app.config["SECRET_KEY"]:
    logger.ERROR(
        "No SECRET_KEY set for Flask application!",
        extra={
            "action": "Application configuration error",
            "config": app.config.items()
            }
        )
    raise ValueError("No SECRET_KEY set for Flask application")

app.config["CERT_FILE"] = (
    "E:\\Projects\\Git\\Righten\\Sources\\Web\\cert.pem"
    if app.config["ENV"] == "development"
    else "/righten/cert.pem")
app.config["KEY_FILE"] = (
    "E:\\Projects\\Git\\Righten\\Sources\\Web\\key.pem"
    if app.config["ENV"] == "development"
    else "/righten/key.pem")

app.config["LOG_FILE"] = (
    "E:\\Projects\\Git\\Righten\\Sources\\Logs\\rightenlog.jsonl"
    if app.config["ENV"] == "development"
    else "/logs/rightenlog.jsonl"
    )

setup_logging(app.config["LOG_FILE"])
# Print all variables if in debug mode
logger.debug(
    "Righten Application started",
    extra={
        "action": "Application started",
        "config": app.config.items()
        }
    )

from Resources import routes