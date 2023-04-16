'''
    UtahRealestate.py
    
    Implements the class to source properties from UtahRealestate    
'''
import sys
from lxml import html
import requests
import json
from datetime import date
import csv
from rescrape import ListingSource, ListingSourceType, Property, PropertyType, SellerType, ZoneType, RecordProperties

class UtahRealestate(ListingSource):
    def __init__(self):
        super().__init__()
        self.Type = ListingSourceType.UtahRealestate
    
    # API contract to load a list of properties matching some criteral (filters)
    #
    def LoadPropertyList(uri='https://homes.Utahrealestate.com', filters = None):
        return []
    
    # API contract to load a specific property with a given ID (specific to the listing source)
    #
    def LoadProperty(self, uri):
        # Load in the page data
        #
        FirefoxUA={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0'}
        r = requests.get(uri, headers=FirefoxUA)
        doc = html.fromstring(r.text)
        p = self.CreatePropertyFromPage(doc)
        if p:
            p.Uri = uri

        return p
        
    def CreatePropertyFromPage(self, doc):
        p = Property()
        p.Zone = ZoneType.Unknown       # TODO fill this in from the numeric value
        p.DateCreated = date.today()
        p.ListingSource = ListingSourceType.UtahRealestate
        p.Seller = SellerType.Agent

        # Address
        #
        data = doc.xpath("//div[@class='prop___overview']")[0]
        address = data.text_content().split('\n')
        csz = address[2].split(',')
        sz = csz[1].strip().split(' ')
        p.StreetAddress = address[1].strip()
        p.City = csz[0].strip()
        p.Zip = sz[1]
        p.State = sz[0]

        # Extract items from the propert details overview
        #
        pdo = doc.xpath("//ul[@class='prop-details-overview']")
        lis = pdo[0].xpath("//li")
        p.Price = lis[9].text_content().split('\n')[1].strip()
        p.Beds = lis[10].text_content().split('\n')[1].strip().split(' ')[0]
        p.Baths = lis[11].text_content().split('\n')[1].strip().split(' ')[0]
        p.Sqft = lis[12].text_content().split('\n')[1].strip().split(' ')[0]

        # The following items are at unpredictable indices
        #
        li = self.FindPropItem(lis, 'MLS#')
        p.MLS = int(li.text_content().split('\n')[5].strip())
        p.ID = p.MLS

        li = self.FindPropItem(lis, 'Year Built')
        p.YearBuilt = int(li.text_content().split('\n')[5].strip())

        li = self.FindPropItem(lis, 'Acres:')
        p.Acres = float(li.text.split(' ')[1])

        # The request require some custom logic
        #
        p.Type = self.LookupPropertyType(doc)
        ao = doc.xpath('//div[@class="agent___overview___info"]')
        agent = ao[0].xpath('//strong')
        p.SellerID = agent[0].text_content()

        # TODO - Fill in these values
        # p.Parking = lis[42].text + ' ' + list[43].text
        # p.Cooling = lis[34].text
        # p.Heating = lis[35].text
        # p.Appliances = lis[28].text
        # p.Basement = "" # TODO - fill this in, it's in the notes
        # p.SchoolDistrict = self.AttributeLookup(data, 'School District', str)
        # p.SpecialFeatures = self.AttributeLookup(data, 'Special Features', str)
        # p.TimePosted = self.AttributeLookup(data, 'Time Posted', str)

        return p
    
    def FindPropItem(self, lis, searchtext):
        for li in lis:
            if searchtext in li.text_content():
                return li
        return None

    def LookupPropertyType(self, doc):
        x = doc.xpath('//div[@class="facts___item"]')
        Type = x[3].text_content().split('\n')[4].strip()
        LookupTable = {'Single Family': PropertyType.SingleFamily}
        if Type in LookupTable:
            return LookupTable[Type]
        return PropertyType.Unknown

def UnitTest_Utahrealestate(ReportName):
    ur = UtahRealestate()
    print(ur)
    f = open('properties.db', 'r')
    Uris = f.read().splitlines()
    
    PropertyList = []
    for uri in Uris:
        if uri[0] != '#' and "utahrealestate.com" in uri:
            p = ur.LoadProperty(uri)
            print(p)
            if (p):
                PropertyList.append(p)
    
    RecordProperties(PropertyList, ReportName)

def Main(Argv):
    ReportName = "Utahrealestate-Fsbo"
    if len(Argv) > 1:
        ReportName = Argv[1]
    return UnitTest_Utahrealestate(ReportName)

if __name__ == '__main__':
    Main(sys.argv)