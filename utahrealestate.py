'''
    UtahRealestate.py
    
    Implements the class to source properties from UtahRealestate    
'''
import sys
from lxml import html
import requests
import json
from datetime import date, timedelta
import csv
from rescrape import ListingSource, ListingSourceType, Property, PropertyType, SellerType, ZoneType, RecordProperties

def CleanSF(x):
    return " ".join(x.text_content().replace("\n", "").replace("\t", "").split())

def FindPropItem(lis, searchtext):
    for li in lis:
        if searchtext in li.text_content():
            return li
    return None

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
        p.DateScraped = date.today()
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
        li = FindPropItem(lis, 'MLS#')
        p.MLS = int(li.text_content().split('\n')[5].strip())
        p.ID = p.MLS

        li = FindPropItem(lis, 'Year Built')
        p.YearBuilt = int(li.text_content().split('\n')[5].strip())

        li = FindPropItem(lis, 'Acres:')
        p.Acres = float(li.text.split(' ')[1])

        # Type and SellerID
        #
        p.Type = self.LookupPropertyType(doc)
        ao = doc.xpath('//div[@class="agent___overview___info"]')
        agent = ao[0].xpath('//strong')
        p.SellerID = agent[0].text_content()

        # Description
        #
        fw = doc.xpath('//div[@class="features-wrap"]')[0]
        p.Description = fw[0].text_content()

        # Zoning
        #
        li = FindPropItem(fw, 'Zoning:')
        p.Zone = li.text_content().strip()

        # Parking
        #
        lis = fw[5]
        li = FindPropItem(lis, "Garage Capacity:")
        p.Parking = li.text_content().strip() if li is not None else p.Parking

        # Interior features
        #
        lis = fw[3]
        li = FindPropItem(lis, "Air Conditioning:")
        p.Cooling = li.text_content().strip() if li is not None else p.Cooling
        li = FindPropItem(lis, "Heating:")
        p.Heating = li.text_content().strip() if li is not None else p.Heating
        li = FindPropItem(lis, "Basement:")
        p.Basement = li.text_content().strip() if li is not None else p.Basement
        p.Appliances = "|".join([x.text_content() for x in fw[7]])
        sfs = [CleanSF(x) for x in fw[3]] + [CleanSF(x) for x in fw[5]]
        p.SpecialFeatures = "|".join(sfs)
        
        # Time posted
        #
        x = doc.xpath('//div[@class="facts___item"]')
        DaysOnURE = x[0].text_content().split('\n')[4].strip()
        p.DatePosted = DaysOnURE
        if DaysOnURE.isdigit():
            posteddate = date.today() - timedelta(days=int(DaysOnURE))
            p.DatePosted = posteddate.strftime("%m-%d-%y")

        # Image Links
        #
        imgs = doc.xpath('//img[@class="image___gallery__photo___img"]')
        p.ImageLink = imgs[0].get('src')
        p.ImageGallery = " | ".join([x.get('src') for x in imgs])

        # Other
        #
        li = FindPropItem(fw[24], "School District")
        p.SchoolDistrict = li.text_content().split('\n')[2].strip() if li is not None else p.SchoolDistrict
        
        return p
    
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
    ReportName = "UtahRealestate"
    if len(Argv) > 1:
        ReportName = Argv[1]
    return UnitTest_Utahrealestate(ReportName)

if __name__ == '__main__':
    Main(sys.argv)