from RightenWeb import db
from RightenWeb import app
from sqlalchemy import Table, MetaData, create_engine
from sqlalchemy.ext.automap import automap_base

#TODO: Table reflection https://docs.sqlalchemy.org/en/20/tutorial/metadata.html#table-reflection
# OR better
#TODO: Automap https://www.youtube.com/watch?v=UK57IHzSh8I

#engine = create_engine(db, echo=True)
#with app.app_context():
#    Incometable=db.Table("Income",metadata=db.metadata,autoload=True, autoload_with=db.engine)

#TODO: Move it out
with app.app_context():
    Base = automap_base()
    Base.prepare(autoload_with=db.engine, reflect=True)
    Incometable=Base.classes.Income
