from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, SubmitField, BooleanField, PasswordField, SelectMultipleField
from wtforms.validators import DataRequired, Regexp, NumberRange, InputRequired, Length, ValidationError, EqualTo
from datetime import date
from Resources.models import *
from Resources.logging_definition import logger

# TODO: MIgrate to global application configuration
MAX_VISUALIZATION_ITEMS=15

def user_valid(form, field):
    """User validator, client-side"""

    with app.app_context():
        usr=db.session.query(Users).filter_by(Username=field.data).first()
    if usr is None:
        raise ValidationError("User %s is not valid!"%(field.data))

# Based on validators.py EqualTo
class BiggerThan:
    """
    Compares the values of two fields.

    :param fieldname:
        The name of the other field to compare to.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated with `%(other_label)s` and `%(other_name)s` to provide a
        more helpful error.
    """

    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError as exc:
            raise ValidationError(
                field.gettext("Invalid field name '%s'.") % self.fieldname
            ) from exc
        if field.data > other.data:
            return

        d = {
            "other_label": hasattr(other, "label")
            and other.label.text
            or self.fieldname,
            "other_name": self.fieldname,
        }
        message = self.message
        if message is None:
            message = field.gettext("Field must be bigger than %(other_name)s.")

        raise ValidationError(message % d)

def get_PasswordField_protytpe(
        label: str, 
        placeholder: str,
        extravalidators=None
    ) -> PasswordField:
    """Single place for password field application requirements

    Arguments:
        :placeholder: -- text to display as hint

    Returns:
        Fully configured PasswordField class object with specified placeholder

    #NICE-TO-HAVE: enforce better passowrd policy
    """
    validators=[
        InputRequired(),
        Length(min=4, max=20)
        ]
    if not extravalidators is None:
        validators+=extravalidators
    
    return PasswordField(label=label, validators=validators, render_kw={"placeholder": placeholder})

class CommonForm(FlaskForm):
    """Base class with elements common to most Input forms
    
    Attributes:
        :datetime: -- ISO 8601 Date default today
        :amount: -- decimal value
        :comment: -- free text
        :submit: -- form submission button
    """

    datetime = StringField("DateTime", 
                           validators=[DataRequired(),
                                       Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])-([12][0-9]|3[01]|0?[1-9])", 
                                              message="Date must be in format: YYYY-MM-DD")
                                      ],
                           default=date.today().isoformat())
    amount = DecimalField("Amount", validators=[DataRequired()])
    comment = StringField("Comment", validators=[])
    submit = SubmitField("Submit")

class UserForm(FlaskForm):
    """Base form for handling user data

    Arguments:
        :FlaskForm: -- base class
    """
    
    username=StringField(validators=[InputRequired(), Length(min=4, max=40)], render_kw={"placeholder": "Username"})
    password=get_PasswordField_protytpe("Password", "Password")
    submit=SubmitField("Submit")

#Keyword: autocomplete
#TODO: Allow new input as per https://stackoverflow.com/questions/58354678/wtforms-textfield-searchfield-with-autocompletion-for-flask-app-similar-to-a-go
class IncomeInputForm(CommonForm):
    """Income input form, has all common fields and Income table specific fields
    
    Additional fields:
        :type: -- type of income, list populated from database
        :source: -- sources of income, list populated from database
    
    NICE-TO-HAVE: display only sources viable for specified type
    NICE-TO-HAVE: Derive new Form class - SelectField with freetext. 
    Idea for later. For now changed into StringField. 
    """
    
    """
    with app.app_context():
      types=[]
      sources=[]
      for type in db.session.query(Income.Type).distinct():
          types.append(type[0])
      for source in db.session.query(Income.Source).distinct():
          sources.append(source[0])

    type = SelectField("Type", validators=[DataRequired()],
                          choices=types,
                        )
    
    #mordej: try htmx library - based on change in form ask backend to get new form - as per https://www.youtube.com/watch?v=L76zDuDmsuY
    source = SelectField("Source", validators=[DataRequired()],
                          choices=sources
                        )
    """
    type = StringField(
                "Type", 
                validators=[DataRequired()],
                render_kw={"placeholder": "Income type"}
                )
    source = StringField(
                "Source", 
                validators=[DataRequired()],
                render_kw={"placeholder": "Income source"}
                )

# TODO: add current_user.uuid as param
class BillsInputForm(CommonForm):
    """Bills input form, has all common fields and Bill table specific fields

    Arguments:
        :CommonForm: -- Base class with elements common to most Input forms

    TODO: Allow new input as per https://stackoverflow.com/questions/58354678/wtforms-textfield-searchfield-with-autocompletion-for-flask-app-similar-to-a-go
    solution Keyword: Autocomplete
    """

    with app.app_context():
      medias=[]
      for medium in db.session.query(Bills.Medium).distinct():
                                #filter_by(UserID=current_user.uuid).distinct():\
          medias.append(medium[0])
    medium=StringField(
                "Medium", 
                validators=[DataRequired()],
                render_kw={"placeholder": "Medium"}
                )
    #medium=SelectField("Medium", validators=[DataRequired()],
    #                      choices=medias
    #                    )

class ExpenditureInputForm(CommonForm):
    """Expenditures input form, has all common fields and Expenditures table specific fields

    Arguments:
        :CommonForm: -- Base class with elements common to most Input forms
    """

    with app.app_context():
      productsquery=db.session.query(
          ProductSummary.columns.ID, 
          ProductSummary.columns.Product).\
            order_by(ProductSummary.columns.Times.desc()).all()
      products=[]
      for ID, product in productsquery:
          products.append((int(ID), str(product)))
      productID=SelectField("Product", validators=[DataRequired()],
                            choices=products
                          )
    isCash=BooleanField("Cash", default=False)

class ProductTypeInputForm(FlaskForm):
    """ProductTypes input form, all fields are ProductTypes table specific fields

    Arguments:
        :FlaskForm: -- Base class
    
    FIXME: check for duplicates  - idea, build blacklist regex from existing data or create own validator
    """
    
    type = StringField("Type", validators=[DataRequired()])
    priority = IntegerField("Priority (%)", validators=[DataRequired(), NumberRange(min=1,max=100)], default=50)
    comment = StringField("Comment", validators=[])
    submit = SubmitField("SubmitField")

class ProductInputForm(FlaskForm):
    """Product input form, all fields are Products table specific fields

    Arguments:
        :FlaskForm: -- Base class
    
    FIXME: check for duplicates  - idea, build blacklist regex from existing data or create own validator
    """
    
    with app.app_context():
      typesquery=db.session.query(
          TypeSummary.columns.ID, 
          TypeSummary.columns.Type).\
            order_by(TypeSummary.columns.Times.desc()).all()
      types=[]
      for ID, type in typesquery:
          types.append((int(ID), str(type)))
    product= StringField("Product", validators=[DataRequired()])
    typeID = SelectField("Type", validators=[DataRequired()],
                        choices=types
                      )
    priority=IntegerField("Priority (%)", validators=[DataRequired(), NumberRange(min=1,max=100)], default=50)
    comment = StringField("Comment", validators=[])
    submit = SubmitField("Submit")

#As per https://youtu.be/71EU8gnZqZQ?t=999
class RegisterForm(UserForm):
    """New user register form, has all UserForm fields and password repeated field for validation

    Arguments:
        :UserForm: -- base class
    
    Fields:
        :passwordrepeated: -- password validity check
    """

    passwordrepeated = get_PasswordField_protytpe(
                            "Password repeated",
                            "Repeat password"
                            )

class LoginForm(UserForm):
    """User login form, has all UserForm fields

    Arguments:
        :UserForm: -- base class
    """

    pass

class SettingsForm(FlaskForm):
    """User settings change form. has all Settings table specific fields.

    Arguments:
        :FlaskForm: -- base class
    """

    productprioritytarget = IntegerField(
                                label="Product priority target",
                                validators=[
                                    InputRequired(),
                                    NumberRange(min = 1,max = 100)
                                    ],
                                default = 33)
    spendingtarget = DecimalField(
                        label = "Spending target",
                        validators = [InputRequired()],
                        default = 1000)
    savingstarget = DecimalField(
                        label = "Savings target",
                        validators = [InputRequired()],
                        default = 1000)
    productsdisplaylimit = IntegerField(
                        label = "Products display limit",
                        validators = [InputRequired()],
                        default = 10)
    producttypesdisplaylimit = IntegerField(
                        label = "Product types display limit",
                        validators = [InputRequired()],
                        default = 10)
    accountactive = BooleanField(
                        label = "Account active",
                        default = False)
    submit = SubmitField(label = "Submit")

class PasswordConfirmationForm(FlaskForm):
    """Base form for password changes operations, consists of two password fields

    Arguments:
        :FlaskForm: -- base class
    
    Fields:
        :newpassword: -- new user provided password
        :passwordrepeated: -- new user password repeated for validation
    """

    newpassword = get_PasswordField_protytpe(
        "New password",
        "New password"
        )
    passwordrepeated = get_PasswordField_protytpe(
        "Password repated",
        "Repeat password",
        [EqualTo(
            fieldname = "newpassword",
            message = "New password and repeated new password do not match!")]
        )
    submit = SubmitField("Submit")

class PasswordChangeForm(PasswordConfirmationForm):
    """Password change form, consists of three password fields

    Arguments:
        :PasswordConfirmationForm: -- base class
    
    Fields:
        :password: -- current user passowrd
    """

    password = get_PasswordField_protytpe(
                    "Current password",
                    "Current password"
                    )

class PasswordResetForm(PasswordConfirmationForm):
    """Password reset form, consists of two password fields

    Arguments:
        :PasswordConfirmationForm: -- base class
    
    Fields:
        :password: -- current user passowrd
    """

    resettoken = StringField(
                    "ResetToken", 
                    validators=[DataRequired()],
                    default="Reset token"
                    )

class PasswordResetGenerateTokenForm(FlaskForm):
    """Password reset form for first stage -token generation

    Arguments:
        :FlaskForm: -- base class
    
    TODO: Add captcha
    TODO: Send token via email as per https://pythonbasics.org/flask-mail/
    """

    username = StringField(
        label = "Username",
        validators=[
            InputRequired(),
            Length(min = 4, max = 20),
            user_valid],
            render_kw={"placeholder": "Username"}
        )
    submit = SubmitField("Submit")

# FIXME: filter dates by UserID
class MonthRange_WIP(FlaskForm):
    """Month range for summaries

    Arguments:
        :FlaskForm: -- base class
    """

    with app.app_context():
        db_months = db.session.query(MonthlyExpendituresbyType.columns.Month).\
                                    order_by(MonthlyExpendituresbyType.columns.Month).\
                                    distinct()
                                        #filter_by(UserID=current_user.uuid)
        monthsoptions=[]
        first_month=str(db_months[0][0])
        last_month=str(db_months[db_months.count()-1][0])
        for Month in db_months:
            monthsoptions.append(str(Month[0]))
    minmonth = SelectField("Min month", validators=[DataRequired()],
                    choices = monthsoptions,
                    default = last_month)
    maxmonth = SelectField("Max month", validators=[DataRequired(),
                                    BiggerThan(fieldname = "minmonth")],
                    choices = monthsoptions,
                    default = last_month)

class MonthRange(FlaskForm):
    """Month range for summaries

    Arguments:
        :FlaskForm: -- base class
    """

    minmonth = StringField("Start date", 
                        validators=[
                            DataRequired(),
                            Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])", 
                                message="Date must be in format: YYYY-MM")
                            ],
                        # TODO: Get default via argument or initialize properly
                        default=str(date.today().isoformat())[:7]) 
    maxmonth = StringField("End date", 
                        validators=[
                            DataRequired(),
                            Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])", 
                                message="Date must be in format: YYYY-MM"),
                            BiggerThan(fieldname = "minmonth")
                            ],
                        # TODO: Get default via argument or initialize properly
                        default=str(date.today().isoformat())[:7])
    submit=SubmitField("Submit")

class DateRange(FlaskForm):
    """Date range for summaries

    Arguments:
        :FlaskForm: -- base class
    """

    mindate = StringField("Start date", 
                        validators=[
                            DataRequired(),
                            Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])-([12][0-9]|3[01]|0?[1-9])", 
                                message="Date must be in format: YYYY-MM-DD")
                            ],
                        # TODO: Get default via argument or initialize properly
                        default=date.today().isoformat()) 
    maxdate = StringField("End date", 
                        validators=[
                            DataRequired(),
                            Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])-([12][0-9]|3[01]|0?[1-9])", 
                                message="Date must be in format: YYYY-MM-DD"),
                            BiggerThan(fieldname = "mindate")
                            ],
                        # TODO: Get default via argument
                        default=date.today().isoformat())
    submit=SubmitField("Submit")

# FIXME: filter products by UserID
class ProductVisualizationForm(MonthRange):
    """Product summary visualization form, decides which products data are 
    selected from database to be visualized

    Arguments:
        :MonthRange: -- base class
    """

    with app.app_context():
        user_products_count = db.session.query(
                                            ProductSummary.columns.Product,
                                            ProductSummary.columns.Amount).count()
                                        #filter_by(UserID=current_user.uuid)
        user_products = db.session.query(Products.Product).all()
                                        #filter_by(UserID=current_user.uuid)
        top10_user_products = db.session.query(ProductSummary.columns.Product).\
                                        order_by(ProductSummary.columns.Times).\
                                        limit(10) #TODO: Populate from user setting
    choices = []
    for product in user_products:
        choices.append(product[0])

    limit = IntegerField(
                validators=[
                    InputRequired(),
                    # Setting reasonable limit, otherwise graph gets too crowded 
                    NumberRange(
                        min = 1,
                        max = MAX_VISUALIZATION_ITEMS 
                              if user_products_count > MAX_VISUALIZATION_ITEMS
                              else user_products_count
                        )
                    ],
                default = 10) #TODO: Fill in from ProductsDisplayLimit user setting 
    products = SelectMultipleField(
                    choices = choices,
                    default = top10_user_products)
    # MonthRange already has Submit

# FIXME: filter types by UserID
class TypeVisualizationForm(MonthRange):
    """Type summary visualization form, decides which types data are 
    selected from database to be visualized

    Arguments:
        :FlaskForm: -- base class
    """

    with app.app_context():
        user_types_count = db.session.query(TypeSummary.columns.Type,
                                            TypeSummary.columns.Amount).count()
                                        #filter_by(UserID=current_user.uuid)
        user_types = db.session.query(ProductTypes.Type).all()
                                        #filter_by(UserID=current_user.uuid)
        top10_user_types = db.session.query(TypeSummary.columns.Type).\
                                        order_by(TypeSummary.columns.Times).\
                                        limit(10)  #TODO: Populate from user setting
    choices = []
    for type in user_types:
        choices.append(type[0])

    limit = IntegerField(
                validators=[
                    InputRequired(),
                    # Setting reasonable limit, otherwise graph gets too crowded 
                    NumberRange(
                        min = 1,
                        max = MAX_VISUALIZATION_ITEMS
                              if user_types_count > MAX_VISUALIZATION_ITEMS
                              else user_types_count
                        )
                    ])
    types = SelectMultipleField(
                    choices = choices,
                    default = top10_user_types)
    submit = SubmitField("Submit")
    # MonthRange already has Submit

# FIXME: filter types by UserID
class MonthInputForm(FlaskForm):
    """Month summary form, decides which month data is displayed

    Arguments:
        :FlaskForm: -- base class
    """

    with app.app_context():
        db_months = db.session.query(MonthlyExpendituresbyType.columns.Month).\
                                    order_by(MonthlyExpendituresbyType.columns.Month).\
                                    distinct()
                                        #filter_by(UserID=current_user.uuid)
        monthsoptions=[]
        last_month=str(db_months[db_months.count()-1][0])
        for Month in db_months:
            monthsoptions.append(str(Month[0]))
    months = SelectField("Month", validators=[DataRequired()],
                    choices = monthsoptions,
                    default = last_month)
    submit = SubmitField("Submit")