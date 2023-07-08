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

#NICE-TO-HAVE: create factory function to recreate full schema as classes
with app.app_context():
    Base = automap_base()
    Base.prepare(autoload_with=db.engine, reflect=True)
    Income=Base.classes.Income
    Bills=Base.classes.Bills
    ProductTypes=Base.classes.ProductTypes
    Products=Base.classes.Products
    Expenditures=Base.classes.Expenditures
    #TODO: temporary table, can get rid of it if data added to this table is strictly verified
    Expenditures_transitory=Base.classes.Expenditures

    Expenditures_Enriched=Table("Expenditures_Enriched", db.metadata, autoload_with=db.engine)
    MonthlyBilance=Table("MonthlyBilance", db.metadata, autoload_with=db.engine)
    MonthlyBills=Table("MonthlyBills", db.metadata, autoload_with=db.engine)
    MonthlyExpenditures=Table("MonthlyExpenditures", db.metadata, autoload_with=db.engine)
    MonthlyIncome=Table("MonthlyIncome", db.metadata, autoload_with=db.engine)
    Monthly_Expenditures_by_Type=Table("Monthly_Expenditures_by_Type", db.metadata, autoload_with=db.engine)
    Monthly_common_products=Table("Monthly_common_products", db.metadata, autoload_with=db.engine)
    ProductSummary=Table("ProductSummary", db.metadata, autoload_with=db.engine)
    ProductTypeSummary=Table("ProductTypeSummary", db.metadata, autoload_with=db.engine)