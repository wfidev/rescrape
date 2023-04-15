'''
    Ksl.py
    
    Implements the class to source properties from Ksl    
'''
import sys
from lxml import html
import requests
import json
from datetime import date
import csv
from rescrape import ListingSource, ListingSourceType, Property, PropertyType, SellerType, ZoneType

class Ksl(ListingSource):
    def __init__(self):
        super().__init__()
        self.Type = ListingSourceType.KSL
    
    # API contract to load a list of properties matching some criteral (filters)
    #
    def LoadPropertyList(uri='https://homes.ksl.com', filters = None):
        r = requests.get(uri)
        doc = html.fromstring(r.text)
        print(doc)
        # Anchors = doc.xpath('//div[@class="GridItem_GridItemInner__LOPea"]')
        Anchors = doc.xpath('//*[contains(@class, "GridItem_GridItemInner")]')

        for a in Anchors:
            print(a.href)

        return []
    
    # API contract to load a specific property with a given ID (specific to the listing source)
    #
    def LoadProperty(self, uri):
        # Load in the page data
        #
        FirefoxUA={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0'}
        r = requests.get(uri, headers=FirefoxUA)
        doc = html.fromstring(r.text)
        
        # Extract the image linke and the description from the metafields
        #
        ImageLink = ""
        Description = ""
        metafields = doc.xpath('//meta')
        for field in metafields:
            attribute = field.get('property')
            if attribute:
                if attribute == 'og:image':
                    ImageLink = field.get('content')
                elif attribute == 'og:description':
                    Description = field.get('content')

        # Extract the dataLayerTmp which is a json object in a script used to populate detail in the web page. It has the
        # rest of the fields we need.
        #
        dataLayerTmp = r.text[r.text.find('dataLayerTmp'):r.text.find('dataLayerTmp.pageDetails.ddmHitID')].strip('\n ')[15:-1]
        if dataLayerTmp and len(dataLayerTmp) > 0:
            tempdata = json.loads(dataLayerTmp)
            if tempdata and 'pageDetails' in tempdata:
                p = self.CreatePropertyFromPage(tempdata['pageDetails'])
                p.Uri = uri
                p.ImageLink = ImageLink if ImageLink else p.ImageLink
                p.Description = Description if Description else p.Description
                #p.Address = metafields.get('og:title')
                return p
        return None
        
    def CreatePropertyFromPage(self, data):
        p = Property()
        p.Zone = ZoneType.Unknown
        p.DateCreated = date.today()
        p.ListingSource = ListingSourceType.KSL

        # Read in the values from the page
        #
        p.Type = self.LookupPropertyType(data, 'Category')
        p.Seller = self.LookupSellerType(data, 'Seller Type')
        p.ID = self.AttributeLookup(data, 'AD ID', int)
        p.StreetAddress = self.AttributeLookup(data, 'Title', str)
        p.City = self.AttributeLookup(data, 'City', str)
        p.State = self.AttributeLookup(data, 'State', str)
        p.Zip = self.AttributeLookup(data, 'Zip', int)
        p.Price = self.AttributeLookup(data, 'Asking Price', float)
        p.Acres = self.AttributeLookup(data, 'Acres', float)
        p.Sqft = self.AttributeLookup(data, 'Square Feet', int)
        p.Beds = self.AttributeLookup(data, 'Bedrooms', int)
        p.Baths = self.AttributeLookup(data, 'Bathrooms', float)
        p.SellerID = self.AttributeLookup(data, 'Seller ID', int)
        p.Parking = self.AttributeLookup(data, 'Parking Type', str)
        p.Heating = self.AttributeLookup(data, 'heating', str)
        p.Cooling = self.AttributeLookup(data, 'cooling', str)
        p.YearBuilt = self.AttributeLookup(data, 'Year Built', 0)
        p.SchoolDistrict = self.AttributeLookup(data, 'School District', str)
        p.SpecialFeatures = self.AttributeLookup(data, 'Special Features', str)
        p.Basement = self.AttributeLookup(data, 'Basement Type', str)
        p.Appliances = self.AttributeLookup(data, 'Included Appliances', str)
        p.MLS = self.AttributeLookup(data, 'mls number', int)
        p.TimePosted = self.AttributeLookup(data, 'Time Posted', str)

        # Normalize the data as needed
        #
        p.StreetAddress = p.StreetAddress.split('|')[0]

        return p

    def AttributeLookup(self, data, key, Type):
        DefaultReturn = {str: "", int: 0, float: 0.0}
        return data[key] if key in data else DefaultReturn[Type]

    def LookupPropertyType(self, data, key):
        Table = {'single family home': PropertyType.SingleFamily}
        if key in data and data[key] in Table:
            return Table[data[key]]
        return PropertyType.Unknown
    
    def LookupSellerType(self, data, key):
        Table = {'by owner': SellerType.Owner}
        if key in data and data[key] in Table:
            return Table[data[key]]
        return SellerType.Unknown

    def PrintPropertyAttribute(self, data, attribute):
        if attribute in data:
            print(f'{attribute:<25}: {data[attribute]}')
    
def RecordProperties(PropertyList, Name):
    Filename = f"Reports/{Name}-{date.today()}.csv"
    with open(Filename, 'w', newline='') as f:
        writer = csv.writer(f)
        p = Property()
        writer.writerow(p.GetReportHeader())
        for p in PropertyList:
            writer.writerow(p.GetReportRow())

#<div class="GridItem_GridItemTitle__k35xf">473 13th Street, Ogden, UT 84404</div><div class="GridItem_GridItemTitle__k35xf" style="visibility: hidden; height: 0px; margin-bottom: 0px;"><span>473 13th Street, Ogden, UT 84404</span></div><div class="GridItem_GridItemPrice__Cdf3J">$449,900</div><div class="GridItem_GridItemDetail__VRLk2"><span>4 bed</span><span> | 3 bath</span><span> | 2,931 sqft</span></div>    
#<a class="GridItem_GridItemInner__LOPea" href="/listing/40514347" target="_blank"><div class="GridItem_GridItemTitle__k35xf">473 13th Street, Ogden, UT 84404</div><div class="GridItem_GridItemTitle__k35xf" style="visibility: hidden; height: 0px; margin-bottom: 0px;"><span>473 13th Street, Ogden, UT 84404</span></div><div class="GridItem_GridItemPrice__Cdf3J">$449,900</div><div class="GridItem_GridItemDetail__VRLk2"><span>4 bed</span><span> | 3 bath</span><span> | 2,931 sqft</span></div></a>

def UnitTest_Ksl():
    ksl = Ksl()
    print(ksl)

    f = open('kslproperties.db', 'r')
    Uris = f.read().splitlines()
    
    PropertyList = []
    for uri in Uris:
        if uri[0] != '#':
            p = ksl.LoadProperty(uri)
            print(p)
            PropertyList.append(p)
        print(uri)
    
    RecordProperties(PropertyList, "Ksl-Fsbo")

def Main(Argv):
    return UnitTest_Ksl()

if __name__ == '__main__':
    Main(sys.argv)