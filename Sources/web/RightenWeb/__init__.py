from flask import Flask
from flask_sqlalchemy import SQLAlchemy
debugmode=True

app=Flask(__name__)

from RightenWeb import routes
