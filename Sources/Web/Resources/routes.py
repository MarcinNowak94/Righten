from typing import SupportsComplex, List, Dict
from datetime import date
from decimal import Decimal
import flask
from flask import render_template, flash, redirect, url_for, request
import flask_login
from flask_login import current_user
import json
from secrets import token_urlsafe
from sqlalchemy import delete, union_all, func
import uuid

from Resources import db, app
from Resources.models import *
from Resources.forms import *
from Resources.__init__ import bcrypt

class DecimalEncoder(json.JSONEncoder):
  """Dumps decimal data in JSON format"""
  # As per: https://stackoverflow.com/questions/63278737/object-of-type-decimal-is-not-json-serializable
  
  def default(self, obj):
    if isinstance(obj, Decimal):
      return str(obj)
    return json.JSONEncoder.default(self, obj)

def get_request_data() -> json:
    """Returns request data formated as json"""
    cookie = request.cookies["session"] if request.cookies else None

    return {
        "session": cookie,
        "useragent": request.user_agent.string,
        "accessroute": request.access_route,
        "sourceip": request.remote_addr,
        "sourceport": request.environ["REMOTE_PORT"],
        "method": request.method,
        "server": request.server,
        "ful_path": request.full_path                    
    }

def get_current_user_ID() -> str:
    """Get current user id or None"""
    
    try:
        userid=current_user.uuid
    except AttributeError:
        userid=None
    return userid

def log_site_opened() -> None:
    """Logs that site was opened by user"""
    
    logger.info(
        "User visited site",
        extra={
            "action": "Site visited",
            "result": "Success",
            "user": get_current_user_ID(),
            "request": get_request_data()
            }
        )

def check_password(
        user: Users, 
        password: str
    ) -> bool:
    """Checks user password and logs event

    Arguments:
        user -- User record check 
        newpass -- given password

    Returns:
        True if succeeded
    """

    result = bcrypt.check_password_hash(
                    user.Password, 
                    password.encode('utf-8')
                    )
    
    extra={
        "action": "User password check",
        "result": "Success" if result is True else "Failure",
        "function": check_password.__name__,
        "user": user.Username,
        "error": None if result is True else "Password incorrect",
        "request": get_request_data()
        }

    if result is True:
        logger.info("Password check passed",extra)
    else:
        logger.warn("Password check failed",extra)

    return result

def change_password(
        user: Users, 
        newpass: str
    ) -> bool:
    """Changes user password in database

    Arguments:
        user -- User record to update 
        newpass -- new password

    Returns:
        True if succeeded
    """

    user.Password = bcrypt.generate_password_hash(newpass)
    extra={
            "action": "User password change",
            "result": None,
            "function": change_password.__name__,
            "user": user.Username,
            "error": None,
            "request": get_request_data()
        }

    try:
        db.session.commit()
        flash("Password updated", "success")
        result = True
    except Exception as error:
        db.session.flush()
        flash("Password not updated", "danger")
        result = True
        extra["error"] = error
    pass
    extra["result"] = "Success" if result is True else "Failure"
    logger.info(
        "Password change",
        extra
        )
    return result

def addtodb(entry, notify=False) -> bool:
    """Commit entry to database and log changes

    Arguments:
        :entry: -- data to add to database

    Keyword Arguments:
        :notify: -- Wether to notify user of changes or not (default: {False})

    Returns:
        True if operation was successful
    """
    result = False
    errors = None
    try:
        db.session.add(entry)
        db.session.commit()
        if notify is True:
            flash("Data added", "success")
        result = True
    except Exception as error:
        db.session.flush()
        if notify is True:
            flash("Data not added", "danger")
        result = False
        errors = error
    
    logger.debug(
            "Database insert attempt",
            extra = {
                "action": "Database insert",
                "result": "Success" if result else "Failure",
                "function": addtodb.__name__,
                "user": get_current_user_ID(),
                "error": errors,
                "table": entry.__table__.description,
                "request": get_request_data()
                }
            )
    return result

def createuser(user: Users) -> bool:
    """Creates user with specified data and initializes settings with default values

    Arguments:
        :user: -- User to be created

    Returns:
        True if creation is successfull
    """

    # NICE-TO-HAVE: Populate with statistical data from app or GUS 
    settings={
        "ProductPriorityTarget":	33,
        "SpendingTarget":	3000,
        "SavingsTarget":	100
    }

    success = False
    success = addtodb(user, notify=True)
    operations={
        "UserCreation" : success
    } 

    for setting in settings:
        usersetting = UserSettings(
            UserID=user.ID,
            Setting=setting,
            Value=settings[setting]
        )
        # Notify = False or else every setting change generates separate notification
        success = addtodb(usersetting, notify=False)
        operations[setting]=success

    for operation in operations:
        if operations[operation] is False: 
            success = False
            break

    logger.info(
        "New user registered",
        extra={
            "action": "User add",
            "result": "Success" if success else "Failure",
            "function": register.__name__,
            "user": user.ID,
            "operations": operations,
            "request": get_request_data()
            }
        )

    return success

def createchartdataset(dbdata: list, fill="false") -> list:
    """Formats provided sets od data into unified chart data set {date, value} 
    with labels. To display data on the same graph dates in all sets are 
    normalized meaning entrioes for missing dates are added with value 0."""
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

    logger.debug(
            "Created chart data set",
            extra={
                "action": "Chart dataset creation", 
                "result": "Success",
                "function": createchartdataset.__name__,
                "user": get_current_user_ID(),
                "request": get_request_data()
                }
            )
    return dataset

def createpiechartdataset(
        data: List[Dict[str, SupportsComplex]],
        value_descriptor="Amount",
        addperc=False
        ):
    """Creates data for jschart piechart

    Arguments:
        :data: -- Data to chart in form: [Label, value] 

    Keyword Arguments:
        :value_descriptor: -- Text displayed beside value on mouse hover (default: {"Amount"})
        :addperc: -- Adds percentage to label (default: {False})

    Returns:
        JSON formatted jschart piechart data
    """

    labels=[]
    values=[]
    total=0
    if addperc is True:
        for label, value in data:
            total+=value
        #sum=sum(value for label, value in data)

    for label, value in data:
        if addperc is True:
            label+=" "+str(round((value/total)*100))+"%"
        labels.append(label)
        values.append(value)

    chartdata={
        "labels": labels,
        "datasets": [{
            "label": value_descriptor,
            "data": values
        }]
    }

    return chartdata

def redirect_url(default='index') -> str:
    """Returns redirect url either:
    1. 'next' argument in request
    2. referrer
    3. provided site
    4. default site - index    
    As per https://stackoverflow.com/questions/14277067/redirect-back-in-flask
    """
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

@app.route("/")
def index():
    log_site_opened()
    return render_template('index.html', title="Main apage");

@app.route("/layout")
def layout():
    log_site_opened()
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        username = form.username.data
        usr = db.session.query(Users).filter_by(Username=username).first()
        errors = {}
        
        # Silent check tree
        if usr is None:
            errors["User exist"]=False
        else:
            if not usr.isActive:
                errors["User is active"]=False
            if not check_password(usr, form.password.data):
                errors["Password is valid"]=False

        if not errors:
            user = User()
            user.id = username
            flask_login.login_user(user)
            flash("User logged in", "success")
            logger.info(
                "User logged in",
                extra = {
                    "action": "Login",
                    "result": "Success",
                    "user": usr.ID,
                    "request": get_request_data()
                    }
                )
            return redirect(redirect_url(url_for("index", next="index")))

        # No details as to deter password bruteforce
        flash("Failed to log in", "danger")
        logger.info(
                "User failed to logged in", 
                extra = {
                    "action": "Login",
                    "result": "Failure",
                    "user": get_current_user_ID(),
                    "params": {
                        "givenusername": username
                        },
                    "errors" : errors,
                    "request": get_request_data()
                    }
                )
        return redirect(redirect_url(url_for("login", next="index")))
    return render_template("login.html", title="Login", form=form)

#TODO: Login and logout should be one button
@app.route('/logout')
@flask_login.login_required
def logout():
    flash("User logged out", "success")
    logger.debug(
        "User logged out",
        extra={
            "action": "Logout", 
            "result": "Success",
            "function": logout.__name__,
            "user": get_current_user_ID(),
            "request": get_request_data()
            }
        )
    flask_login.logout_user()
    return redirect(redirect_url("index"))

@login_manager.unauthorized_handler
def unauthorized_handler():
    flash("Access denied - requires logon", "danger")
    logger.warning(
        "Access denied - requires logon",
        extra={
            "action": "Access attempt",
            "result": "Failure",
            "function": unauthorized_handler.__name__,
            "reason": "Login required",
            "request": get_request_data()
            }
        )
    return redirect(url_for('index'))

# NICE-TO-HAVE: Refactoring
@app.route('/settings', methods=['GET', 'POST'])
@flask_login.login_required
def settings():
    result="Success"
    changeerror=None
    settingschanged=[]

    userentry = db.one_or_404(db.select(Users).filter_by(ID=current_user.uuid))
    # Settings must be separate to update them separately
    priority = db.session.query(UserSettings).\
                            filter_by(
                                Setting="ProductPriorityTarget",
                                UserID=current_user.uuid).\
                            first()
    spending = db.session.query(UserSettings).\
                            filter_by(
                                Setting="SpendingTarget",
                                UserID=current_user.uuid).\
                            first()
    savings = db.session.query(UserSettings).\
                            filter_by(
                                Setting="SavingsTarget",
                                UserID=current_user.uuid).\
                            first()

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
            change = {}
            change["setting"] = "Account activity"
            change["oldvalue"] = userentry.isActive
            change["newvalue"] = form.accountactive.data

            userentry.isActive=form.accountactive.data   
            try:
                db.session.commit()
                flash("Account activity state changed to "+str(userentry.isActive), "success")
                result="Success"
                flask_login.logout_user()
            except Exception as error:
                db.session.flush()
                flash("Account activity state NOT changed", "danger")
                result="Failure"
                changeerror=error
            
            change["result"] = result
            change["error"] = changeerror
            settingschanged.append(change)
        
        #Store only changed values
        if form.productprioritytarget.data and form.productprioritytarget.data!=Decimal(priority.Value):
            change = {}
            change["setting"] = "Priority target"
            change["oldvalue"] = priority.Value
            change["newvalue"] = form.productprioritytarget.data

            priority.Value=form.productprioritytarget.data
            try:
                db.session.commit()
                flash("Product priority target updated", "success")
                result="Success"
            except Exception as error:
                db.session.flush()
                flash("Product priority target not updated", "danger")
                result="Failure"
                changeerror=error
            
            change["result"] = result
            change["error"] = changeerror
            settingschanged.append(change)

        if form.spendingtarget.data and form.spendingtarget.data!=Decimal(spending.Value):
            change = {}
            change["setting"] = "Spending target"
            change["oldvalue"] = spending.Value
            change["newvalue"] = form.spendingtarget.data

            spending.Value=str(form.spendingtarget.data)
            try:
                db.session.commit()
                flash("Spending target updated", "success")
                result="Success"
            except Exception as error:
                db.session.flush()
                flash("Spending target not updated", "danger")
                result="Failure"
                changeerror=error
            
            change["result"] = result
            change["error"] = changeerror
            settingschanged.append(change)

        if form.savingstarget.data and form.savingstarget.data!=Decimal(savings.Value):
            change = {}
            change["setting"] = "Savings target"
            change["oldvalue"] = savings.Value
            change["newvalue"] = form.savingstarget.data
            
            savings.Value=str(form.savingstarget.data)
            try:
                db.session.commit()
                flash("Savings target updated", "success")
                result="Success"
            except Exception as error:
                db.session.flush()
                flash("Savings target not updated", "danger")
                result="Failure"
                changeerror=error
            pass
            
            change["result"] = result
            change["error"] = changeerror
            settingschanged.append(change)

        logger.warn(
            "User settings change",
            extra={
                "action": "User settings change",
                "function": settings.__name__,
                "user": get_current_user_ID(),
                "changes": settingschanged,
                "request": get_request_data()
                }
            )
        return redirect(redirect_url())
    log_site_opened()
    return render_template("settings.html", form=form)

#User registration https://www.youtube.com/watch?v=71EU8gnZqZQ&t=45s
# NICE-TO-HAVE: Add account activation
@app.route("/register", methods=['GET', 'POST'])
def register():
    form=RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        user = Users(ID=str(uuid.uuid4()),
                Username=form.username.data,
                Password=bcrypt.generate_password_hash(form.password.data),
                isActive=True
        )

        if createuser(user):
            flash("Account created successfully", "success")
        else:
            flash("Account creation failed", "error")

        return redirect(redirect_url(url_for("login", next="login")))
    log_site_opened()
    return render_template('register.html', title="Register", form=form)

@app.route('/passwordreset_generatetoken', methods=['GET', 'POST'])
def passwordreset_generatetoken():
    form=PasswordResetGenerateTokenForm()

    if request.method == "POST" and form.validate_on_submit():
        token=token_urlsafe()   #FIXME: Solely for proof of concrpt
        logger.info(
            "Password reset token generation",
            extra={
                "action": "User password change",
                "result": "Success",
                "token": token,
                "provideduser": form.username,
                "function": passwordreset.__name__,
                "user": get_current_user_ID(),
                "request": get_request_data()
                }
            )
        return redirect(url_for('passwordreset', token=token))
    
    log_site_opened()
    return render_template('passwordreset_generatetoken.html', title="Generate token", form=form)

#FIXME: Solely for proving concept
@app.route('/paswordreset/<string:token>', methods=['GET', 'POST'])
def passwordreset(token): 
    form=PasswordResetForm()
    form.resettoken.data=token
    
    if request.method == "POST" and form.validate_on_submit():
        #TODO: reset password in DB
        userentry = db.one_or_404(
            db.select(Users).filter_by(token=form.resettoken.data)
            )
        change_password(userentry, form.newpassword.data)

    log_site_opened()
    return render_template('passwordreset.html', title="Password reset", form=form)

#NICE-TO-HAVE: add email password change confirmation
@app.route('/passwordchange', methods=['GET', 'POST'])
@flask_login.login_required
def passwordchange():
    form = PasswordChangeForm()
    
    if request.method == "POST" and form.validate_on_submit():
        userentry = db.one_or_404(db.select(Users).filter_by(ID=current_user.uuid))
        isvalidpassword=check_password(userentry, form.password.data)
        if not isvalidpassword:
            flash("Password incorrect", "danger")

        if (form.password.data
            and userentry.isActive
            and isvalidpassword
            ):
            change_password(userentry, form.newpassword.data)
        
        return redirect(redirect_url())
    
    log_site_opened()
    return render_template('passwordchange.html', title="Password reset", form=form)

#Summaries and visualizations --------------------------------------------------

#TODO: Add percentages in piechart as in finances
@app.route("/incomesummary")
@flask_login.login_required
def incomesummary():
    IncomeSummarydata = db.session.query(IncomeSummaryByType.columns.Type,
                                         IncomeSummaryByType.columns.Amount).\
                                filter_by(UserID=current_user.uuid).all()
    summary = db.session.query(IncomeSummary).\
                                filter_by(UserID=current_user.uuid).all()
    IncomeOverTime = db.session.query(
                                    MonthlyIncome.columns.Month,
                                    MonthlyIncome.columns.Amount).\
                                filter_by(UserID=current_user.uuid).all()
    IncomeTypesByTime = db.session.query(
                                MonthlyIncomeByType.columns.Month,
                                MonthlyIncomeByType.columns.Amount,
                                MonthlyIncomeByType.columns.Type).\
                                filter_by(UserID=current_user.uuid).all()
    
    IncomeTypechart=createpiechartdataset(IncomeSummarydata, addperc=True)
    IncomeTypesByTimeDataset=createchartdataset(IncomeTypesByTime)

    monthlyincomedata = []
    for month, amount in IncomeOverTime:
        monthlyincomedata.append({"x": month, "y": amount})

    log_site_opened()
    return render_template("incomesummary.html",
                           title="Income",
                           IncomeTypechart=json.dumps(IncomeTypechart, cls=DecimalEncoder),
                           MonthlyIncome=json.dumps(monthlyincomedata, cls=DecimalEncoder),
                           IncomeTypesByTimeDataset=json.dumps(IncomeTypesByTimeDataset, cls=DecimalEncoder),
                           Summary=summary
                           )

#TODO: Add percentages in piechart as in finances
@app.route("/billssummary")
@flask_login.login_required
def billssummary():
    BillsTypeAmounts = []
    BillsTypes = []
    Summary = db.session.query(BillsSummary).\
                                filter_by(UserID=current_user.uuid).all()
    for Medium, Amount in db.session.query(BillsSummary.columns.Medium,
                                           BillsSummary.columns.Amount).\
                                            filter_by(UserID=current_user.uuid).\
                                            order_by(BillsSummary.columns.Amount.desc())\
                                                .all():
        BillsTypeAmounts.append(Amount)
        BillsTypes.append(Medium)

    MonthlyBillsData = []
    for Month, Amount in db.session.query(MonthlyBills).\
                                filter_by(UserID=current_user.uuid).all():
        MonthlyBillsData.append({"x": Month, "y":Amount})
    
    BillsTypespermonth = db.session.query(MonthlyBillsByMedium).\
                                filter_by(UserID=current_user.uuid).all()
    BillsTypesData = createchartdataset(BillsTypespermonth)

    log_site_opened()
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

    log_site_opened()
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
    SpendingTarget=db.session.query(UserSettings).filter_by(Setting="SpendingTarget", UserID=current_user.uuid).first()
    MonthlySpendingData=[]
    CashPercentageData=[]
    MonthlyPossibleSavingsData=[]
    ProductPriorityData=[]
    TypePriorityData=[]
    SpendingTargetData=[]
    PriorityTargetData=[]
    for Month, Total, CashPercentage, AverageProductPriority, AverageTypePriority, PossibleSavings, AverageDaily in Spending:
        MonthlySpendingData.append({"x":Month,"y":Total})
        CashPercentageData.append({"x":Month,"y":CashPercentage})        
        MonthlyPossibleSavingsData.append({"x":Month,"y":PossibleSavings})
        ProductPriorityData.append({"x":Month,"y":AverageProductPriority})
        TypePriorityData.append({"x":Month,"y":AverageTypePriority})
        
        # Priority target is deeming which products are deemed as unnecessary expense
        # Priority data is average of month priorities, thus target priority is 100-target  
        PriorityTargetData.append({"x":Month,"y":100-int(PriorityTarget.Value)})
        SpendingTargetData.append({"x":Month,"y":SpendingTarget.Value})
    
    log_site_opened()
    return render_template("spendingsummary.html",
                           title="Spending",
                           MonthlySpendingData=json.dumps(MonthlySpendingData, cls=DecimalEncoder),
                           CashPercentageData=json.dumps(CashPercentageData, cls=DecimalEncoder),
                           MonthlyPossibleSavingsData=json.dumps(MonthlyPossibleSavingsData, cls=DecimalEncoder),
                           ProductPriorityData=json.dumps(ProductPriorityData, cls=DecimalEncoder),
                           TypePriorityData=json.dumps(TypePriorityData, cls=DecimalEncoder),
                           PriorityTargetData=json.dumps(PriorityTargetData, cls=DecimalEncoder),
                           SpendingTargetData=json.dumps(SpendingTargetData, cls=DecimalEncoder)
                           )

#TODO: Financial posture
#TODO: add average income year to date
@app.route("/finances")
@flask_login.login_required
def finances():
    StatisticData=db.session.query(Statistics).all()
    BilanceData=db.session.query(MonthlyBilanceSingle).all()
    SavingsTargetData=(db.session.query(UserSettings).filter_by(Setting="SavingsTarget", UserID=current_user.uuid).first()).Value
    Bilance=[]
    Breakeven=[]
    BilanceSet=[]
    SavingsTarget=[]
    sets = {
        "Bilance": Bilance,
        "Breakeven": Breakeven,
        "Savings Target": SavingsTarget
        }
    
    #Adding breakeven line 
    for Month, Amount in BilanceData:
        Bilance.append({"x":Month,"y":Amount})
        Breakeven.append({"x":Month,"y":0})
        SavingsTarget.append({"x":Month,"y":SavingsTargetData})
    
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

    log_site_opened()
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
    # TODO: filter results to products chosen by user in GUI
    monthlyProducts = db.session.query(MonthlyProducts).all()
    
    Top10Products = db.session.query(Top10ProductsMonthly).all()
    
    Top10ProductsData = createchartdataset(Top10Products)


    log_site_opened()
    return render_template("underconstruction.html",
                        title="Products"
                        )

#TODO: producttypessummary
#TODO: Add type picker and corresponding graph
@app.route("/producttypessummary")
@flask_login.login_required
def producttypessummary():
    log_site_opened()
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
    entries = db.session.query(Income).\
                            filter_by(UserID=current_user.uuid).\
                            order_by(Income.DateTime.desc(),Income.ID.desc()).\
                            all()
    if form.validate_on_submit():
        entry = Income(DateTime=date.fromisoformat(form.datetime.data),
                Amount=form.amount.data,
                Type=form.type.data,
                Source=form.source.data,
                Comment=form.comment.data,
                UserID=current_user.uuid
        )
        addtodb(entry, notify=True)
        return redirect(redirect_url(url_for("income", next="income")))
    log_site_opened()
    return render_template("incometable.html", title="Income", entries=entries, form=form)

#TODO: add average bills year to date
#TODO: Paginate
#NICE-TO-HAVE: Add data import option
@app.route("/bills", methods=["GET", "POST"])
@flask_login.login_required
def bills():
    form = BillsInputForm(current_user.uuid)
    entries = db.session.query(Bills).\
                            filter_by(UserID=current_user.uuid).\
                            order_by(Bills.DateTime.desc()).\
                            all()
    if form.validate_on_submit():
        entry = Bills(DateTime=date.fromisoformat(form.datetime.data),
                Amount=form.amount.data,
                Medium=form.medium.data,
                Comment=form.comment.data,
                UserID=current_user.uuid
        )
        addtodb(entry, notify = True)
        return redirect(redirect_url(url_for("bills", next="bills")))
    
    log_site_opened()
    return render_template("billstable.html", title="Bills", entries=entries, form=form)

#TODO: add average expenditures year to date
#TODO: Paginate
#NICE-TO-HAVE: Add data import option
@app.route("/expenditures", methods=["GET", "POST"])
@flask_login.login_required
def expenditures():
    form = ExpenditureInputForm()
    entries = db.session.query(ExpendituresEnriched).\
                            filter_by(UserID=current_user.uuid).\
                            order_by(ExpendituresEnriched.columns.DateTime.desc()).\
                            all()
    if form.validate_on_submit():
        #TODO: GET ProductID, table[] usage is setup for generalization
        entry = Expenditures(DateTime=date.fromisoformat(form.datetime.data),
                Amount=form.amount.data,
                ProductID=form.productID.data,
                isCash=form.isCash.data,
                Comment=form.comment.data,
                UserID=current_user.uuid
        )
        addtodb(entry, notify=True)
        return redirect(redirect_url())
    
    log_site_opened()
    return render_template("expenditurestable.html", title="Expenditures", entries=entries, form=form)

@app.route("/products", methods=["GET", "POST"])
@flask_login.login_required
def products():
    form = ProductInputForm()
    entries = db.session.query(ProductSummary).\
                            filter_by(UserID=current_user.uuid).\
                            all()
    if form.validate_on_submit():
        #TODO: GET ProductID, table[] usage is setup for generalization
        entry = Products(Product=form.product.data,
                TypeID=form.typeID.data,
                Comment=form.comment.data,
                Priority=form.priority.data,
                UserID=current_user.uuid
        )
        addtodb(entry, notify=True)
        return redirect(redirect_url())
    
    log_site_opened()
    return render_template("productstable.html", title="Products", entries=entries, form=form)

@app.route("/producttypes", methods=["GET", "POST"])
@flask_login.login_required
def producttypes():
    form = ProductTypeInputForm()
    entries = db.session.query(TypeSummary).\
                            filter_by(UserID=current_user.uuid).\
                            all()
    if form.validate_on_submit():
        #TODO: GET ProductID, table[] usage is setup for generalization
        entry = ProductTypes(Type=form.type.data,
                Comment=form.comment.data,
                Priority=form.priority.data,
                UserID=current_user.uuid
        )
        addtodb(entry, notify = True)

        return redirect(redirect_url())
    
    log_site_opened()
    return render_template("producttypestable.html", title="Product Types", entries=entries, form=form)



#Deletion and edition pages ----------------------------------------------------

#NICE-TO-HAVE: let user bulk delete records
#TODO: Secure - at least hash it
@app.route("/delete/<string:table>/<int:entry_id>")
@flask_login.login_required
def delete(table, entry_id):
    result=False
    errors=None
    try:
        db.session.query(tables[table]).\
                        filter_by(
                            ID=entry_id,
                            UserID=current_user.uuid).\
                        delete()
        db.session.commit()
        flash("Data removed", "success")
        result=True
    except Exception as error:
        db.session.flush()
        flash("Data not removed", "danger")
        result=False
        errors=error

    logger.debug(
            "Database delete attempt",
            extra={
                "action": "Database delete",
                "result": "Success" if result else "Failure",
                "function": delete.__name__,
                "user": get_current_user_ID(),
                "error": errors,
                "table": table,
                "entryID": entry_id,
                "request": get_request_data()
                }
            )
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
        source=entry.Source
        # Should not be necessary ,UserID=current_user.uuid
    )
    if request.method == "POST" and form.validate_on_submit():
        result="Success"
        errors=None
        entry.DateTime=date.fromisoformat(form.datetime.data)
        entry.Amount=form.amount.data.real
        entry.Type=form.type.data
        entry.Source=form.source.data
        entry.Comment=form.comment.data
        #TODO: Return to table, currently returns to editor -
        try:
            db.session.commit()
            flash("Data updated", "success")
            result="Success"
        except Exception as error:
            db.session.flush()
            flash("Data not updated", "danger")
            result="Failure"
            errors=error
        logger.warn(
            "Income data edit",
            extra={
                "action": "Database update",
                "result": result,
                "function": incomeedit.__name__,
                "user": get_current_user_ID(),
                "error": errors,
                "table": "Income",
                "entryID": entry_id,
                "request": get_request_data()
                }
            )
        return redirect(redirect_url())
    log_site_opened()
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
        # Should not be necessary ,UserID=current_user.uuid
    )
    if request.method == "POST" and form.validate_on_submit():
        result="Success"
        errors=None
        entry.DateTime=date.fromisoformat(form.datetime.data)
        entry.Amount=form.amount.data.real
        entry.Medium=form.medium.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
            result="Success"
        except Exception as error:
            db.session.flush()
            flash("Data not updated", "danger")
            result="Failure"
            errors=error
        logger.warn(
            "Bills data edit",
            extra={
                "action": "Database update",
                "result": result,
                "function": billsedit.__name__,
                "user": get_current_user_ID(),
                "error": errors,
                "table": "Bills",
                "entryID": entry_id,
                "request": get_request_data()
                }
            )
        return redirect(redirect_url())
    log_site_opened()
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
        # Should not be necessary ,UserID=current_user.uuid
    )
    if request.method == "POST" and form.validate_on_submit():
        result="Success"
        errors=None
        entry.DateTime=date.fromisoformat(form.datetime.data)
        entry.Amount=form.amount.data.real
        entry.ProductID=form.productID.data
        entry.isCash=form.isCash.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
            result="Success"
        except Exception as error:
            db.session.flush()
            flash("Data not updated", "danger")
            result="Failure"
            errors=error
        logger.warn(
            "Expenditures data edit",
            extra={
                "action": "Database update",
                "result": result,
                "function": expendituresedit.__name__,
                "user": get_current_user_ID(),
                "error": errors,
                "table": "Expenditures",
                "entryID": entry_id,
                "request": get_request_data()
                }
            )
            
        return redirect(redirect_url())
    log_site_opened()
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
        # Should not be necessary ,UserID=current_user.uuid
    )
    if request.method == "POST" and form.validate_on_submit():
        result="Success"
        errors=None
        entry.Type=form.type.data
        entry.Priority=form.priority.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
            result="Success"
        except Exception as error:
            db.session.flush()
            flash("Data not updated", "danger")
            result="Failure"
            errors=error
        logger.warn(
            "Product Types data edit",
            extra={
                "action": "Database update",
                "result": result,
                "function": producttypes.__name__,
                "user": get_current_user_ID(),
                "error": errors,
                "table": "ProductTypes",
                "entryID": entry_id,
                "request": get_request_data()
                }
            )
        return redirect(redirect_url())
    log_site_opened()
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
        # Should not be necessary ,UserID=current_user.uuid
    )
    if request.method == "POST" and form.validate_on_submit():
        result="Success"
        errors=None
        entry.Product=form.product.data
        entry.TypeID=form.typeID.data
        entry.Priority=form.priority.data
        entry.Comment=form.comment.data
        try:
            db.session.commit()
            flash("Data updated", "success")
            result="Success"
        except Exception as error:
            db.session.flush()
            flash("Data not updated", "danger")
            result="Failure"
            errors=error
        logger.warn(
            "Products data edit",
            extra={
                "action": "Database update",
                "result": result,
                "function": productsedit.__name__,
                "user": get_current_user_ID(),
                "error": errors,
                "table": "Products",
                "entryID": entry_id,
                "request": get_request_data()
                }
            )
        return redirect(redirect_url())
    log_site_opened()
    return render_template("productsedit.html", title="Products Edit", form=form)

#Manual pages ------------------------------------------------------------------

@app.route("/manbasic", methods=["GET"])
def manbasic():
    log_site_opened()
    return render_template("manbasic.html", title="Basics")

@app.route("/mandata", methods=["GET"])
def mandata():
    log_site_opened()
    return render_template("underconstruction.html", title="Basics")

@app.route("/manvisual", methods=["GET"])
def manvisual():
    log_site_opened()
    return render_template("underconstruction.html", title="Basics")

@app.route("/manaction", methods=["GET"])
def manaction():
    log_site_opened()
    return render_template("underconstruction.html", title="Basics")

@app.route("/manQnA", methods=["GET"])
def manQnA():
    log_site_opened()
    return render_template("underconstruction.html", title="Basics")

@app.route("/contact", methods=["GET"])
def contact():
    log_site_opened()
    return render_template("underconstruction.html", title="Basics")