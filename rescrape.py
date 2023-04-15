'''
 Rescrape.py

 Base classes to represent properties across differents services and sites that provide information about them.

'''
from aenum import Enum
from datetime import date
import sys

class PropertyType(Enum):
    _init_ = 'value string'
    def __str__(self):
        return self.string

    Unknown = 0, "Unknown"
    Land = 1, "Land"
    SingleFamily = 2, "Single Family"
    MultiUnit = 3, "Multi Unit"
    Commercial = 4, "Commercial"


#    @classmethod
#    def _missing_value_(cls, value):
#        for member in cls:
#            if member.string == value:
#                return member

class ZoneType(Enum):
    _init_ = 'value string'
    def __str__(self):
        return self.string

    Unknown = 0, 'Unknown'
    SingleFamily = 1, 'Single Family'
    Duplex = 2, "Duplex"
    LowDensity = 3, "Low Density"     # Up to 10 units allowed
    HighDensity = 4, "High Density"         # More than 10
    Recreational = 5, "Recreational"
    Nonbuildable = 6, "Non-buildable"
    Commerical = 7, "Commercial"
    MixedUse = 8, "Mixed Use"
    def __str__(self):
        return self.string

class SellerType(Enum):
    _init_ = 'value string'
    def __str__(self):
        return self.string

    Unknown = 0, "Unknown"
    Owner = 1, "Owner"
    Agent = 2, "Agent"

class ListingSourceType(Enum):
    _init_ = 'value string'
    def __str__(self):
        return self.string

    Unknown = 0,"Unknown"
    UtahRealestate = 1, "UtahRealEstate"
    KSL = 2, "KSL Homes"
    Zillow = 3, "Zillow"
       
class Property:
    def __init__(self):
        self.Type = PropertyType.Unknown
        self.Zone = ZoneType.Unknown
        self.Seller = SellerType.Unknown
        self.ListingSource = ListingSourceType.Unknown
        self.DateCreated = date.today()
        self.ID = None                          # Specific to the listing source
        self.StreetAddress = ""
        self.City = ""
        self.State = ""
        self.Zip = 0
        self.Price = 0.0
        self.Acres = 0.0
        self.Sqft = 0
        self.Beds = 0
        self.Baths = 0.0

    def __repr__(self):
        ty = f'{str(self.Type)[:8]:<9}'
        zn = f'{str(self.Zone)[:8]:<9}'
        se = f'{self.Seller:<6}'
        dc = f'{self.DateCreated.strftime("%m-%d-%y"):<9}'
        sa = f'{self.StreetAddress[:19]:<20}'
        id = f'{str(self.ID)[:4]:<5}'
        ls = f'{str(self.ListingSource):<8}'
        return f"{dc}{ls}{id}{sa}{zn}{se}"

class ListingSource:
    def __init__(self):
        self.Type = ListingSourceType.Unknown
    
    def __repr__(self):
        return f"{self.Type}"
    
    # API contract to load a list of properties matching some criteral (filters)
    #
    def LoadPropertyList(uri, filters):
        return []
    
    # API contract to load a specific property with a given ID (specific to the listing source)
    #
    def LoadProperty(id):
        return None
        
def UnitTest_Property():
    p = Property()  
    p.Type = PropertyType.SingleFamily
    p.Zone = ZoneType.SingleFamily
    p.Seller = SellerType.Owner
    p.StreetAddress = "1334 Gillman Blvd"
    p.City = "Salt Lake City"
    p.State = "Utah"
    p.Zip = 84102
    print(p)

def Main(Argv):
    return UnitTest_Property()

if __name__ == '__main__':
    Main(sys.argv)
