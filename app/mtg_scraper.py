#!/usr/bin/env python3

import requests
import sys
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import json
import argparse

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
    'en': 'English'
}

CONDITIONS = {
    'nm': 'NM-Mint',
    'lp': 'Light Play',
    'mp': 'Moderate Play',
    'hp': 'Heavy Play'
}


def main(card, file, languages, conditions, output):
    wishlist = read_and_encode_wishlist(card, file)
    print(wishlist)
    cards_info = retrieve_cards_info(wishlist)
    buylist = build_buylist(cards_info, languages, conditions)
    display_buylist(buylist, output)


def read_and_encode_wishlist(card, file):
    wishlist = ""
    if card is not None:
        wishlist = [card.lower() for card in card.strip().split('\r\n')]
        wishlist = {'query': card}
    else:
        with open(file) as f:
            wishlist = [card.lower()
                        for card in f.read().strip().split('\r\n')]
            wishlist = {'query': '\r\n'.join(wishlist)}
    return urlencode(wishlist)


def retrieve_cards_info(wishlist, selected_stores):
    # TODO: parallelize queries
    cards_info = {}
    for store in selected_stores:
        store_url = "{}/products/multi_search".format(store['url'])
        results = requests.post(store_url, data=wishlist)
        soup = BeautifulSoup(results.content, 'html.parser')
        card_list = soup.find_all('div', class_='products-container')
        for card in card_list:
            card_name = card.find('h4', class_='name')
            if card_name.text not in cards_info:
                cards_info[card_name.text] = []
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
                        card_info_variant["price"] = float(
                            card_in_set_price_info[1])
                        card_info_variant["store"] = store['abbr']
                        cards_info[card_name.text].append(card_info_variant)
    return cards_info


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
