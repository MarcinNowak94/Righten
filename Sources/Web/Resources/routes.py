from Resources import app
from Resources import db
from flask import render_template, flash, redirect, url_for, request
from Resources.models import *
from Resources.forms import *
from sqlalchemy import delete, union_all, func
from datetime import date
import json
#NICE-TO-HAVE: Add event logging

#https://stackoverflow.com/questions/63278737/object-of-type-decimal-is-not-json-serializable
#Dumping decimal data
from decimal import Decimal
class DecimalEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Decimal):
      return str(obj)
    return json.JSONEncoder.default(self, obj)

def addtodb(entry):
    try:
        db.session.add(entry)
        db.session.commit()
        flash("Data added", "success")
    except Exception as error:
        print(error)
        db.session.flush()
        flash("Data not added", "error")

def createchartdataset(dbdata, fill="false"):
    months=[]
    sets={}

    #Build distinct month list for labels and type dictionaries for data 
    for Month, Amount, Type in dbdata:
        if Month not in months: months.append(Month)
        if Type not in sets: sets[Type]=[]

    #Fill type dictionaries with amount or 0 
    for Month, Amount, Type in dbdata:
        for set in sets:
            if not Type==set:
                sets[set].append({"x": Month, "y": 0})
            else:
                sets[set].append({"x": Month, "y": Amount})

    dataset=[]
    for set in sets:
        dataset.append({"label": set, "data": sets[set], "fill": fill})

    return dataset

#As per https://stackoverflow.com/questions/14277067/redirect-back-in-flask
def redirect_url(default="/"):
    return request.args.get("next") or \
           request.referrer or \
           url_for(default)

@app.route("/")
def index():
    return render_template('index.html', title="Main apage");

@app.route("/layout")
def layout():
    return render_template("layout.html")

@app.route("/incomesummary")
def incomesummary():
    IncomeSummarydata=db.session.query(TotalIncomeByType).all()
    incometypesummary=[]
    incometypes=[]
    Summary = db.session.query(IncomeSummary).all()
    for sum, type in IncomeSummarydata:
        incometypesummary.append(sum)
        incometypes.append(type)

    IncomeOverTime=db.session.query(MonthlyIncome).all()
    monthlyincomedata=[]
    for Month, Amount in IncomeOverTime:
        monthlyincomedata.append({"x": Month, "y": Amount})

    IncomeTypesByTime=db.session.query(MonthlyIncomeByType).all()
    IncomeTypesByTimeDataset=createchartdataset(IncomeTypesByTime)

    return render_template("incomesummary.html",
                           title="Income",
                           IncomeSummarydata=json.dumps(incometypesummary, cls=DecimalEncoder),
                           IncomeSummarylabels=json.dumps(incometypes, cls=DecimalEncoder),
                           MonthlyIncome=json.dumps(monthlyincomedata, cls=DecimalEncoder),
                           IncomeTypesByTimeDataset=json.dumps(IncomeTypesByTimeDataset, cls=DecimalEncoder),
                           Summary=Summary
                           )

@app.route("/billssummary")
def billssummary():
    BillsTypeAmounts=[]
    BillsTypes=[]
    Summary = db.session.query(BillsSummary).all()
    for Medium, Amount in db.session.query(BillsSummary.columns.Medium,
                                           BillsSummary.columns.Amount)\
                                            .order_by(BillsSummary.columns.Amount.desc())\
                                                .all():
        BillsTypeAmounts.append(Amount)
        BillsTypes.append(Medium)

    MonthlyBillsData=[]
    for Month, Amount in db.session.query(MonthlyBills).all():
        MonthlyBillsData.append({"x": Month, "y":Amount})
    
    BillsTypespermonth=db.session.query(MonthlyBillsByMedium).all();
    BillsTypesData=createchartdataset(BillsTypespermonth)

    return render_template("billssummary.html",
                           title="Bills",
                           BillsTypeAmounts=json.dumps(BillsTypeAmounts, cls=DecimalEncoder),
                           BillsTypes=json.dumps(BillsTypes, cls=DecimalEncoder),
                           MonthlyBillsData=json.dumps(MonthlyBillsData, cls=DecimalEncoder),
                           BillsTypesData=json.dumps(BillsTypesData, cls=DecimalEncoder),
                           Summary=Summary
                           )

#TODO: Add product picker and corresponding graph
#TODO: Add type picker and corresponding graph
#TODO: Add pie chart by 'Necessary'
#TODO: Organize displays by Amount descending
@app.route("/expendituressummary")
def expendituressummary():
    ExpendituresSummarydata=db.session.query(TypeSummary.columns.Type,
                                             TypeSummary.columns.Amount)\
                                                .order_by(TypeSummary.columns.Amount.desc()).all()
    ExpendituresSummaryData=[]
    ExpendituresSummaryTypes=[]
    for Type, Amount in ExpendituresSummarydata:
        ExpendituresSummaryData.append(Amount)
        ExpendituresSummaryTypes.append(Type)

    ExpendituresOverTime=db.session.query(MonthlyExpenditures).all()
    MonthlyExpendituresData=[]
    for Month, Amount in ExpendituresOverTime:
        MonthlyExpendituresData.append({"x":Month,"y":Amount})

    TopTypeExpendituresData=db.session.query(Top10ProductTypesMonthly).all();
    TopTypeExpenditures=createchartdataset(TopTypeExpendituresData, "true")

    TopProductsChartData=db.session.query(Top10ProductsMonthly).all();
    TopProductsExpenditures=createchartdataset(TopProductsChartData, "true")

    return render_template("expendituressummary.html",
                           title="Expenditures",
                           ExpendituresSummaryData=json.dumps(ExpendituresSummaryData, cls=DecimalEncoder),
                           ExpendituresSummaryTypes=json.dumps(ExpendituresSummaryTypes, cls=DecimalEncoder), 
                           MonthlyExpenditures=json.dumps(MonthlyExpendituresData, cls=DecimalEncoder),
                           TopTypeExpenditures=json.dumps(TopTypeExpenditures, cls=DecimalEncoder),
                           TopProductsExpenditures=json.dumps(TopProductsExpenditures, cls=DecimalEncoder)
                           )

#TODO: Financial posture
#TODO: add average income year to date
@app.route("/finances")
def finances():
    BilanceData=db.session.query(MonthlyBilanceSingle).all();
    Bilance=[]
    Breakeven=[]
    BilanceSet=[]
    #Adding breakeven line 
    for Month, Amount in BilanceData:
        Bilance.append({"x":Month,"y":Amount})
        Breakeven.append({"x":Month,"y":0})

    sets={"Bilance":Bilance, "Breakeven":Breakeven}
    for set in sets:
        BilanceSet.append({"label": set, "data": sets[set]})
    
    BilanceSources=db.session.query(MonthlyBilance).all()
    BilanceSourcesData=createchartdataset(BilanceSources, "true")

    BilanceTotal=db.session.query(MonthlyBilance.columns.Source,
                                  db.func.round(db.func.sum(MonthlyBilance.columns.Amount)))\
                                    .group_by(MonthlyBilance.columns.Source).all()
    
    #Calculate net income
    NetIncome=0
    Total=0
    for Source, Amount in BilanceTotal:
        NetIncome=NetIncome+Amount
        Total=Total+abs(Amount)
    BilanceTotalLabels=[]
    BilanceTotalValues=[]
    for Source, Amount in BilanceTotal:
        BilanceTotalLabels.append(Source+' '+str(round((abs(Amount)/Total)*100,2))+'%')
        BilanceTotalValues.append(Amount)

    return render_template("financialposture.html",
                           title="Finances",
                           BilanceTotalLabels=json.dumps(BilanceTotalLabels, cls=DecimalEncoder),
                           BilanceTotalValues=json.dumps(BilanceTotalValues, cls=DecimalEncoder),
                           NetIncome=NetIncome,
                           BilanceSourcesData=json.dumps(BilanceSourcesData, cls=DecimalEncoder),
                           BilanceData=json.dumps(BilanceSet, cls=DecimalEncoder)
                           )

#TODO: productssummary. Add panels:
# - Product priority over time
# - spending by Product (move from expenditures?)
# - Top 10 low priority product spending Calculate (Amount*(100-priority))
@app.route("/productssummary")
def productssummary():
        #Needs: 
        return render_template("underconstruction.html",
                           title="Products"
                           )

#TODO: producttypessummary
@app.route("/producttypessummary")
def producttypessummary():
        return render_template("underconstruction.html",
                           title="Product types"
                           )

#TODO: add average income year to date
#TODO: Paginate
@app.route("/income", methods=["GET", "POST"])
def income():
    form = IncomeInputForm()
    entries = db.session.query(Income).order_by(Income.DateTime.desc(),Income.ID.desc()).all()
    if form.validate_on_submit():
        entry = Income(DateTime=date.fromisoformat(form.datetime.data),
                Amount=form.amount.data,
                Type=form.type.data,
                Source=form.source.data,
                Comment=form.comment.data
        )
        addtodb(entry)
        return redirect(redirect_url())
    return render_template("incometable.html", title="Income", entries=entries, form=form)

#TODO: add average bills year to date
#TODO: Paginate
@app.route("/bills", methods=["GET", "POST"])
def bills():
    form = BillsInputForm()
    entries = db.session.query(Bills).order_by(Bills.DateTime.desc()).all()
    if form.validate_on_submit():
        entry = Bills(DateTime=date.fromisoformat(form.datetime.data),
                Amount=form.amount.data,
                Medium=form.medium.data,
                Comment=form.comment.data
        )
        addtodb(entry)
        return redirect(redirect_url())
    
    return render_template("billstable.html", title="Bills", entries=entries, form=form)

#TODO: add average expenditures year to date
#TODO: Paginate
@app.route("/expenditures", methods=["GET", "POST"])
def expenditures():
    form = ExpenditureInputForm()
    entries = db.session.query(ExpendituresEnriched).order_by(ExpendituresEnriched.columns.DateTime.desc()).all()
    if form.validate_on_submit():
        #TODO: GET ProductID, table[] usage is setup for generalization
        entry = Expenditures(DateTime=date.fromisoformat(form.datetime.data),
                Amount=form.amount.data,
                ProductID=form.productID.data,
                isCash=form.isCash.data,
                Comment=form.comment.data
        )
        addtodb(entry)
        return redirect(redirect_url())
    return render_template("expenditurestable.html", title="Expenditures", entries=entries, form=form)

@app.route("/products", methods=["GET", "POST"])
def products():
    form = ProductInputForm()
    entries = db.session.query(ProductSummary).all()
    if form.validate_on_submit():
        #TODO: GET ProductID, table[] usage is setup for generalization
        entry = Products(Product=form.product.data,
                TypeID=form.typeID.data,
                Comment=form.comment.data,
                Priority=form.priority.data
        )
        addtodb(entry)
        return redirect(redirect_url())

    return render_template("productstable.html", title="Products", entries=entries, form=form)

@app.route("/producttypes", methods=["GET", "POST"])
def producttypes():
    form = ProductTypeInputForm()
    entries = db.session.query(TypeSummary).all()
    if form.validate_on_submit():
        #TODO: GET ProductID, table[] usage is setup for generalization
        entry = ProductTypes(Type=form.type.data,
                Comment=form.comment.data,
                Priority=form.priority.data
        )
        addtodb(entry)
        return redirect(redirect_url())

    return render_template("producttypestable.html", title="Product Types", entries=entries, form=form)

#NICE-TO-HAVE: let user bulk delete records
#TODO: Fix - it does not work
#TODO: Secure - at least hash it
@app.route("/delete/<string:table>/<int:entry_id>")
def delete(table, entry_id):
    try:
        db.session.query(tables[table]).filter_by(ID=entry_id).delete()
        db.session.commit()
        flash("Data removed", "success")
    except Exception as error:
        print(error)
        db.session.flush()
        flash("Data not removed", "error")
    
    return redirect(redirect_url())

@app.route("/manbasic", methods=["GET"])
def manbasic():
    return render_template("manbasic.html", title="Basics")

@app.route("/mandata", methods=["GET"])
def mandata():
    return render_template("underconstruction.html", title="Basics")

@app.route("/manvisual", methods=["GET"])
def manvisual():
    return render_template("underconstruction.html", title="Basics")

@app.route("/manaction", methods=["GET"])
def manaction():
    return render_template("underconstruction.html", title="Basics")

@app.route("/manQnA", methods=["GET"])
def manQnA():
    return render_template("underconstruction.html", title="Basics")


#TODO: Secure - at least hash it
#TODO: FIX - producttypestable > edit - "ProductTypes has no DateTime column"*/
@app.route("/edit/<string:table>/<int:entry_id>", methods=["GET", "POST"])
def edit(table, entry_id):
    #TODO: this does not work, halting work for now
    #TODO: Generalize - use table variable
    # - need to base available fields on table itself
    # - IDs are not editable
    # - some fields need to be from droplist
    form = IncomeInputForm()
    #Get edited entry from db
    entry = db.get_or_404(entity=tables[table], ident=entry_id)
    #Set default values for edition form 
    if request.method == "POST" and form.validate_on_submit():
        #FIXME: for some unknown reason form data is converted into tuples while saving into class fields, thus commits are failing
        entry.DateTime=date.fromisoformat(form.datetime.data)
        entry.Amount=form.amount.data.real #FIXME: (builtins.TypeError) float() argument must be a string or a real number, not 'tuple'
        #FIXME: (sqlite3.InterfaceError) Error binding parameter 1 - probably unsupported type.
        entry.Type=str(form.type.data),    #FIXME: Arbitrary string works, form data even converted into string does not
        entry.Source=str(form.source.data),
        entry.Comment=str(form.comment.data)

        try:
            db.session.commit()
            flash("Data updated", "success")
        except Exception as error:
            print(error)
            db.session.flush()
            flash("Data not updated", "error")
        return redirect(redirect_url())
    else:
        form.datetime.data=entry.DateTime.strftime("%Y-%m-%d")
        form.amount.data=entry.Amount,
        form.type.data=entry.Type,
        form.source.data=entry.Source,
        form.comment.data=entry.Comment
    
    flash("Data editted", "success")
    return render_template("incomeedit.html", title="Incomeedit", form=form)
