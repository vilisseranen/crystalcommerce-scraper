#!/usr/bin/env python3

import requests
import sys
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import json

# List of stores close to me
STORES = [
    { "name": "L'expedition", "url": "http://www.expeditionjeux.com"},
    { "name": "Le Valet de Coeur", "url": "http://www.carte.levalet.com"},
    { "name": "Le Secret des Korrigans", "url": "http://www.lesecretdeskorrigans.com"},
    { "name": "Multizone Gatineau", "url": "https://jittedivision.crystalcommerce.com"},
    { "name": "Carta Magicka", "url": "https://www.cartamagica.com"},
    { "name": "Gamekeeper", "url": "https://www.gamekeeperverdun.com"}
]

def main(wishlist_file):
    wishlist = read_and_encode_wishlist(wishlist_file)
    cards_info = retrieve_cards_info(wishlist)
    buylist = build_buylist(cards_info)
    display_buylist(buylist)

def read_and_encode_wishlist(wishlist_file):
    wishlist = ""
    with open(sys.argv[1]) as wishlist_file:
        wishlist = [card[2:].lower() for card in wishlist_file.read().strip().split('\r\n')]
        wishlist = { 'query': '\r\n'.join(wishlist)}
        return urlencode(wishlist)

def retrieve_cards_info(wishlist):
    cards_info = {}
    for store in STORES:
        # print("Checking store {}".format(store['name']))
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
                # print("{:30.30} in set {:30.30}".format(card_name.text, card_set.text))
                card_in_set_variants = card_in_set.select('div.variant-row.row')
                for card_in_set_variant in card_in_set_variants:
                    card_info_variant = {}
                    card_in_set_quality = card_in_set_variant.find('span', class_='variant-short-info')
                    card_in_set_price = card_in_set_variant.find('span', class_='price')
                    card_in_set_quality_info = card_in_set_quality.text.split(',')
                    card_in_set_price_info = card_in_set_price.text.split(' ')
                    if card_in_set_quality_info[0] != 'Out of stock.' and card_in_set_quality_info[0] != 'All variants' and card_in_set_quality_info[0] != 'Out of Stock' and card_in_set_quality_info[0] != 'Hors stock.':
                        card_info_variant["condition"] = card_in_set_quality_info[0]
                        card_info_variant["language"] = card_in_set_quality_info[1]
                        card_info_variant["set"] = card_set.text
                        card_info_variant["price"] = float(card_in_set_price_info[1])
                        card_info_variant["store"] = store['name']
                        cards_info[card_name.text].append(card_info_variant)
                        # print("{:2.2} {:30.30} {}".format("", card_in_set_quality.text.strip(), card_in_set_price.text.strip()))
    return cards_info

def build_buylist(cards_info):
    buylist = {}
    for card in cards_info:
        buylist[card] = {}
        # TODO: filter here
        for store in STORES:
            cards_in_store = [card_in_store for card_in_store in cards_info[card] if card_in_store['store'] == store['name']]
            if len(cards_in_store) > 0:
                prices = [card_price['price'] for card_price in cards_in_store]
                min_price = min(prices)
                for card_in_store in cards_in_store:
                    if card_in_store['price'] == min_price:
                        buylist[card][store['name']] = card_in_store
    return buylist

def display_buylist(buylist):
    # print(json.dumps(buylist))
    for card in buylist:
        card_line = '"{}"'.format(card)
        for store in STORES:
            card_line += ","
            if store['name'] in buylist[card]:
                card_line += "{}".format(buylist[card][store['name']]['price'])
        print(card_line)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the file containing the list of cards as an argument.")
        quit()
    main(sys.argv[1])
