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
from Resources.getdata import *
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
        "fullpath": request.full_path                    
    }

def get_current_user_ID() -> str:
    """Get current user id or None"""
    
    try:
        userid=current_user.uuid
    except AttributeError:
        userid=None
    return userid

def log_site_opened(params=None) -> None:
    """Logs that site was opened by user

    Arguments:
        :params: -- variables used while displaying site
    """
    
    logger.info(
        "User visited site",
        extra={
            "action": "Site visited",
            "result": "Success",
            "user": get_current_user_ID(),
            "request": get_request_data(),
            "params": params
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

    success = False
    success = addtodb(user, notify=True)
    operations={
        "UserCreation" : success
    }

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
            sets[set].append({"x": Month, "y": Amount if Type==set else 0})

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

#FIXME: Temporary function, genralize it and refactor 
def createchartdatasetMonthlyBilanceSummary(dbdata: list, fill="false") -> list:
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
            sets[set].append({"x": Month, "y": Amount if Type==set else 0})

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
            # Some datasets contain negative values
            total+=abs(value)
        #sum=sum(value for label, value in data)

    for label, value in data:
        if addperc is True:
            # Some datasets contain negative values
            # FIXME: Crashes when there is no data in Type field
            label+=" "+str(round((abs(value)/total)*100))+"%"
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

def createpiechartdatasethorizontal(
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
        for row in data:
            for column in row:
                # Some datasets contain negative values
                    total+=abs(column)
        #sum=sum(value for label, value in data)

    for row in data:
        for column in row:
            if addperc is True:
                # Some datasets contain negative values
                # FIXME: Crashes when there is no data in Type field
                label+=" "+str(round((abs(column)/total)*100))+"%"
            labels.append(label)
            values.append(column)

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

def getuserdata(checkeduser):
    if checkeduser is None:
        return
    userdbdata=getUserbyName(checkeduser)
    if userdbdata is not None:
        #TODO: Check if whole userentry can be moved here
        #possible issue: it can be na active session maintained for the duration of user interaction
        #possible issue: user object containing password stored in memory  
        user = User()
        user.id = checkeduser
        user.uuid = userdbdata.ID
        return user
    return
# NICE-TO-HAVE: Load all user settings here
# Used for UI single login for session
@login_manager.user_loader
def user_loader(checkeduser):
    return getuserdata(checkeduser)

# Used for api key or basic authentication (auth required on every request)
@login_manager.request_loader
def request_loader(request):
    checkeduser=request.form.get('email')
    return getuserdata(checkeduser)

# TODO: Use native mechanisms, i.e.: user.is_active = 
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        username = form.username.data
        usr = getUserbyName(username)
        errors = {}
        
        # Silent check tree
        if usr is None:
            errors["User exist"]=False
        else:
            if not usr.isActive:
                errors["User is active"]=False
            if not check_password(usr, form.password.data):
                errors["Password is valid"]=False
            if get_current_user_ID() is not None:
                errors["User already logged in during session"]=False

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

# NICE-TO-HAVE: Refactor - move all settings to user entry
@app.route('/settings', methods=['GET', 'POST'])
@flask_login.login_required
def settings():
    result="Success"
    changeerror=None
    settingschanged=[]

    # Function usage removed - if not done directly, settings are not commited to database
    userentry = db.one_or_404(db.session.query(Users).filter_by(ID=current_user.uuid)) #getUserbyID(current_user.uuid)
    
    form=SettingsForm(
        productprioritytarget=Decimal(userentry.ProductPriorityTarget),
        spendingtarget=Decimal(userentry.SpendingTarget),
        savingstarget=Decimal(userentry.SavingsTarget),
        accountactive=bool(userentry.isActive),
        productsdisplaylimit=int(userentry.ProductsDisplayLimit),
        producttypesdisplaylimit=int(userentry.ProductTypesDisplayLimit)
    )
    
    # TODO: Refactor all as one separate function, next step - figure out a way to do it as one general loop
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
        if form.productprioritytarget.data and form.productprioritytarget.data!=Decimal(userentry.ProductPriorityTarget):
            change = {}
            change["setting"] = "Priority target"
            change["oldvalue"] = userentry.ProductPriorityTarget
            change["newvalue"] = form.productprioritytarget.data

            userentry.ProductPriorityTarget=form.productprioritytarget.data
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

        if form.spendingtarget.data and form.spendingtarget.data!=Decimal(userentry.SpendingTarget):
            change = {}
            change["setting"] = "Spending target"
            change["oldvalue"] = userentry.SpendingTarget
            change["newvalue"] = form.spendingtarget.data

            userentry.SpendingTarget=str(form.spendingtarget.data)
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

        if form.savingstarget.data and form.savingstarget.data!=Decimal(userentry.SavingsTarget):
            change = {}
            change["setting"] = "Savings target"
            change["oldvalue"] = userentry.SavingsTarget
            change["newvalue"] = form.savingstarget.data
            
            userentry.SavingsTarget=str(form.savingstarget.data)
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
        
        if form.productsdisplaylimit.data and form.productsdisplaylimit.data!=Decimal(userentry.ProductsDisplayLimit):
            change = {}
            change["setting"] = "Products display limit"
            change["oldvalue"] = userentry.ProductsDisplayLimit
            change["newvalue"] = form.productsdisplaylimit.data
            
            userentry.ProductsDisplayLimit=str(form.productsdisplaylimit.data)
            try:
                db.session.commit()
                flash("Products display limit updated", "success")
                result="Success"
            except Exception as error:
                db.session.flush()
                flash("Products display limit not updated", "danger")
                result="Failure"
                changeerror=error
            pass
            
            change["result"] = result
            change["error"] = changeerror
            settingschanged.append(change)
        
        if form.producttypesdisplaylimit.data and form.producttypesdisplaylimit.data!=Decimal(userentry.ProductTypesDisplayLimit):
            change = {}
            change["setting"] = "Products display limit"
            change["oldvalue"] = userentry.ProductTypesDisplayLimit
            change["newvalue"] = form.producttypesdisplaylimit.data
            
            userentry.ProductTypesDisplayLimit=str(form.producttypesdisplaylimit.data)
            try:
                db.session.commit()
                flash("Products types display limit updated", "success")
                result="Success"
            except Exception as error:
                db.session.flush()
                flash("Products types display limit not updated", "danger")
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

# FIXME: Solely for proving concept
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

# NICE-TO-HAVE: add email password change confirmation
@app.route('/passwordchange', methods=['GET', 'POST'])
@flask_login.login_required
def passwordchange():
    form = PasswordChangeForm()
    
    if request.method == "POST" and form.validate_on_submit():
        userentry = getUserbyID(current_user.uuid)
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

# Summaries and visualizations -------------------------------------------------
# NICE-TO-HAVE: Repork incomesummary, billssummary, expendituressummary as 
# generic summary function reffered to via eg. url_for('summary', table='Income').
# Needs to be extensible to let them develop separately in future (as expenditures did) 

# NICE-TO-HAVE: Stacked year graph
@app.route("/incomesummary", methods=['GET', 'POST'])
@flask_login.login_required
def incomesummary():
    form=MonthRange()
    range=getTimeRangeMonth(MonthlyBilance, current_user.uuid)
    # TODO: initialize properly inside class, this is quick and dirty way
    if request.method == "GET":
        form.minmonth.data = range.beginning
        form.maxmonth.data = range.end

    if request.method == "POST" and form.validate_on_submit():
        range.beginning = form.minmonth.data
        range.end = form.maxmonth.data
    
    summary = getDataFromTableforUser(IncomeSummary, current_user.uuid)
    IncomeSummarydata = getSummaryByColumnGrouped(
                            MonthlyIncomeByType,
                            current_user.uuid,
                            range,
                            "Type")
    
    IncomeOverTime = getMonthlySummaryByColumn(MonthlyBilance, current_user.uuid, range, "Income")
    IncomeTypesByTime = getMonthlySummaryByColumn(MonthlyIncomeByType, current_user.uuid, range, "Type")
    
    IncomeTypechart=createpiechartdataset(IncomeSummarydata, addperc=True)
    IncomeTypesByTimeDataset=createchartdataset(IncomeTypesByTime)

    #TODO: Start chart at 0 - negative income is not an acceptable input
    monthlyincomedata = []
    for month, amount in IncomeOverTime:
        monthlyincomedata.append({"x": month, "y": amount})

    log_site_opened()
    return render_template("incomesummary.html",
                           title="Income",
                           IncomeTypechart=json.dumps(IncomeTypechart, cls=DecimalEncoder),
                           MonthlyIncome=json.dumps(monthlyincomedata, cls=DecimalEncoder),
                           IncomeTypesByTimeDataset=json.dumps(IncomeTypesByTimeDataset, cls=DecimalEncoder),
                           Summary=summary,
                           form=form
                           )

@app.route("/billssummary", methods=['GET', 'POST'])
@flask_login.login_required
def billssummary():
    form=MonthRange()
    range=getTimeRangeMonth(MonthlyBilance, current_user.uuid)
    # TODO: initialize properly inside class, this is quick and dirty way
    if request.method == "GET":
        form.minmonth.data = range.beginning
        form.maxmonth.data = range.end

    if request.method == "POST" and form.validate_on_submit():
        range.beginning = form.minmonth.data
        range.end = form.maxmonth.data
    
    summary = getDataFromTableforUser(BillsSummary, current_user.uuid)
    BillsSummarydata = getSummaryByColumnGrouped(
                            MonthlyBillsByMedium,
                            current_user.uuid,
                            range,
                            "Medium")
    BillsOverTime = getMonthlySummaryByColumn(MonthlyBilance, current_user.uuid, range, "Bills")
    BillsTypesByTime = getMonthlySummaryByColumn(MonthlyBillsByMedium, current_user.uuid, range, "Medium")
    
    
    bills_type_chart = createpiechartdataset(BillsSummarydata, addperc=True)
    bills_types_data = createchartdataset(BillsTypesByTime)
    monthly_bills_data = []
    for month, amount in BillsOverTime:
        monthly_bills_data.append({"x": month, "y":amount})

    log_site_opened()
    return render_template("billssummary.html",
                           title="Bills",
                           BillsTypechart=json.dumps(bills_type_chart, cls=DecimalEncoder),
                           MonthlyBillsData=json.dumps(monthly_bills_data, cls=DecimalEncoder),
                           BillsTypesData=json.dumps(bills_types_data, cls=DecimalEncoder),
                           Summary=summary,
                           form=form
                           )

@app.route("/expendituressummary", methods=['GET', 'POST'])
@flask_login.login_required
def expendituressummary():
    form=MonthRange()
    range=getTimeRangeMonth(MonthlyBilance, current_user.uuid)
    # TODO: initialize properly inside class, this is quick and dirty way
    if request.method == "GET":
        form.minmonth.data = range.beginning
        form.maxmonth.data = range.end

    if request.method == "POST" and form.validate_on_submit():
        range.beginning = form.minmonth.data
        range.end = form.maxmonth.data
    
    ExpendituresSummarydata = getSummaryByColumnGrouped(
                                MonthlyExpendituresbyType,
                                current_user.uuid,
                                range,
                                "Type")
    ExpendituresOverTime = getMonthlySummaryByColumn(
                                MonthlyBilance,
                                current_user.uuid,
                                range,
                                "Expenditures")
    TopTypeExpendituresData = getMonthlyTopExpenditures(
                                Top10ProductTypesMonthly,
                                current_user.uuid,
                                range,
                                "Type")
    TopProductsChartData = getMonthlyTopExpenditures(
                                Top10ProductsMonthly,
                                current_user.uuid,
                                range,
                                "Product")
    SpendingTargetValue = getUserbyID(current_user.uuid).SpendingTarget

    expenditures_summary_chart = createpiechartdataset(ExpendituresSummarydata, addperc=True)
    TopTypeExpenditures=createchartdataset(TopTypeExpendituresData, "true")
    TopProductsExpenditures=createchartdataset(TopProductsChartData, "true")
    MonthlyExpendituresData=[]
    SpendingTarget=[]
    
    for Month, Amount in ExpendituresOverTime:
        MonthlyExpendituresData.append({"x":Month,"y":Amount})
        SpendingTarget.append({"x":Month,"y":SpendingTargetValue})
    
    ExpendituresSet=[]
    ExpendituresSet.append({"label": "Exenditures", "data": MonthlyExpendituresData})
    ExpendituresSet.append({"label": "Spending target", "data": SpendingTarget})
    
    log_site_opened()
    return render_template("expendituressummary.html",
                           title="Expenditures",
                           ExpendituresSet=json.dumps(ExpendituresSet, cls=DecimalEncoder),
                           ExpendituresSummaryChart=json.dumps(expenditures_summary_chart, cls=DecimalEncoder),
                           TopTypeExpenditures=json.dumps(TopTypeExpenditures, cls=DecimalEncoder),
                           TopProductsExpenditures=json.dumps(TopProductsExpenditures, cls=DecimalEncoder),
                           form=form
                           )

# NICE-TO-HAVE: Add stacked year graph to show trend
# NICE-TO-HAVE: Add averages per Bills and Expenditures for specified timeframe
@app.route("/spending", methods=['GET', 'POST'])
@flask_login.login_required
def spending():
    form=MonthRange()
    range=getTimeRangeMonth(MonthlyBilance, current_user.uuid)
    # TODO: initialize properly inside class, this is quick and dirty way
    if request.method == "GET":
        form.minmonth.data = range.beginning
        form.maxmonth.data = range.end

    if request.method == "POST" and form.validate_on_submit():
        range.beginning = form.minmonth.data
        range.end = form.maxmonth.data
    
    Spending = getMonthRangeDataFromTableforUser(
                    MonthlySpending,
                    current_user.uuid,
                    range
                    )
    
    # All settings are stored as text, thus type cast to int
    PriorityTarget = getUserbyID(current_user.uuid).ProductPriorityTarget
    
    SpendingTarget = getUserbyID(current_user.uuid).SpendingTarget

    MonthlySpendingData=[]
    CashPercentageData=[]
    MonthlyPossibleSavingsData=[]
    ProductPriorityData=[]
    TypePriorityData=[]
    SpendingTargetData=[]
    PriorityTargetData=[]
    total_possible_savings = 0
    for UserID, Month, Total, CashPercentage, AverageProductPriority, AverageTypePriority, PossibleSavings, AverageDaily in Spending:
        MonthlySpendingData.append({"x":Month,"y":Total})
        CashPercentageData.append({"x":Month,"y":CashPercentage})        
        MonthlyPossibleSavingsData.append({"x":Month,"y":PossibleSavings})
        total_possible_savings+=PossibleSavings
        ProductPriorityData.append({"x":Month,"y":AverageProductPriority})
        TypePriorityData.append({"x":Month,"y":AverageTypePriority})
        
        # Priority target describes which products are deemed as unnecessary expense
        # Priority data is average of month priorities, thus target priority is 100-target  
        PriorityTargetData.append({"x":Month,"y":100-PriorityTarget})
        SpendingTargetData.append({"x":Month,"y":SpendingTarget})
    
    log_site_opened()
    return render_template("spendingsummary.html",
                           title="Spending",
                           MonthlySpendingData=json.dumps(MonthlySpendingData, cls=DecimalEncoder),
                           CashPercentageData=json.dumps(CashPercentageData, cls=DecimalEncoder),
                           MonthlyPossibleSavingsData=json.dumps(MonthlyPossibleSavingsData, cls=DecimalEncoder),
                           ProductPriorityData=json.dumps(ProductPriorityData, cls=DecimalEncoder),
                           TypePriorityData=json.dumps(TypePriorityData, cls=DecimalEncoder),
                           PriorityTargetData=json.dumps(PriorityTargetData, cls=DecimalEncoder),
                           SpendingTargetData=json.dumps(SpendingTargetData, cls=DecimalEncoder),
                           total_possible_savings=round(total_possible_savings,2),
                           form=form
                           )

# NICE-TO-HAVE: green color above SavingsTarget 
@app.route("/finances", methods=['GET', 'POST'])
@flask_login.login_required
def finances():
    form=MonthRange()
    range=getTimeRangeMonth(MonthlyBilance, current_user.uuid)
    # TODO: initialize properly inside class, this is quick and dirty way
    if request.method == "GET":
        form.minmonth.data = range.beginning
        form.maxmonth.data = range.end

    if request.method == "POST" and form.validate_on_submit():
        range.beginning = form.minmonth.data
        range.end = form.maxmonth.data
    # NICE-TO-HAVE: Add statistic type, and get only financial here
    StatisticData = getDataFromTableforUser(Statistics, current_user.uuid)
    BilanceData = getMonthRangeDataFromTableforUser(
                    MonthlyBilance,
                    current_user.uuid,
                    range)

    BilanceTotal= getMonthlyBilanceSummaryforUser(
                        MonthlyBilance,
                        current_user.uuid,
                        range)
    SavingsTargetData = getUserbyID(current_user.uuid).SavingsTarget
    
    bilance=[]
    Breakeven=[]
    BilanceSet=[]
    SavingsTarget=[]
    sets = {
        "Bilance": bilance,
        "Breakeven": Breakeven,
        "Savings Target": SavingsTarget
        #TODO: Add savings rate here
        }
    income=[]
    expenditures=[]
    bills=[]
    BilanceSourcesData=[]
    BilanceSources = {
        "Income": income,
        "Expenditures": expenditures,
        "Bills": bills
    }

    #Adding breakeven line 
    for UserID, Month, Income, Expenditures, Bills, Bilance, SavingsRate in BilanceData:
        bilance.append({"x":Month,"y":Bilance})
        Breakeven.append({"x":Month,"y":0})
        SavingsTarget.append({"x":Month,"y":SavingsTargetData})
        income.append({"x":Month,"y":Income})
        expenditures.append({"x":Month,"y":Expenditures})
        bills.append({"x":Month,"y":Bills})

    for set in sets:
        BilanceSet.append({"label": set, "data": sets[set]})
    for source in BilanceSources:
        BilanceSourcesData.append({"label": source, "data": BilanceSources[source]})
   
    BilanceTotalchart=createpiechartdataset(BilanceTotal, addperc=True)
    log_site_opened()
    return render_template("financialposture.html",
                           title="Finances",
                           BilanceTotalchart=json.dumps(BilanceTotalchart, cls=DecimalEncoder),
                           BilanceSourcesData=json.dumps(BilanceSourcesData, cls=DecimalEncoder),
                           BilanceData=json.dumps(BilanceSet, cls=DecimalEncoder),
                           StatisticData=StatisticData,
                           form=form
                           )

# NICE-TO-HAVE: Refactor productssummary and producttypessummary into one view
# NICE-TO-HAVE: Add panels:
# - Product priority over time
# - spending by Product (move from expenditures?)
# - Top 10 low priority product spending Calculate (Amount*(100-priority))
# TODO: Calculate all data within specified timeframe - requires moving whole db ProductSummary view logic to getdata.py (hard)
# NICE-TO-HAVE: add Show outiers/Show uncommon control and ignore specific records 
@app.route("/productssummary", methods=['GET', 'POST'])
@flask_login.login_required
def productssummary():
    form = ProductVisualizationForm() # Extends MonthRange
    range = getTimeRangeMonth(MonthlyProducts, current_user.uuid)
    limit = getUserbyID(current_user.uuid).ProductsDisplayLimit
    selected_products = []

    # TODO: initialize properly inside class, this is quick and dirty way
    if request.method == "GET":
        form.minmonth.data = range.beginning
        form.maxmonth.data = range.end
    
    if request.method == "POST" and form.validate_on_submit():
        limit = form.limit.data
        selected_products = form.products.data
        range.beginning = form.minmonth.data
        range.end = form.maxmonth.data

    top_products = getTopNProductOrTypesforUser(
                        ProductSummary,
                        current_user.uuid,
                        "Product",
                        limit
                        )
    selection_products_list = (product for product, amount in top_products)
    selected_products.extend(selection_products_list)
    form.products.default = selected_products # Set all displayed products as chosen

    chosen_products = getSpecifiedProductsOrTypesforUser(
                        ProductSummary,
                        current_user.uuid,
                        "Product",
                        selected_products
                        )

    monthly_products = getMonthlySummarySubsetByColumn(
                        MonthlyProducts,
                        current_user.uuid,
                        range,
                        "Product",
                        selected_products
                        )
    products_table = getDataSubsetFromTableforUser(
                        ProductSummary,
                        current_user.uuid,
                        "Product",
                        selected_products
                        )
    
    # Combine top products and selected products data
    top_products_chart = createpiechartdataset(chosen_products, addperc=True)
    top_products_line = createchartdataset(monthly_products)

    params={
        "limit": limit,
        "selectedproducts": selected_products,
        "minmonth": range.beginning,
        "maxmonth": range.end
    }

    log_site_opened(params=params)
    return render_template("productsummary.html",
                        title="Products",
                        top_products_chart=json.dumps(top_products_chart, cls=DecimalEncoder),
                        top_products_line=json.dumps(top_products_line, cls=DecimalEncoder),
                        entries=products_table,
                        form=form
                        )

# TODO: Calculate all data within specified timeframe - requires moving whole db ProductSummary view logic to getdata.py (hard)
# NICE-TO-HAVE: add Show outiers/Show uncommon control and ignore specific records 
@app.route("/producttypessummary", methods=['GET', 'POST'])
@flask_login.login_required
def producttypessummary():
    form=TypeVisualizationForm()
    range=getTimeRangeMonth(MonthlyBilance, current_user.uuid)
    limit = getUserbyID(current_user.uuid).ProductTypesDisplayLimit
    selected_types=[]

    # TODO: initialize properly inside class, this is quick and dirty way
    if request.method == "GET":
        form.minmonth.data = range.beginning
        form.maxmonth.data = range.end

    if request.method == "POST" and form.validate_on_submit():
        limit = form.limit.data
        selected_types = form.types.data
        range.beginning = form.minmonth.data
        range.end = form.maxmonth.data

    top_types = getTopNProductOrTypesforUser(
                        TypeSummary,
                        current_user.uuid,
                        "Type",
                        limit
                        )

    selection_types_list = (type for type, amount in top_types)
    selected_types.extend(selection_types_list)
    form.types.default=selected_types # Set all displayed types as chosen

    chosen_types = getSpecifiedProductsOrTypesforUser(
                        TypeSummary,
                        current_user.uuid,
                        "Type",
                        selected_types
                        )

    monthly_types = getMonthlySummarySubsetByColumn(
                        MonthlyProductTypes,
                        current_user.uuid,
                        range,
                        "Type",
                        selected_types
                        )
    types_table = getDataSubsetFromTableforUser(
                        TypeSummary,
                        current_user.uuid,
                        "Type",
                        selected_types
                        )
    
    top_types_chart = createpiechartdataset(chosen_types, addperc=True)
    top_types_line = createchartdataset(monthly_types)

    params={
        "limit": limit,
        "selectedtypes": selected_types,
        "minmonth": range.beginning,
        "maxmonth": range.end
    }

    log_site_opened(params=params)
    return render_template("typesummary.html",
                        title="types",
                        top_types_chart=json.dumps(top_types_chart, cls=DecimalEncoder),
                        top_types_line=json.dumps(top_types_line, cls=DecimalEncoder),
                        entries=types_table,
                        form=form
                        )

#TODO: fill in
#TODO: Add current month bills pie chart
@app.route("/month", methods=["GET", "POST"])
@flask_login.login_required
def month():
    #Expenditures pie chart "SELECT * FROM Month" 
    #MonthlyBilance table
    #Unnecessary productsBought(Group by Product)
    #MonthlySpending
    
    form = MonthInputForm()
    range = getTimeRangeMonth(MonthlyExpendituresbyType, current_user.uuid)
    if request.method == "GET":
        range.beginning = range.end # To get only one months data
        chosenmonth = range.end

    if form.validate_on_submit():
        range.beginning = range.end = form.months.data
        chosenmonth = form.months.data

    typespendingdata = getSummaryByColumnGrouped(
                        MonthlyExpendituresbyType,
                        current_user.uuid,
                        range,
                        "Type"
                        )
    bilancedata = getMonthRangeDataFromTableforUser(
                        MonthlyBilance,
                        current_user.uuid,
                        range
                        )
    netresult=0
    for record in bilancedata:
        netresult += record.Amount #NICE-TO-HAVE: sum in more pytonic way 

    unnecessaryproducts = getMonthRangeDataFromTableforUser(
                            UnnecessaryProductsBought,
                            current_user.uuid,
                            range)
    
    possiblesavings=0
    for record in unnecessaryproducts:
        possiblesavings += record.Amount #NICE-TO-HAVE: sum in more pytonic way 
    
    typespendingchart=createpiechartdataset(typespendingdata, addperc=True)

    log_site_opened()
    return render_template("month.html",
                           title="Month summary",
                           typespending=json.dumps(typespendingchart, cls=DecimalEncoder),
                           bilancedata=bilancedata,
                           unnecessaryproducts=unnecessaryproducts,
                           possiblesavings=round(possiblesavings,2),
                           netresult=round(netresult,2),
                           form=form)

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