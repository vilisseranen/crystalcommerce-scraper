from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.widgets import TextArea, ListWidget, CheckboxInput
from wtforms import SelectMultipleField

from app.mtg_scraper import STORES, LANGUAGES, CONDITIONS



class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class InputForm(FlaskForm):
    languages_options = [(language_short, language_long) for language_short, language_long in LANGUAGES.items()]
    stores_options = [(store['abbr'], store['name']) for store in STORES]
    conditions_options = [(condition_short, condition_long) for condition_short, condition_long in CONDITIONS.items()]

    list = StringField('List', widget=TextArea())
    languages = MultiCheckboxField('Languages', choices=languages_options)
    stores = MultiCheckboxField('Stores', choices=stores_options)
    conditions = MultiCheckboxField('Stores', choices=conditions_options)
    submit = SubmitField('Submit')