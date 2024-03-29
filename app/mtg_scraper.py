#!/usr/bin/env python3

import requests
import sys
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import json
import argparse
import locale
import re
import concurrent.futures

# List of stores close to me
STORES = [
    {"name": "L'expedition", "url": "http://www.expeditionjeux.com", "abbr": "EX"},
    {"name": "Le Valet de Coeur", "url": "http://www.carte.levalet.com", "abbr": "VC"},
    {"name": "Le Secret des Korrigans",
        "url": "http://www.lesecretdeskorrigans.com", "abbr": "SK"},
    {"name": "Multizone Gatineau",
        "url": "https://jittedivision.crystalcommerce.com", "abbr": "MZ"},
    {"name": "Carta Magicka", "url": "https://www.cartamagica.com", "abbr": "CM"},
    {"name": "Gamekeeper", "url": "https://www.gamekeeperverdun.com", "abbr": "GK"},
    {"name": "Chez Geeks", "url": "http://www.chezgeeks.com", "abbr": "CG"},
    {"name": "3 kings loot", "url": "https://www.threekingsloot.com", "abbr": "3K"},
    {"name": "Jeux 3 dragons", "url": "https://www.jeux3dragons.com", "abbr": "3D"},
    {"name": "L'abyss", "url": "https://www.labyss.com", "abbr": "AB"}
]

LANGUAGES = {
    'fr': 'French',
    'en': 'English',
    'na': 'Not specified'
}

CONDITIONS = {
    'nm': 'NM-Mint',
    'lp': 'Light Play',
    'mp': 'Moderate Play',
    'hp': 'Heavy Play'
}

CARDS_IGNORE = [
    'Plains', 'Swamp', 'Mountain', 'Island', 'Forest'
]

def main(card, file, languages, conditions, output):
    wishlist = read_and_create_wishlist(card, file)
    cards_info, cards_ignored = retrieve_cards_info(wishlist)
    buylist = build_buylist(cards_info, languages, conditions)
    display_buylist(buylist, output)


def read_and_create_wishlist(card, file):
    wishlist = []
    if card is not None:
        for card in card.strip().split('\r\n'):
            card_search = re.search('(\d+x?\s)?(.+)', card)
            card_name = card_search.group(2)
            if card_name not in CARDS_IGNORE:
                wishlist.append(card_name)
    else:
        with open(file) as f:
            wishlist = [card.lower()
                        for card in f.read().strip().split('\r\n')]
    return wishlist

def query_store(store, query):
    store_url = "{}/products/multi_search".format(store['url'])
    return {'store': store, 'content': requests.post(store_url, data=query).content}

def retrieve_cards_info(wishlist, selected_stores, include_foil):
    encoded_wishlist = urlencode({'query': '\r\n'.join(wishlist)})

    html_results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        pool = [executor.submit(query_store, store, encoded_wishlist) for store in selected_stores]
        for i in concurrent.futures.as_completed(pool):
            html_results.append(i.result())
    cards_info = {}
    cards_ignored = []
    for html in html_results:
        soup = BeautifulSoup(html['content'], 'html.parser')
        card_list = soup.find_all('div', class_='products-container')
        for card in card_list:
            card_name = card.find('h4', class_='name')
            card_search = re.search("([a-z'\-,]+((,)?\s[a-z][a-z'\-]*[a-z]*)*(( \/\/ )([a-z'\-,]+((,)?\s[a-z][a-z'\-]*[a-z]*)*))?)", card_name.text, flags=re.IGNORECASE)
            if card_search != None:
                card_basename = card_search.group(1)
                print("Found card {:<80.80} is {}".format(card_name.text, card_basename))
            else:
                card_basename = card_name.text
                print("Not matching a card name: {}".format(card_basename))
            if card_basename.lower() not in [card.lower() for card in wishlist]:
                print("{} is not in the wish list".format(card_name.text))
                cards_ignored.append(card_name.text)
                continue
            if not include_foil:
                card_search = re.search('- Foil', card_name.text)
                if card_search != None:
                    print("Ignoring card {} because it is foiled.".format(card_name.text))
                    continue
            if card_basename not in cards_info:
                cards_info[card_basename] = []
            card_in_sets = card.find_all('div', class_='inner')
            for card_in_set in card_in_sets:
                card_set = card_in_set.find('span', class_='category')
                card_in_set_variants = card_in_set.select(
                    'div.variant-row.row')
                for card_in_set_variant in card_in_set_variants:
                    card_info_variant = {}
                    card_in_set_quality = card_in_set_variant.find(
                        'span', class_='variant-short-info')
                    if not card_in_set_quality:
                        # For some stores, means item is not in store
                        continue
                    card_in_set_price = card_in_set_variant.find(
                        'span', class_='price')
                    card_in_set_quality_info = card_in_set_quality.text.split(
                        ',')
                    card_in_set_price_info = card_in_set_price.text.split(' ')
                    if card_in_set_quality_info[0] != 'Out of stock.' and card_in_set_quality_info[0] != 'All variants' and card_in_set_quality_info[0] != 'Out of Stock' and card_in_set_quality_info[0] != 'Hors stock.':
                        card_info_variant["condition"] = card_in_set_quality_info[0].strip(
                        )
                        if len(card_in_set_quality_info) > 1:
                            card_info_variant["language"] = card_in_set_quality_info[1].strip(
                            )
                        else:
                            card_info_variant["language"] = LANGUAGES['na']
                        if card_set:
                            card_info_variant["set"] = card_set.text.strip()
                        else:
                            card_info_variant["set"] = "Unknown"
                        # We should be able to load the locale in the docker container to translate
                        # prices > 1000 (with comma), but I have trouble loading the locale in alpine
                        card_info_variant["price"] = locale.atof(card_in_set_price_info[1].replace(',', ''))
                        card_info_variant["store"] = html['store']['abbr']
                        card_info_variant["variant_name"] = card_name.text
                        cards_info[card_basename].append(card_info_variant)
    return cards_info, list(set(cards_ignored))


def build_buylist(cards_info, languages, conditions):
    buylist = {}
    if languages is not None:
        languages_filter = [LANGUAGES[language] for language in languages]
    if conditions is not None:
        conditions_filter = [CONDITIONS[condition] for condition in conditions]
    for card in cards_info:
        buylist[card] = {}
        for store in STORES:
            cards_in_store = [card_in_store for card_in_store in cards_info[card]
                              if card_in_store['store'] == store['abbr']]
            if len(cards_in_store) > 0:
                prices = [card_price['price'] for card_price in cards_in_store]
                min_price = min(prices)
                if languages is not None:
                    cards_in_store = [
                        card for card in cards_in_store if card['language'] in languages_filter]
                if conditions is not None:
                    cards_in_store = [
                        card for card in cards_in_store if card['condition'] in conditions_filter]
                for card_in_store in cards_in_store:
                    if card_in_store['price'] == min_price:
                        buylist[card][store['abbr']] = card_in_store
    return buylist


def display_buylist(buylist, output):
    if output == 'json':
        print(json.dumps(buylist))
    else:
        for card in buylist:
            card_line = '"{}"'.format(card)
            for store in STORES:
                card_line += ","
                if store['abbr'] in buylist[card]:
                    card_line += "{}".format(buylist[card]
                                             [store['abbr']]['price'])
            print(card_line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check the prices of magic cards from stores in Montreal.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str,
                       help='File containing the list of cards.')
    group.add_argument('-c', '--card', type=str,
                       help='Specific card to check.')
    parser.add_argument('-l', '--languages', type=str, choices=['fr', 'en'], nargs='*',
                        help='Keep only cards with these specific languages.')
    parser.add_argument('-n', '--conditions', type=str, choices=['nm', 'lp', 'mp', 'hp'], nargs='*',
                        help='Keep only cards with these specific conditions.')
    parser.add_argument('-o', '--output', type=str,
                        choices=['json', 'csv'], default='json')
    args = parser.parse_args()
    main(args.card, args.file, args.languages, args.conditions, args.output)
