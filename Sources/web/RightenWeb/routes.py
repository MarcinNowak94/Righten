from RightenWeb import app
from RightenWeb import db
from flask import render_template, flash, redirect, url_for, get_flashed_messages
from RightenWeb.models import Income, MonthlyIncome
from RightenWeb.forms import IncomeInputForm
import json
#NICE-TO-HAVE: Add event logging


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
    return render_template("income_add.html", title="Add income", form=form)

@app.route("/summary")
def summary():
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


    return render_template("summary.html",
                           title="Summary",
                           IncomeSummarydata=json.dumps(incometypesummary),
                           labels=json.dumps(incometypes), 
                           mimonths=json.dumps(MonthlyIncomemonths),
                           miamounts=json.dumps(MonthlyIncomeamounts)
                           )

@app.route("/income")
def income():
    entries = db.session.query(Income).order_by(Income.DateTime.desc()).all()
    return render_template("income_table.html", title="Income", entries=entries)

#NICE-TO-HAVE: let user bulk delete records
#TODO: Fix - it does not work
#TODO: Secure - at least hash it
@app.route("/delete/<string:table><int:entry_id>")
def delete(table, entry_id):
    #TODO: Generalize - use table variable

    #entry = db.session.query(Incometable).get_or_404(entity=db.Model, ident=entry_id)
    try:
        db.session.delete().where(Incometable.ID==entry_id)
        db.session.commit()
        flash("Data removed", "success")
    except:
        #TODO: Handle exception
        db.session.flush()
        flash("Data not removed", "error")
    #TODO: Ask once again if user wants to delete record
    return redirect(url_for("income"))

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