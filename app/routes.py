from app import app
from app.list import InputForm

from flask import render_template, flash, redirect
from re import sub

from app.mtg_scraper import read_and_create_wishlist, retrieve_cards_info, build_buylist
from app.mtg_scraper import STORES, LANGUAGES, CONDITIONS, CARDS_IGNORE


@app.route('/', methods=['GET', 'POST'])
def index():
    selected_stores = STORES
    listForm = InputForm()
    cardsInfo = None
    buylist = None
    totals = None
    missing_cards = []
    cardsIgnored = []
    if listForm.validate_on_submit():
        query = read_and_create_wishlist(
            card=listForm.list.data, file=None)
        if listForm.stores.data:
            selected_stores = [store for store in STORES if store['abbr'] in listForm.stores.data]
        selected_stores = [store for store in selected_stores if store['name'] != 'Min']
        cardsInfo, cardsIgnored = retrieve_cards_info(query, selected_stores)
        missing_cards = [sub('^(\d+x?)?(.*)', '\\2', line).strip() for line in listForm.list.data.split("\n")]
    if cardsInfo:
        languages_filter = listForm.languages.data if listForm.languages.data else None
        conditions_filter = listForm.conditions.data if listForm.conditions.data else None
        buylist = build_buylist(cardsInfo, languages_filter, conditions_filter) # We should filter by store here or before
        totals = {store['abbr']: 0 for store in selected_stores}
        for card, stores in buylist.items():
            if stores:
                cheapest_store = min(stores, key = lambda k: stores[k]['price'])
                most_expensive_store = max(stores, key = lambda k: stores[k]['price'])
                stores['min'] = stores[cheapest_store].copy()
                stores[most_expensive_store]['class'] = "has-background-danger-dark has-text-white"
                stores[cheapest_store]['class'] = "has-background-primary-dark has-text-white"
                totals[cheapest_store] += stores[cheapest_store]['price']
            buylist[card] = stores
        totals['min'] = sum(totals.values())
        buylistKeysLowerCase = [k.lower() for k, v in buylist.items()]
        missing_cards = [item for item in missing_cards if item.lower() not in buylistKeysLowerCase]
        
    return render_template('form.html',
        form=listForm,
        cardList=buylist,
        stores=selected_stores,
        languages=LANGUAGES,
        totals=totals,
        missing_cards=", ".join(missing_cards),
        ignored_cards=', '.join(CARDS_IGNORE + cardsIgnored) # We ignore some cards by default (basic lands) + others returned by the website
    )
