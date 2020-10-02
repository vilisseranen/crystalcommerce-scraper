from app import app
from app.list import InputForm

from flask import render_template, flash, redirect

from app.mtg_scraper import read_and_encode_wishlist, retrieve_cards_info, build_buylist
from app.mtg_scraper import STORES, LANGUAGES, CONDITIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    selected_stores = STORES
    listForm = InputForm()
    cardsInfo = None
    buylist = None
    if listForm.validate_on_submit():
        query = read_and_encode_wishlist(
            card=listForm.list.data, file=None)
        cardsInfo = retrieve_cards_info(query)
    if cardsInfo:
        buylist = build_buylist(cardsInfo, None, None)
    return render_template('index.html', form=listForm, cardList=buylist, stores=selected_stores)
