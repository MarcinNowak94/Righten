from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Regexp, NumberRange
from datetime import date
from RightenWeb.models import *

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
    submit = SubmitField("SubmitField")

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
    source = SelectField("Source", validators=[DataRequired()],
                          choices=sources
                        )

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
    submit = SubmitField("SubmitField")