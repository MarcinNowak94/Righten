from RightenWeb import app
from RightenWeb import db
from flask import render_template, flash, redirect, url_for, request
from RightenWeb.models import *
from RightenWeb.forms import IncomeInputForm
from sqlalchemy import delete
import json
#NICE-TO-HAVE: Add event logging

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

@app.route("/incomeadd", methods=["GET", "POST"])
def incomeadd():
    form = IncomeInputForm()
    if form.validate_on_submit():
        #https://youtu.be/JgF6vaDYxzU?t=1015
        #TODO: Get ProductID, TypeID of product
        #productID=form.product.data
        #typeID=form.product.data
        #entry = #IncomeRecord(datetime=form.datetime.data,
        #                      amount=form.amount.data,
            #                      source=form.source.data,
        #                      type=form.type.data,
        #                      comment=form.comment.data
        # )
        #db.session.add(entry)
        #TODO: Add confirmation screen
        #flash("do you really want to add record", "message")
        #db.session.commit()
        flash("Data added", "success")
        return redirect(url_for("incomeadd")) #So user can add another record
    return render_template("incomeadd.html", title="Add income", form=form)

@app.route("/incomesummary")
def incomesummary():
    IncomeSummarydata=db.session.query(
        db.func.round(db.func.sum(Income.Amount),2),
        Income.Type
        ).group_by(Income.Type)\
         .order_by(Income.Type).all()
    #TODO: Change summary automate chart labels and values
    incometypesummary=[]
    incometypes=[]
    for sum, type in IncomeSummarydata:
        incometypesummary.append(sum)
        incometypes.append(type)

    IncomeOverTime=db.session.query(MonthlyIncome).all()
    MonthlyIncomemonths=[]
    MonthlyIncomeamounts=[]
    for Month, Amount in IncomeOverTime:
        MonthlyIncomeamounts.append(Amount)
        MonthlyIncomemonths.append(Month)


    return render_template("incomesummary.html",
                           title="Income",
                           IncomeSummarydata=json.dumps(incometypesummary),
                           labels=json.dumps(incometypes), 
                           mimonths=json.dumps(MonthlyIncomemonths),
                           miamounts=json.dumps(MonthlyIncomeamounts)
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
    #TODO: Change summary automate chart labels and values
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

@app.route("/income")
def income():
    entries = db.session.query(Income).order_by(Income.DateTime.desc()).all()
    return render_template("incometable.html", title="Income", entries=entries)

@app.route("/bills")
def bills():
    entries = db.session.query(Bills).order_by(Bills.DateTime.desc()).all()
    return render_template("billstable.html", title="Bills", entries=entries)

@app.route("/expenditures")
def expenditures():
    entries = db.session.query(Expenditures_Enriched).order_by(Expenditures_Enriched.columns.DateTime.desc()).all()
    return render_template("expenditurestable.html", title="Expenditures", entries=entries)

@app.route("/products")
def products():
    entries = db.session.query(ProductSummary).all()
    return render_template("productstable.html", title="Products", entries=entries)

@app.route("/producttypes")
def producttypes():
    entries = db.session.query(TypeSummary).all()
    return render_template("producttypestable.html", title="Product Types", entries=entries)

#NICE-TO-HAVE: let user bulk delete records
#TODO: Fix - it does not work
#TODO: Secure - at least hash it
@app.route("/delete/<string:table>/<int:entry_id>")
def delete(table, entry_id):
    #TODO: Add record deletion confirmation screen
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
@app.route("/edit/<string:table><int:entry_id>")
def edit(table, entry_id):
    #TODO: Generalize - use table variable
    entry = db.get_or_404(entity=Incometable, ident=entry_id)
    #TODO: Prepare edition panel
    #db.session.delete(entry)
    #db.session.commit()
    #TODO: Ask once again if user wants to delete record
    flash("Data editted", "success")
    return redirect(url_for("income"))