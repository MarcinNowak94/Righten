from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Regexp
from datetime import date

class IncomeInputForm(FlaskForm):
    datetime = StringField("DateTime", 
                           validators=[DataRequired(),Regexp("((?:19|20)\\d\\d)-(0?[1-9]|1[012])-([12][0-9]|3[01]|0?[1-9])", message="Date must be in format: YYYY-MM-DD")],
                           default=date.today().isoformat())
    source = SelectField("Source", validators=[DataRequired()],
                          choices=[
                                    #TODO: Get Valid sources from DB
                                    #TODO: Allow freetext to add new option
                                    ("Praca1", "Praca1"),
                                    ("Praca2", "Praca2"),
                                    ("Praca3", "Praca3"),
                                    ("Praca4", "Praca4")
                          ],
                          #TODO: Set default based on DB data - most used, based on type
                          default="Praca"
                        )
    type = SelectField("Type", validators=[DataRequired()],
                          choices=[
                                    #TODO: Get valid types form DB
                                    ("Praca", "Praca"),
                                    ("Premia", "Premia"),
                                    ("Sprzedaż", "Sprzedaż"),
                                    ("Inwestycje", "Inwestycje"),
                                    ("Zwrot", "Zwrot"),
                                    ("ProductTypes", "ProductTypes")
                          ]
                          #TODO: Set default based on DB data - most used 
                        )
    
    #NICE-TO-HAVE: Alert if amount is unusual
    amount = DecimalField("Amount", validators=[DataRequired()])
    comment = StringField("Comment", validators=[])

    submit = SubmitField("SubmitField")