import sys
from lxml import html
import requests
import json
from datetime import date
import csv
from rescrape import ListingSource, ListingSourceType, Property, PropertyType, SellerType, ZoneType, RecordProperties

def loaddoc(uri):
    r = requests.get(uri)
    doc = html.fromstring(r.text)
    return r, doc

def content(list):
    i = 0
    for item in list:
        print(f"ITEM {i}")
        print("==========")
        print(item.text_content())
        i = i + 1

def FindPropItem(self, lis, searchtext):
    for li in lis:
        if searchtext in li.text_content():
            return li
    return None

uri = 'https://utahrealestate.com/1817444'
r, doc = loaddoc(uri)
