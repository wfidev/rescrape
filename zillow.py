'''
    Zillow.py
    
    Implements the class to source properties from Zillow    
'''
import sys
from rescrape import ListingSource, ListingSourceType, Property 

class Zillow(ListingSource):
    def __init__(self):
        super().__init__()
        self.Type = ListingSourceType.Zillow
    
    # API contract to load a list of properties matching some criteral (filters)
    #
    def LoadPropertyList(uri, filters):
        return []
    
    # API contract to load a specific property with a given ID (specific to the listing source)
    #
    def LoadProperty(id):
        return None
    

def UnitTest_Zillow():
    Z = Zillow()
    print(Z)

def Main(Argv):
    return UnitTest_Zillow()

if __name__ == '__main__':
    Main(sys.argv)