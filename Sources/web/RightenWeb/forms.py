from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class IncomeInputForm(FlaskForm):
    product = SelectField("Product", validators=[DataRequired()],
                          choices=[
                                    ("Product1", "Product1"),
                                    ("Product2", "Product2"),
                                    ("Product3", "Product3"),
                                    ("Product4", "Product4")
                          ]
                        )
    table = SelectField("Table", validators=[DataRequired()],
                          choices=[
                                    ("Income", "Income"),
                                    ("Bills", "Bills"),
                                    ("Expenditures", "Expenditures"),
                                    ("Products", "Products"),
                                    ("ProductTypes", "ProductTypes")
                          ]
                        )
    
    amount = IntegerField("Amount", validators=[DataRequired()])

    comment = StringField("Comment", validators=[])

    submit = SubmitField("SubmitField")