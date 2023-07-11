from RightenWeb import app
from RightenWeb import db
from flask import render_template, flash, redirect, url_for, request
from RightenWeb.models import *
from RightenWeb.forms import *
from sqlalchemy import delete
from datetime import date
import json
#NICE-TO-HAVE: Add event logging

def addtodb(entry):
    try:
        db.session.add(entry)
        db.session.commit()
        flash("Data added", "success")
    except Exception as error:
        print(error)
        db.session.flush()
        flash("Data not added", "error")

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

class ChartData():
    def __init__(self,
                    label,
                    value):
        self.label=label,
        self.value=value

@app.route("/incomesummary")
def incomesummary():
    IncomeSummarydata=db.session.query(TotalIncomeByType).all()
    incometypesummary=[]
    incometypes=[]
    for sum, type in IncomeSummarydata:
        incometypesummary.append(sum)
        incometypes.append(type)

    IncomeOverTime=db.session.query(MonthlyIncome).all()
    monthlyincomedata=[]
    for Month, Amount in IncomeOverTime:
        monthlyincomedata.append({"x": Month, "y": Amount})

    InvomeTypesByTime=db.session.query(MonthlyIncomeByType).all()

    return render_template("incomesummary.html",
                           title="Income",
                           IncomeSummarydata=json.dumps(incometypesummary),
                           IncomeSummarylabels=json.dumps(incometypes),
                           MonthlyIncome=json.dumps(monthlyincomedata)
                           )

@app.route("/billssummary")
def billssummary():
    BillsSummarydata=db.session.query(BillsSummary.columns.Medium, BillsSummary.columns.Amount).all()
    #TODO: Change summary automate chart labels and values
    billstypesummary=[]
    billstypes=[]
    for Medium, Amount in BillsSummarydata:
        billstypesummary.append(Amount)
        billstypes.append(Medium)

    BillsOverTime=db.session.query(MonthlyBills).all()
    MonthlyBillsmonths=[]
    MonthlyBillsamounts=[]
    for Month, Amount in BillsOverTime:
        MonthlyBillsmonths.append(Month)
        MonthlyBillsamounts.append(Amount)


    return render_template("billssummary.html",
                           title="Bills",
                           data=json.dumps(billstypesummary),
                           labels=json.dumps(billstypes), 
                           months=json.dumps(MonthlyBillsmonths),
                           amounts=json.dumps(MonthlyBillsamounts)
                           )

@app.route("/expendituressummary")
def expendituressummary():
    ExpendituresSummarydata=db.session.query(TypeSummary.columns.Type, TypeSummary.columns.Amount).all()
    Expenditurestypesummary=[]
    Expenditurestypes=[]
    for Type, Amount in ExpendituresSummarydata:
        Expenditurestypesummary.append(Amount)
        Expenditurestypes.append(Type)

    ExpendituresOverTime=db.session.query(MonthlyExpenditures).all()
    MonthlyExpendituresmonths=[]
    MonthlyExpendituresamounts=[]
    for Month, Amount in ExpendituresOverTime:
        MonthlyExpendituresmonths.append(Month)
        MonthlyExpendituresamounts.append(Amount)

    return render_template("expendituressummary.html",
                           title="Expenditures",
                           data=json.dumps(Expenditurestypesummary),
                           labels=json.dumps(Expenditurestypes), 
                           months=json.dumps(MonthlyExpendituresmonths),
                           amounts=json.dumps(MonthlyExpendituresamounts)
                           )

#TODO: productssummary
@app.route("/productssummary")
def productssummary():
        return render_template("underconstruction.html",
                           title="Products"
                           )

#TODO: producttypessummary
@app.route("/producttypessummary")
def producttypessummary():
        return render_template("underconstruction.html",
                           title="Product types"
                           )

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

@app.route("/expenditures", methods=["GET", "POST"])
def expenditures():
    form = ExpenditureInputForm()
    entries = db.session.query(Expenditures_Enriched).order_by(Expenditures_Enriched.columns.DateTime.desc()).all()
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


#TODO: Secure - at least hash it
@app.route("/edit/<string:table>/<int:entry_id>", methods=["GET", "POST"])
def edit(table, entry_id):
    #TODO: this does not work, halting work for now
    #TODO: Generalize - use table variable
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
