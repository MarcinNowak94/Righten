from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from Resources.logging_definition import logger, setup_logging
from Resources.rightenlogger import RightenJSONFormatter
#Secure config as per https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure
#https://www.youtube.com/watch?v=L1h5gRxh8w8
import os
from dotenv import load_dotenv
setup_logging()
logger.info("Logging started")
basepath = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basepath, '.env'))

app=Flask(__name__)
app.config.from_prefixed_env() #Reads FLASK_* from .env and .flaskenv
version="debug_local"
if version=="debug_local":
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///E:\\Projects\\Git\\Righten\\Sources\\Database\\Righten_mock.sqlite3' #Local SQLite3

db=SQLAlchemy(app)
bcrypt=Bcrypt(app)

if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application")
logger.info("Application setup finished")

#Print all variables if in debug mode
if (app.config['DEBUG']):
    for key, variable in app.config.items():
        value=str(variable)
        print("{:<35} {:<10}".format(key, value))


from Resources import routes