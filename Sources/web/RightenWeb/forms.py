from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Regexp, NumberRange
from datetime import date

#Base class with common elements
class CommonForm(FlaskForm):
    datetime = StringField("DateTime", 
                           validators=[DataRequired(),Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])-([12][0-9]|3[01]|0?[1-9])", message="Date must be in format: YYYY-MM-DD")],
                           default=date.today().isoformat())
    amount = DecimalField("Amount", validators=[DataRequired()])
    comment = StringField("Comment", validators=[])
    submit = SubmitField("SubmitField")

class IncomeInputForm(CommonForm):
    type = SelectField("Type", validators=[DataRequired()],
                          choices=[
                            #TODO: Get valid types form DB
                              "Praca",
                              "Premia",
                              "Sprzedaż", 
                              "Inwestycje", 
                              "Zwrot"
                          ]
                          #TODO: Set default based on DB data - most used 
                        )
    source = SelectField("Source", validators=[DataRequired()],
                          choices=[
                              #TODO: Get Valid sources from DB
                              #TODO: Allow freetext to add new option
                              "Praca1", 
                              "Praca2", 
                              "Praca3", 
                              "Praca4"
                          ],
                          #TODO: Set default based on DB data - most used, based on type
                          default="Praca"
                        )

class BillsInputForm(CommonForm):
    medium=SelectField("Medium", validators=[DataRequired()],
                          choices=[
                                    #TODO: Get Valid sources from DB
                                    #TODO: Allow freetext to add new option
                                    "Medium1", 
                                    "Medium2", 
                                    "Medium3", 
                                    "Medium4"
                          ],
                          #TODO: Set default based on DB data - most used
                          default="Medium1"
                        )

class ExpenditureInputForm(CommonForm):
    product=SelectField("Product", validators=[DataRequired()],
                          choices=[
                                    #TODO: Get Valid sources from DB
                                    "Product1", 
                                    "Product2", 
                                    "Product3", 
                                    "Product4"
                          ],
                          #TODO: Set default based on DB data - most used
                          default="Product1"
                        )

class ProductTypeInputForm(FlaskForm):
    #FIXME: check for duplicates
    type= StringField("Type", validators=[DataRequired()])
    priority=IntegerField("Priority", validators=[DataRequired(), NumberRange(min=1,max=10)], default=5)
    comment = StringField("Comment", validators=[])
    submit = SubmitField("SubmitField")
class ProductInputForm(FlaskForm): 
    #FIXME: check for duplicates
    product= StringField("Product", validators=[DataRequired()])
    typeID = SelectField("TypeID", validators=[DataRequired()],
                        choices=[
                                  #TODO: Get valid types form DB
                                    ("Type1", 1),
                                    ("Type2", 2),
                                    ("Type3", 3),
                                    ("Type4", 4)
                        ],
                        #TODO: Set default based on DB data - most used
                        default=("Type1", 1)
                      )
    priority=IntegerField("Priority", validators=[DataRequired(), NumberRange(min=1,max=10)], default=5)
    comment = StringField("Comment", validators=[])
    submit = SubmitField("SubmitField")
