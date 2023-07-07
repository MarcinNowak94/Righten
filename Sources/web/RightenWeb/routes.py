from RightenWeb import app
from flask import render_template, flash, redirect, url_for, get_flashed_messages
from RightenWeb.forms import IncomeInputForm
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
        return redirect(url_for("income_add")) #So user can add another record
    return render_template("income_add.html", title="Add income", form=form)

@app.route("/summary")
def summary():
    return render_template("summary.html", title="Summary")