from Resources import db, app
from sqlalchemy import Table
from sqlalchemy.ext.automap import automap_base


#NICE-TO-HAVE: create factory function to recreate full schema as classes
#Currently 'public' schema, need to figure out how to make and access separate schemas for each user
#https://stackoverflow.com/questions/2342999/postgres-is-there-a-way-to-tie-a-user-to-a-schema
with app.app_context():
    # Currently all objects are in 'public' schema
    Base = automap_base()
    Base.prepare(autoload_with=db.engine, reflect=True)

    # Tables
    # Automapping creates class equivalent to records for table interaction, as per: 
    #   https://www.youtube.com/watch?v=UK57IHzSh8I
    #   https://docs.sqlalchemy.org/en/20/orm/extensions/automap.html#module-sqlalchemy.ext.automap

    Income = Base.classes.Income
    Bills = Base.classes.Bills
    ProductTypes = Base.classes.ProductTypes
    Products = Base.classes.Products
    Expenditures = Base.classes.Expenditures
    Users = Base.classes.Users

    #Views
    ExpendituresEnriched = Table("ExpendituresEnriched", db.metadata, autoload_with=db.engine)
    MonthlyBilance = Table("MonthlyBilance", db.metadata, autoload_with=db.engine)
    MonthlyExpendituresbyType = Table("MonthlyExpendituresbyType", db.metadata, autoload_with=db.engine)
    MonthlyProducts = Table("MonthlyProducts", db.metadata, autoload_with=db.engine)
    MonthlyCommonProducts = Table("MonthlyCommonProducts", db.metadata, autoload_with=db.engine)
    MonthlyProductTypes = Table("MonthlyProductTypes", db.metadata, autoload_with=db.engine)
    ProductSummary = Table("ProductSummary", db.metadata, autoload_with=db.engine)
    TypeSummary = Table("TypeSummary", db.metadata, autoload_with=db.engine)
    BillsSummary = Table("BillsSummary", db.metadata, autoload_with=db.engine)
    MonthlyIncomeByType = Table("MonthlyIncomeByType", db.metadata, autoload_with=db.engine)
    IncomeSummary = Table("IncomeSummary", db.metadata, autoload_with=db.engine)
    IncomeSummaryByType = Table("IncomeSummaryByType", db.metadata, autoload_with=db.engine)
    MonthlyBillsByMedium = Table("MonthlyBillsByMedium", db.metadata, autoload_with=db.engine)
    Top10ProductTypesMonthly = Table("Top10ProductTypesMonthly", db.metadata, autoload_with=db.engine)
    Top10ProductsMonthly = Table("Top10ProductsMonthly", db.metadata, autoload_with=db.engine)
    MonthlySpending = Table("MonthlySpending", db.metadata, autoload_with=db.engine)
    UnnecessaryProductsBought = Table("UnnecessaryProductsBought", db.metadata, autoload_with=db.engine)
    Statistics = Table("Statistics", db.metadata, autoload_with=db.engine)

# Maps used to generalize functions - to refer to table by objectname alone
tables = {
    "Income": Income,
    "Bills" : Bills,
    "ProductTypes": ProductTypes,
    "Products" : Products,
    "Expenditures" : Expenditures,
    "Users" : Users
}

views = {
    "ExpendituresEnriched" : ExpendituresEnriched,
    "MonthlyBilance" : MonthlyBilance,
    "MonthlyExpendituresbyType": MonthlyExpendituresbyType,
    "MonthlyProducts" : MonthlyProducts,
    "MonthlyCommonProducts" : MonthlyCommonProducts,
    "MonthlyProductTypes" : MonthlyProductTypes,
    "ProductSummary" : ProductSummary,
    "TypeSummary" : TypeSummary,
    "BillsSummary" : BillsSummary,
    "MonthlyIncomeByType" : MonthlyIncomeByType,
    "IncomeSummary" : IncomeSummary,
    "IncomeSummaryByType" : IncomeSummaryByType,
    "MonthlyBillsByMedium" : MonthlyBillsByMedium,
    "Top10ProductTypesMonthly" : Top10ProductTypesMonthly,
    "Top10ProductsMonthly" : Top10ProductsMonthly,
    "MonthlySpending" : MonthlySpending,
    "UnnecessaryProductsBought" : UnnecessaryProductsBought,
    "Statistics" : Statistics
}

# TODO: add proper type validation - has to be 'YYYY-MM' or better yet datetime 'YYYY-MM-01' 
class RangeMonth:
    def __init__(
            self, 
            beginning: str, 
            end: str
            ):
        self.beginning = beginning
        self.end = end

# TODO: add proper type validation - has to be 'YYYY-MM-DD'
class RangeDate:
    def __init__(
            self, 
            beginning: str, 
            end: str
            ):
        self.beginning = beginning
        self.end = end