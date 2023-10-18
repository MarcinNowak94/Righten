from flask import Flask
from flask_sqlalchemy import SQLAlchemy
debugmode=True

app=Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///E:\\Projects\\Git\\Righten\\Sources\\web\\RightenWeb\\db\\Righten.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///E:\\Projects\\Git\\Righten\\Sources\\web\\RightenWeb\\db\\Righten_mock.sqlite3'
#TODO: Secure later as per https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure
app.config['SECRET_KEY']="dkmhUYT#U^T#8u286754jd7jGHVSAHGfsa__2" 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db=SQLAlchemy(app)

from RightenWeb import routes
