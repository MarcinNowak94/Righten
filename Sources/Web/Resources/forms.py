from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Regexp, NumberRange, InputRequired, Length, ValidationError, EqualTo
from datetime import date
from Resources.models import *

#Base class with common elements
class CommonForm(FlaskForm):
    datetime = StringField("DateTime", 
                           validators=[DataRequired(),
                                       Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])-([12][0-9]|3[01]|0?[1-9])", 
                                              message="Date must be in format: YYYY-MM-DD")
                                      ],
                           default=date.today().isoformat())
    amount = DecimalField("Amount", validators=[DataRequired()])
    comment = StringField("Comment", validators=[])
    submit = SubmitField("Submit")

#Keyword: autocomplete
#TODO: Allow new input as per https://stackoverflow.com/questions/58354678/wtforms-textfield-searchfield-with-autocompletion-for-flask-app-similar-to-a-go
class IncomeInputForm(CommonForm):
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
    #NICE-TO-HAVE: display only sources viable for specified type
    #modrej: try htmx library - based on chang in form ask backend to get new form - as per https://www.youtube.com/watch?v=L76zDuDmsuY
    source = SelectField("Source", validators=[DataRequired()],
                          choices=sources
                        )

#Keyword: autocomplete
#TODO: Allow new input as per https://stackoverflow.com/questions/58354678/wtforms-textfield-searchfield-with-autocompletion-for-flask-app-similar-to-a-go
class BillsInputForm(CommonForm):
    with app.app_context():
      medias=[]
      for medium in db.session.query(Bills.Medium).distinct():
          medias.append(medium[0])
    medium=SelectField("Medium", validators=[DataRequired()],
                          choices=medias
                        )

class ExpenditureInputForm(CommonForm):
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
    #FIXME: check for duplicates  - idea, build blacklist regex from existing data
    type= StringField("Type", validators=[DataRequired()])
    priority=IntegerField("Priority (%)", validators=[DataRequired(), NumberRange(min=1,max=100)], default=50)
    comment = StringField("Comment", validators=[])
    submit = SubmitField("SubmitField")

class ProductInputForm(FlaskForm):
    #FIXME: check for duplicates  - idea, build blacklist regex from existing data
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
class RegisterForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    #NICE-TO-HAVE: enforce better passowrd policy
    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    passwordrepeated=PasswordField(validators=[InputRequired(), Length(min=4, max=20), EqualTo('password')], render_kw={"placeholder": "Repeat password"})
    submit=SubmitField("Submit")

class LoginForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    #NICE-TO-HAVE: enforce better passowrd policy
    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit=SubmitField("Submit")

class SettingsForm(FlaskForm):
    productprioritytarget=IntegerField(validators=[InputRequired(), NumberRange(min=1,max=100)],  default=33)
    spendingtarget=DecimalField(validators=[InputRequired()],  default=1000)
    savingstarget=DecimalField(validators=[InputRequired()],  default=1000)
    accountactive=BooleanField(default=False)
    submit=SubmitField("Submit")

class PasswordChangeForm(FlaskForm):
    password=PasswordField(validators=[InputRequired(),Length(min=4, max=20)], render_kw={"placeholder": "Current password"})
    newpassword=PasswordField(validators=[InputRequired(),Length(min=4, max=20)], render_kw={"placeholder": "New password"})
    passwordrepeated=PasswordField(validators=[InputRequired(),Length(min=4, max=20), EqualTo(fieldname='newpassword', message="New password and repeated new password do not match!")], render_kw={"placeholder": "Repeat password"})
    submit=SubmitField("Submit")