import flask
from flask import render_template, flash, redirect, url_for, request
import flask_login
from flask_login import current_user
from sqlalchemy import delete, union_all, func
from datetime import date
import json
import uuid
from Resources import db, app, version
from Resources.models import *
from Resources.forms import *
from Resources.__init__ import bcrypt
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
        return True
    except Exception as error:
        print(error)
        db.session.flush()
        flash("Data not added", "danger")
        return False

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
def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

@app.route("/")
def index():
    return render_template('index.html', title="Main apage");

@app.route("/layout")
def layout():
    return render_template("layout.html")

#User authentication -----------------------------------------------------------
#https://pypi.org/project/Flask-Login/

login_manager = flask_login.LoginManager(app=app)
login_manager.init_app(app)
login_manager.login_view="login"
login_manager.login_message="Log In to access this feature"
login_manager.session_protection="strong"

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(checkeduser):
    users=db.session.query(Users).all()
    for user in users:
        if checkeduser==user.Username:
            #TODO: Check if whole userentry can be moved here
            #possible issue: it can be na active session maintained for the duration of user interaction
            #possible issue: user object containing password stored in memory  
            currentuser = User()
            currentuser.id = checkeduser
            currentuser.uuid = user.ID
            return currentuser
    return

@login_manager.request_loader
def request_loader(request):
    users=db.session.query(Users).all()
    user = request.form.get('email')
    if user not in users:
        return

    currentuser = User()
    currentuser.id = user
    return currentuser

#TODO: add 'Forgot password?' and coresponding panel
@app.route('/login', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        username=form.username.data
        usr=db.session.query(Users).filter_by(Username=username).first()
        #if user does not exist password is not checked
        if (usr 
            and bcrypt.check_password_hash(usr.Password, form.password.data.encode('utf-8'))
            and usr.isActive):
            user = User()
            user.id = username
            flask_login.login_user(user)
            flash("User logged in", "success")
            return redirect(redirect_url(url_for("index", next="index")))

        flash("Failed to log in", "danger")
        return redirect(redirect_url(url_for("login", next="index")))
    return render_template("login.html", title="Login", form=form)

#TODO: Login and logout should be one button
@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    flash("User logged out", "success")
    return redirect(redirect_url("index"))

@login_manager.unauthorized_handler
def unauthorized_handler():
    flash("Access denied - requires logon", "danger")
    return redirect(url_for('index'))

#TODO: Move Change Password to separate site
@app.route('/settings', methods=['GET', 'POST'])
@flask_login.login_required
def settings():
    userentry = db.one_or_404(db.select(Users).filter_by(ID=current_user.uuid))
    #Settings must be separate to update them separately
    priority = db.session.query(UserSettings).filter_by(Setting="ProductPriorityTarget").first()
    spending = db.session.query(UserSettings).filter_by(Setting="SpendingTarget").first()
    savings = db.session.query(UserSettings).filter_by(Setting="SavingsTarget").first()

    form=SettingsForm(
        productprioritytarget=Decimal(priority.Value),
        spendingtarget=Decimal(spending.Value),
        savingstarget=Decimal(savings.Value),
        accountactive=bool(userentry.isActive)
    )

    if request.method == "POST" and form.validate_on_submit():
        #TODO: redirect to confirmation screen with password confirmation
        #Only active user can get here
        if form.accountactive.data==False:
            userentry.isActive=form.accountactive.data
            try:
                db.session.commit()
                flash("Account activity state changed to "+str(userentry.isActive), "success")
                flask_login.logout_user()
            except Exception as error:
                print(error)
                db.session.flush()
                flash("Account activity state NOT changed", "danger")
                pass
        
        #Store only changed values
        if form.productprioritytarget.data and form.productprioritytarget.data!=Decimal(priority.Value):
            priority.Value=form.productprioritytarget.data
            try:
                db.session.commit()
                flash("Product priority target updated", "success")
            except Exception as error:
                print(error)
                db.session.flush()
                flash("Product priority target not updated", "danger")
            pass

        if form.spendingtarget.data and form.spendingtarget.data!=Decimal(spending.Value):
            spending.Value=str(form.spendingtarget.data)
            try:
                db.session.commit()
                flash("Spending target updated", "success")
            except Exception as error:
                print(error)
                db.session.flush()
                flash("Spending target not updated", "danger")
            pass

        if form.savingstarget.data and form.savingstarget.data!=Decimal(savings.Value):
            savings.Value=str(form.savingstarget.data)
            try:
                db.session.commit()
                flash("Savings target updated", "success")
            except Exception as error:
                print(error)
                db.session.flush()
                flash("Savings target not updated", "danger")
            pass
        return redirect(redirect_url())
    return render_template("settings.html", form=form)

#User registration https://www.youtube.com/watch?v=71EU8gnZqZQ&t=45s
@app.route("/register", methods=['GET', 'POST'])
def register():
    form=RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        user = Users(ID=str(uuid.uuid4()),
                Username=form.username.data,
                Password=bcrypt.generate_password_hash(form.password.data),
                isActive=True
        )
        useradded=addtodb(user)
        if useradded and version!="debug_local":
            #TODO: create schema in postgreSQL
            print("TODO: create schema in postgreSQL")
        return redirect(redirect_url(url_for("login", next="login")))
    return render_template('register.html', title="Register", form=form)

#TODO
@app.route('/paswordreset', methods=['GET', 'POST'])
@flask_login.login_required
def passwordreset():
    #form=PasswordResetForm()
    #return render_template('passwordreset.html', title="Password reset", form=form)
    return render_template('underconstruction.html')

@app.route('/passwordchange', methods=['GET', 'POST'])
@flask_login.login_required
def passwordchange():
    userentry = db.one_or_404(db.select(Users).filter_by(ID=current_user.uuid))
    form=PasswordChangeForm()
    
    if request.method == "POST" and form.validate_on_submit():
        if (form.password.data
            and userentry.isActive
            and bcrypt.check_password_hash(userentry.Password, form.password.data.encode('utf-8'))):
            userentry.Password=bcrypt.generate_password_hash(form.password.data)
            try:
                db.session.commit()
                flash("Password updated", "success")
            except Exception as error:
                print(error)
                db.session.flush()
                flash("Password not updated", "danger")
                pass
            pass
        return redirect(redirect_url())
    return render_template('passwordchange.html', title="Password reset", form=form)

#Summaries and visualizations --------------------------------------------------

#TODO: Add percentages in piechart as in finances
@app.route("/incomesummary")
@flask_login.login_required
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

#TODO: Add percentages in piechart as in finances
@app.route("/billssummary")
@flask_login.login_required
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

#TODO: Add percentages in piechart as in finances
@app.route("/expendituressummary")
@flask_login.login_required
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

@app.route("/spending")
@flask_login.login_required
def spending():
    Spending=db.session.query(MonthlySpending).all()
    PriorityTarget=db.session.query(UserSettings).filter_by(Setting="ProductPriorityTarget").first()
    MonthlySpendingData=[]
    CashPercentageData=[]
    MonthlyPossibleSavingsData=[]
    ProductPriorityData=[]
    TypePriorityData=[]
    PriorityTargetData=[]
    for Month, Total, CashPercentage, AverageProductPriority, AverageTypePriority, PossibleSavings, AverageDaily in Spending:
        MonthlySpendingData.append({"x":Month,"y":Total})
        CashPercentageData.append({"x":Month,"y":CashPercentage})        
        MonthlyPossibleSavingsData.append({"x":Month,"y":PossibleSavings})
        ProductPriorityData.append({"x":Month,"y":AverageProductPriority})
        TypePriorityData.append({"x":Month,"y":AverageTypePriority})
        #Priority target is deeming which products are deemed as unnecessary expense
        #Priority data is average of month priorities, thus target priority is 100-target  
        PriorityTargetData.append({"x":Month,"y":100-int(PriorityTarget.Value)})
    
    return render_template("spendingsummary.html",
                           title="Spending",
                           MonthlySpendingData=json.dumps(MonthlySpendingData, cls=DecimalEncoder),
                           CashPercentageData=json.dumps(CashPercentageData, cls=DecimalEncoder),
                           MonthlyPossibleSavingsData=json.dumps(MonthlyPossibleSavingsData, cls=DecimalEncoder),
                           ProductPriorityData=json.dumps(ProductPriorityData, cls=DecimalEncoder),
                           TypePriorityData=json.dumps(TypePriorityData, cls=DecimalEncoder),
                           PriorityTargetData=json.dumps(PriorityTargetData, cls=DecimalEncoder)
                           )

#TODO: Financial posture
#TODO: add average income year to date
@app.route("/finances")
@flask_login.login_required
def finances():
    StatisticData=db.session.query(Statistics).all()
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

    Total=0
    for Source, Amount in BilanceTotal:
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
                           BilanceSourcesData=json.dumps(BilanceSourcesData, cls=DecimalEncoder),
                           BilanceData=json.dumps(BilanceSet, cls=DecimalEncoder),
                           StatisticData=StatisticData
                           )

#TODO: productssummary. Add panels:
# - Product priority over time
# - spending by Product (move from expenditures?)
# - Top 10 low priority product spending Calculate (Amount*(100-priority))
#TODO: Add product picker and corresponding graph
@app.route("/productssummary")
@flask_login.login_required
def productssummary():
    return render_template("underconstruction.html",
                        title="Products"
                        )

#TODO: producttypessummary
#TODO: Add type picker and corresponding graph
@app.route("/producttypessummary")
@flask_login.login_required
def producttypessummary():
        return render_template("underconstruction.html",
                           title="Product types"
                           )



#Basic data display ------------------------------------------------------------
#FIXME: As for now user cannot add new Income type or source
#TODO: Paginate
#NICE-TO-HAVE: Add data import option
@app.route("/income", methods=["GET", "POST"])
@flask_login.login_required
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
        return redirect(redirect_url(url_for("income", next="income")))
    return render_template("incometable.html", title="Income", entries=entries, form=form)

#TODO: add average bills year to date
#TODO: Paginate
#NICE-TO-HAVE: Add data import option
@app.route("/bills", methods=["GET", "POST"])
@flask_login.login_required
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
        return redirect(redirect_url(url_for("bills", next="bills")))
    
    return render_template("billstable.html", title="Bills", entries=entries, form=form)

#TODO: add average expenditures year to date
#TODO: Paginate
#NICE-TO-HAVE: Add data import option
@app.route("/expenditures", methods=["GET", "POST"])
@flask_login.login_required
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
@flask_login.login_required
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
@flask_login.login_required
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



#Deletion and edition pages ----------------------------------------------------

#NICE-TO-HAVE: let user bulk delete records
#TODO: Secure - at least hash it
@app.route("/delete/<string:table>/<int:entry_id>")
@flask_login.login_required
def delete(table, entry_id):
    try:
        db.session.query(tables[table]).filter_by(ID=entry_id).delete()
        db.session.commit()
        flash("Data removed", "success")
    except Exception as error:
        print(error)
        db.session.flush()
        flash("Data not removed", "danger")
    
    return redirect(redirect_url())

#TODO: Generalize - use table variable
#TODO: Secure - at least hash it
#TODO: set propper initial type & source based on record
@app.route("/incomeedit/<string:table>/<int:entry_id>", methods=["GET", "POST"])
@flask_login.login_required
def incomeedit(table, entry_id):
    # - need to base available fields on table itself
    # - IDs are not editable
    # - some fields need to be from droplist
    #Get edited entry from db
    entry = db.get_or_404(entity=tables[table], ident=entry_id)
    #Repopulate fields for edition https://stackoverflow.com/questions/26506566/check-the-version-of-wtforms-used-in-flask-wtforms
    form = IncomeInputForm(
        datetime=entry.DateTime.strftime("%Y-%m-%d"),
        amount=entry.Amount,
        comment=entry.Comment,
        type=entry.Type,
        source=entry.Source,
    )
    if request.method == "POST" and form.validate_on_submit():
        entry.DateTime=date.fromisoformat(form.datetime.data)
        entry.Amount=form.amount.data.real
        entry.Type=form.type.data
        entry.Source=form.source.data
        entry.Comment=form.comment.data
        #TODO: Return to table, currently returns to editor -
        try:
            db.session.commit()
            flash("Data updated", "success")
        except Exception as error:
            print(error)
            db.session.flush()
            flash("Data not updated", "danger")
        return redirect(redirect_url())
    return render_template("incomeedit.html", title="Income Edit", form=form)

@app.route("/billsedit/<string:table>/<int:entry_id>", methods=["GET", "POST"])
@flask_login.login_required
def billsedit(table, entry_id):
    #Get edited entry from db
    entry = db.get_or_404(entity=tables[table], ident=entry_id)
    #Repopulate fields for edition https://stackoverflow.com/questions/26506566/check-the-version-of-wtforms-used-in-flask-wtforms
    form = BillsInputForm(
        datetime=entry.DateTime.strftime("%Y-%m-%d"),
        amount=entry.Amount,
        comment=entry.Comment,
        medium=entry.Medium
    )
    if request.method == "POST" and form.validate_on_submit():
        entry.DateTime=date.fromisoformat(form.datetime.data)
        entry.Amount=form.amount.data.real
        entry.Medium=form.medium.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
        except Exception as error:
            print(error)
            db.session.flush()
            flash("Data not updated", "danger")
        return redirect(redirect_url())
    return render_template("billsedit.html", title="Bills Edit", form=form)

@app.route("/expendituresedit/<string:table>/<int:entry_id>", methods=["GET", "POST"])
@flask_login.login_required
def expendituresedit(table, entry_id):
    #Get edited entry from db
    entry = db.get_or_404(entity=tables[table], ident=entry_id)
    #Repopulate fields for edition https://stackoverflow.com/questions/26506566/check-the-version-of-wtforms-used-in-flask-wtforms
    form = form = ExpenditureInputForm(
        datetime=entry.DateTime.strftime("%Y-%m-%d"),
        amount=entry.Amount,
        comment=entry.Comment,
        productID=entry.ProductID,
        isCash=entry.isCash
    )
    if request.method == "POST" and form.validate_on_submit():
        entry.DateTime=date.fromisoformat(form.datetime.data)
        entry.Amount=form.amount.data.real
        entry.ProductID=form.productID.data
        entry.isCash=form.isCash.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
        except Exception as error:
            print(error)
            db.session.flush()
            flash("Data not updated", "danger")
            #https://stackoverflow.com/questions/7075200/converting-exception-to-a-string-in-python-3
            #print("Error {0}".format(str(error.args[0])).encode("utf-8"))
        return redirect(redirect_url())
    return render_template("expendituresedit.html", title="Expenditures Edit", form=form)

@app.route("/producttypesedit/<string:table>/<int:entry_id>", methods=["GET", "POST"])
@flask_login.login_required
def producttypesedit(table, entry_id):
    #Get edited entry from db
    entry = db.get_or_404(entity=tables[table], ident=entry_id)
    #Repopulate fields for edition https://stackoverflow.com/questions/26506566/check-the-version-of-wtforms-used-in-flask-wtforms
    form = form = ProductTypeInputForm(
        type=entry.Type,
        priority=entry.Priority,
        comment=entry.Comment
    )
    if request.method == "POST" and form.validate_on_submit():
        entry.Type=form.type.data
        entry.Priority=form.priority.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
        except Exception as error:
            print(error)
            db.session.flush()
            flash("Data not updated", "danger")
            #https://stackoverflow.com/questions/7075200/converting-exception-to-a-string-in-python-3
            #print("Error {0}".format(str(error.args[0])).encode("utf-8"))
        return redirect(redirect_url())
    return render_template("producttypesedit.html", title="Product Types edit", form=form)

@app.route("/productsedit/<string:table>/<int:entry_id>", methods=["GET", "POST"])
@flask_login.login_required
def productsedit(table, entry_id):
    #Get edited entry from db
    entry = db.get_or_404(entity=tables[table], ident=entry_id)
    #Repopulate fields for edition https://stackoverflow.com/questions/26506566/check-the-version-of-wtforms-used-in-flask-wtforms
    form = form = ProductInputForm(
        product=entry.Product,
        typeID=entry.TypeID,
        priority=entry.Priority,
        comment=entry.Comment
    )
    if request.method == "POST" and form.validate_on_submit():
        entry.Product=form.product.data
        entry.TypeID=form.typeID.data
        entry.Priority=form.priority.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
        except Exception as error:
            print(error)
            db.session.flush()
            flash("Data not updated", "danger")
            #https://stackoverflow.com/questions/7075200/converting-exception-to-a-string-in-python-3
            #print("Error {0}".format(str(error.args[0])).encode("utf-8"))
        return redirect(redirect_url())
    return render_template("productsedit.html", title="Products Edit", form=form)

#Manual pages ------------------------------------------------------------------

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

@app.route("/contact", methods=["GET"])
def contact():
    return render_template("underconstruction.html", title="Basics")