from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.widgets import TextArea

class InputForm(FlaskForm):
    list = StringField('List', widget=TextArea())
    submit = SubmitField('Submit')
