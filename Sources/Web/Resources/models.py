from Resources import db, app
from sqlalchemy import Table
from sqlalchemy.ext.automap import automap_base

#TODO: Table reflection https://docs.sqlalchemy.org/en/20/tutorial/metadata.html#table-reflection
# OR better
#TODO: Automap https://www.youtube.com/watch?v=UK57IHzSh8I

#NICE-TO-HAVE: create factory function to recreate full schema as classes
#Currently 'public' schema, need to figure out how to make and access separate schemas for each user
#https://stackoverflow.com/questions/2342999/postgres-is-there-a-way-to-tie-a-user-to-a-schema
with app.app_context():
    Base = automap_base() 
    Base.prepare(autoload_with=db.engine, reflect=True)
    #Tables
    Income=Base.classes.Income
    Bills=Base.classes.Bills
    ProductTypes=Base.classes.ProductTypes
    Products=Base.classes.Products
    Expenditures=Base.classes.Expenditures
    #TODO: temporary table, can get rid of it if data added to this table is strictly verified
    ExpendituresTransitory=Base.classes.Expenditures
    Users=Base.classes.Users
    #FIXME: Figure out why this does not work
    UserSettings=Base.classes.UserSettings

    #Views
    ExpendituresEnriched=Table("ExpendituresEnriched", db.metadata, autoload_with=db.engine)
    MonthlyBilance=Table("MonthlyBilance", db.metadata, autoload_with=db.engine)
    MonthlyBills=Table("MonthlyBills", db.metadata, autoload_with=db.engine)
    MonthlyExpenditures=Table("MonthlyExpenditures", db.metadata, autoload_with=db.engine)
    MonthlyIncome=Table("MonthlyIncome", db.metadata, autoload_with=db.engine)
    MonthlyExpendituresbyType=Table("MonthlyExpendituresbyType", db.metadata, autoload_with=db.engine)
    MonthlyProducts=Table("MonthlyProducts", db.metadata, autoload_with=db.engine)
    MonthlyCommonProducts=Table("MonthlyCommonProducts", db.metadata, autoload_with=db.engine)
    ProductSummary=Table("ProductSummary", db.metadata, autoload_with=db.engine)
    TypeSummary=Table("TypeSummary", db.metadata, autoload_with=db.engine)
    BillsSummary=Table("BillsSummary", db.metadata, autoload_with=db.engine)
    MonthlyIncomeByType=Table("MonthlyIncomeByType", db.metadata, autoload_with=db.engine)
    IncomeSummary=Table("IncomeSummary", db.metadata, autoload_with=db.engine)
    IncomeSummaryByType=Table("IncomeSummaryByType", db.metadata, autoload_with=db.engine)
    TotalIncomeByType=Table("TotalIncomeByType", db.metadata, autoload_with=db.engine)
    MonthlyBillsByMedium=Table("MonthlyBillsByMedium", db.metadata, autoload_with=db.engine)
    Top10ProductTypesMonthly = Table("Top10ProductTypesMonthly", db.metadata, autoload_with=db.engine)
    Top10ProductsMonthly = Table("Top10ProductsMonthly", db.metadata, autoload_with=db.engine)
    MonthlyBilanceSingle = Table("MonthlyBilanceSingle", db.metadata, autoload_with=db.engine)
    MonthlySpending = Table("MonthlySpending", db.metadata, autoload_with=db.engine)

#Map used to generalize functions - to refer to table by objectname alone
tables={
    "Income": Income,
    "Bills" : Bills,
    "ProductTypes": ProductTypes,
    "Products" : Products,
    "Expenditures" : Expenditures,
    "ExpendituresTransitory" : ExpendituresTransitory,
    "Users" : Users,
    #"UserSettings" : UserSettings,

    "ExpendituresEnriched" : ExpendituresEnriched,
    "MonthlyBilance" : MonthlyBilance,
    "MonthlyBills" : MonthlyBills,
    "MonthlyExpenditures" : MonthlyExpenditures,
    "MonthlyIncome" : MonthlyIncome,
    "MonthlyExpendituresbyType" : MonthlyExpendituresbyType,
    "MonthlyProducts" : MonthlyProducts,
    "MonthlyCommonProducts" : MonthlyCommonProducts,
    "ProductSummary" : ProductSummary,
    "TypeSummary" : TypeSummary,
    "BillsSummary" : BillsSummary,
    "MonthlyIncomeByType" : MonthlyIncomeByType,
    "IncomeSummary" : IncomeSummary,
    "IncomeSummaryByType" : IncomeSummaryByType,
    "TotalIncomeByType" : TotalIncomeByType,
    "MonthlyBillsByMedium" : MonthlyBillsByMedium,
    "Top10ProductTypesMonthly" : Top10ProductTypesMonthly,
    "Top10ProductsMonthly" : Top10ProductsMonthly,
    "MonthlyBilanceSingle" : MonthlyBilanceSingle,
    "MonthlySpending" : MonthlySpending
}