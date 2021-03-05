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
        languages_filter = listForm.languages.data if listForm.languages.data else None
        conditions_filter = listForm.conditions.data if listForm.conditions.data else None
        buylist = build_buylist(cardsInfo, languages_filter, conditions_filter) # We should filter by store here or before
        selected_stores = [store for store in STORES if store['abbr'] in listForm.stores.data]
        non_selected_stores = [store for store in STORES if store['abbr'] not in listForm.stores.data]
        totals = {store['abbr']: 0 for store in selected_stores}
        for card, stores in buylist.items():
            ## remove non selected stores
            for store in non_selected_stores:
                stores.pop(store['abbr'], None)
            if stores:
                cheapest_store = min(stores, key = lambda k: stores[k]['price'])
                most_expensive_store = max(stores, key = lambda k: stores[k]['price'])
                stores['min'] = stores[cheapest_store].copy()
                stores[most_expensive_store]['class'] = "has-background-danger-dark has-text-white"
                stores[cheapest_store]['class'] = "has-background-primary-dark has-text-white"
                totals[cheapest_store] += stores[cheapest_store]['price']
            buylist[card] = stores
        totals['min'] = sum(totals.values())
    return render_template('form.html', form=listForm, cardList=buylist, stores=selected_stores, languages=LANGUAGES, totals=totals)
