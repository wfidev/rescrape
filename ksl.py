'''
    Ksl.py
    
    Implements the class to source properties from Ksl    
'''
import sys
from rescrape import ListingSource, ListingSourceType, Property 

class Ksl(ListingSource):
    def __init__(self):
        super().__init__()
        self.Type = ListingSourceType.KSL
    
    # API contract to load a list of properties matching some criteral (filters)
    #
    def LoadPropertyList(uri, filters):
        return []
    
    # API contract to load a specific property with a given ID (specific to the listing source)
    #
    def LoadProperty(id):
        return None
    

def UnitTest_Ksl():
    ksl = Ksl()
    print(ksl)

def Main(Argv):
    return UnitTest_Ksl()

if __name__ == '__main__':
    Main(sys.argv)