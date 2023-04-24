'''
    Zillow.py
    
    Implements the class to source properties from Zillow    
'''
import sys
from lxml import html
import requests
import json
from datetime import date, timedelta
import time
import csv
from rescrape import ListingSource, ListingSourceType, Property, PropertyType, SellerType, ZoneType, RecordProperties


class Zillow(ListingSource):
    def __init__(self):
        super().__init__()
        self.Type = ListingSourceType.Zillow
    
    # API contract to load a list of properties matching some criteral (filters)
    #
    def LoadPropertyList(self, uri, filters):
        return []
    
    # API contract to load a specific property with a given ID (specific to the listing source)
    #
    def LoadProperty(self, uri):
        # Load in the page data
        #
        print("Loading: " + uri)

        #FirefoxUA={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0'}
        headers = {
                "accept-language": "en-US,en;q=0.9",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "accept-language": "en-US;en;q=0.9",
                "accept-encoding": "gzip, deflate, br",
        }       
        
        r = requests.get(uri, headers=headers)
        #print(r.text)
        doc = html.fromstring(r.text)
        p = self.CreatePropertyFromPage(doc, uri, r.text)
        return p
    
    def LoadPropertyTest(self, uri):
        doc = None
        with open('zill_zenith.txt', 'r') as f:
            text = f.read()
            doc = html.fromstring(text)
            if doc is None:
                print('Unable to read file')
                return None

        p = self.CreatePropertyFromPage(doc)
        if p:
            p.Uri = uri
        return p
        
    def CreatePropertyFromPage(self, doc, uri, text):
        p = Property()
        p.DateScraped = date.today()
        p.ListingSource = ListingSourceType.Zillow
        p.Uri = uri

        # The property details are all conveniently loaded into a json object in the __NEXT_DATA__
        # script. 
        #
        nextdata = doc.xpath("//script[@id='__NEXT_DATA__']")
        if len(nextdata) == 0:
            print(f"No NEXT_DATA in the following, will check hdpApolloPreloadedData : {uri}")
            with open("broken.html", "w") as f:
                f.write(text)
            return None
        
        # TODO -  apollodata = doc.xpath("//script[@id='hdpApolloPreloadedData']")
        #   The alternative way the data is delivered
        #

        datadict = json.loads(nextdata[0].text)
        gdp = json.loads(datadict["props"]["pageProps"]["gdpClientCache"])
        key = list(gdp.keys())[0]
        propdata = gdp[key]['property']
        resoFacts = propdata['resoFacts']

        p.ID = propdata['zpid']
        p.Price = propdata["price"]
        p.Sqft = int(propdata["livingArea"])
        p.Beds = propdata["bedrooms"]
        p.Baths = propdata["bathrooms"]
        p.Acres = round(float(propdata["lotSize"]) / 43560.0, 2)
        p.StreetAddress = propdata['streetAddress'] 
        p.City =  propdata['city']
        p.State = propdata['state']
        p.Zip = propdata['zipcode']
        p.YearBuilt = propdata["yearBuilt"] 
        p.Zone = ZoneType.Unknown
        p.Type = self.ExtractPropertyType(propdata)
        p.Seller = propdata['listedBy'][0]['elements'][0]['text']
        p.DatePosted = self.ExtractDatePosted(propdata)
        p.Basement = resoFacts['basement']
        p.ImageLink = propdata["mediumImageLink"]
        p.Description = propdata['description']
        p.SellerID = propdata['listedBy'][0]['elements'][1]['text']
        p.Parking = resoFacts['parkingCapacity']
        p.Heating = resoFacts['heating']
        p.Cooling = resoFacts['cooling']
        p.SchoolDistrict = propdata['schools'][0]['name']
        p.SpecialFeatures = self.ExtractSpecialFeatures(resoFacts)
        p.Appliances = resoFacts['appliances']
        p.ImageGallery = " | ".join([p['mixedSources']['jpeg'][0]['url'] for p in propdata['photos']])
        p.MLS = self.ExtractMLS(propdata)
        p.Zestimate = float(propdata["zestimate"])
        p.RentEstimate = float(propdata["rentZestimate"])
        p.parcelID = propdata["parcelId"]
        p.HoaFee = float(propdata["monthlyHoaFee"]) if propdata["monthlyHoaFee"] is not None else 0.0
        
        return p
    
    def ExtractSpecialFeatures(self, resoFacts):
        Int = [] if 'interiorFeatures' in resoFacts else resoFacts['interiorFeatures']
        Ext = [] if 'exteriorFeatures' in resoFacts else resoFacts['exteriorFeatures']
        return ' | '.join(Int + Ext)

    def ExtractPropertyType(self, propdata):
        dim = propdata["propertyTypeDimension"]
        if dim == "Single Family":
            return PropertyType.SingleFamily
        return PropertyType.Unknown

    def ExtractSeller(seld, propdata):
        propdata["listedBy"]

    def ExtractDatePosted(self, propdata):
        posteddate = date.today() - timedelta(days=int(propdata["daysOnZillow"]))
        return posteddate.strftime("%m-%d-%y")

    def ExtractMLS(self, propdata):
        if 'pals' in propdata:
            pals = propdata['pals']
            for pal in pals:
                if 'palsId' in pal and 'name' in pal:
                    if pal['name'] == 'UtahRealEstate.com':
                        palsId = pal['palsId']
                        return int(palsId.split('_')[1])
        return 0

    def ExtratImagelist(self, propdata):
        photolist = propdata['photos'] 
        photos = []
        for photo in photolist:
            photos.append(photo['mixedSources']['jpeg'][0]['url'])
        return " | ".join(photos)
  
def UnitTest_Zillow(ReportName):
    Z = Zillow()
    print(Z)
    f = open('properties.db', 'r')
    Uris = f.read().splitlines()
    
    PropertyList = []
    for uri in Uris:
        if uri[0] != '#' and "zillow.com" in uri:
            p = Z.LoadProperty(uri)
            print(p)
            if (p):
                PropertyList.append(p)
            print('Sleeping for 2 seconds...')
            time.sleep(2)
    
    RecordProperties(PropertyList, ReportName)

def Main(Argv):
    ReportName = "Zillow"
    if len(Argv) > 1:
        ReportName = Argv[1]
    return UnitTest_Zillow(ReportName)

if __name__ == '__main__':
    Main(sys.argv)

'''
Base headers example from the example (on the website, not in the py)

BASE_HEADERS = {
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
}

'''


'''
FOR SALE PROPERTY
propdata["listingDataSource"] = Phoenix
propdata["zpid"] = 12786046
propdata["city"] = Salt Lake City
propdata["state"] = UT
propdata["homeStatus"] = FOR_SALE
propdata["address"] = {'streetAddress': '2941 S Zenith Cir', 'city': 'Salt Lake City', 'state': 'UT', 'zipcode': '84106', 'neighborhood': None, 'commu
propdata["isListingClaimedByCurrentSignedInUser"] = False
propdata["isCurrentSignedInAgentResponsible"] = False
propdata["bedrooms"] = 4
propdata["bathrooms"] = 3
propdata["price"] = 740000
propdata["yearBuilt"] = 1961
propdata["streetAddress"] = 2941 S Zenith Cir
propdata["zipcode"] = 84106
propdata["isCurrentSignedInUserVerifiedOwner"] = False
propdata["regionString"] = Salt Lake City UT 84106
propdata["propertyUpdatePageLink"] = None
propdata["moveHomeMapLocationLink"] = None
propdata["propertyEventLogLink"] = None
propdata["editPropertyHistorylink"] = None
propdata["isRentalListingOffMarket"] = False
propdata["hdpUrl"] = /homedetails/2941-S-Zenith-Cir-Salt-Lake-City-UT-84106/12786046_zpid/
propdata["listing_sub_type"] = {'is_newHome': False, 'is_FSBO': False, 'is_FSBA': True, 'is_foreclosure': False, 'is_bankOwned': False, 'is_forAuction
propdata["nearbyCities"] = [{'regionUrl': {'path': '/draper-ut/'}, 'name': 'Draper', 'body': None}, {'regionUrl': {'path': '/herriman-ut/'}, 'name': '
propdata["nearbyNeighborhoods"] = [{'regionUrl': {'path': '/capitol-hill-salt-lake-city-ut/'}, 'name': 'Capitol Hill', 'body': None}, {'regionUrl': {'
propdata["country"] = USA
propdata["nearbyZipcodes"] = [{'regionUrl': {'path': '/salt-lake-city-ut-84101/'}, 'name': '84101', 'body': None}, {'regionUrl': {'path': '/salt-lake-
propdata["cityId"] = 6909
propdata["citySearchUrl"] = {'text': 'Homes in Salt Lake City', 'path': '/salt-lake-city-ut/'}
propdata["zipcodeSearchUrl"] = {'path': '/salt-lake-city-ut-84106/'}
propdata["apartmentsForRentInZipcodeSearchUrl"] = {'path': '/salt-lake-city-ut-84106/apartments/'}
propdata["housesForRentInZipcodeSearchUrl"] = {'path': '/salt-lake-city-ut-84106/rent-houses/'}
propdata["abbreviatedAddress"] = 2941 S Zenith Cir
propdata["neighborhoodRegion"] = {'name': 'Sugar House'}
propdata["building"] = None
propdata["isUndisclosedAddress"] = False
propdata["boroughId"] = None
propdata["providerListingID"] = None
propdata["neighborhoodSearchUrl"] = {'path': '/sugar-house-salt-lake-city-ut/'}
propdata["stateSearchUrl"] = {'path': '/ut/'}
propdata["countySearchUrl"] = {'text': 'Homes in Salt Lake County', 'path': '/salt-lake-county-ut/'}
propdata["boroughSearchUrl"] = None
propdata["communityUrl"] = None
propdata["isPremierBuilder"] = False
propdata["homeType"] = SINGLE_FAMILY
propdata["adTargets"] = {'aamgnrc1': '2941 S Zenith Cir', 'bd': '4', 'fsbid': '508', 'city': 'Salt_Lake_City', 'proptp': 'sfh', 'pid': '12786046', 'lo
propdata["currency"] = USD
propdata["resoFacts"] = {'accessibilityFeatures': None, 'additionalFeeInfo': None, 'associations': [], 'associationFee': None, 'associationAmenities':
propdata["attributionInfo"] = {'listingAgreement': None, 'mlsName': 'PCBR', 'agentEmail': 'cathy.richards@evrealestate.com', 'agentLicenseNumber': Non
propdata["listPriceLow"] = None
propdata["homeRecommendations"] = {'blendedRecs': [], 'displayShort': ''}
propdata["livingArea"] = 2690
propdata["livingAreaValue"] = 2690
propdata["zestimate"] = 740003
propdata["newConstructionType"] = None
propdata["zestimateLowPercent"] = 5
propdata["zestimateHighPercent"] = 5
propdata["rentZestimate"] = 3329
propdata["restimateLowPercent"] = 15
propdata["restimateHighPercent"] = 15
propdata["schools"] = [{'distance': 0.4, 'name': 'Nibley Park School', 'rating': 4, 'level': 'Primary', 'studentsPerTeacher': 18, 'assigned': None, 'g
propdata["homeValues"] = None
propdata["parentRegion"] = {'name': 'Sugar House'}
propdata["nearbyHomes"] = [{'zpid': 12786047, 'miniCardPhotos': [{'url': 'https://maps.googleapis.com/maps/api/streetview?location=2945+S+Zenith+Cir%2
propdata["countyFIPS"] = 49035
propdata["parcelId"] = 16292040100000
propdata["taxHistory"] = [{'time': 1650757356323, 'taxPaid': 2962.58, 'taxIncreaseRate': 0.1158073, 'value': 281160, 'valueIncreaseRate': 0.23240116},
propdata["priceHistory"] = None
propdata["comps"] = [{'zpid': 12783621, 'miniCardPhotos': [{'url': 'https://photos.zillowstatic.com/fp/7fa9db7cac74af9cf716a70083aa3319-p_c.jpg'}], 'p
propdata["description"] = Don't miss your chance to see this incredible home in one of Salt Lake City's most desirable neighborhoods.  Nestled in a qu
propdata["whatILove"] = None
propdata["contingentListingType"] = None
propdata["timeOnZillow"] = 18 days
propdata["pageViewCount"] = 1627
propdata["favoriteCount"] = 55
propdata["daysOnZillow"] = 18
propdata["latitude"] = 40.708138
propdata["longitude"] = -111.86154
propdata["openHouseSchedule"] = []
propdata["desktopWebHdpImageLink"] = https://photos.zillowstatic.com/fp/65b1eb58880e9c69de5bea9a6cbe8c61-p_h.jpg
propdata["brokerageName"] = Engel & Voelkers Park City
propdata["timeZone"] = America/Denver
propdata["listingMetadata"] = {'mustAttributeOfficeNameBeforeAgentName': False, 'mustDisplayAttributionListAgentEmail': False, 'mustDisplayAttribution
propdata["pals"] = [{'name': 'UtahRealEstate.com', 'palsId': '319001_1869688'}, {'name': 'Engel & Volkers', 'palsId': '7c6904c0617c92a82c87c32bbd34eca
propdata["listedBy"] = [{'id': 'LISTING_AGENT', 'elements': [{'id': 'NAME', 'text': 'Catherine Richards', 'action': None}, {'id': 'PHONE', 'text': '43
propdata["homeInsights"] = [{'insights': [{'modelId': 'v2-2', 'treatmentId': 'model_0', 'phrases': ['Gas fireplace', 'Open floor plan', 'Quiet cul de 
propdata["sellingSoon"] = [{'treatmentId': 'model_0', 'percentile': 0.77}]
propdata["listingProvider"] = None
propdata["isIncomeRestricted"] = None
propdata["brokerId"] = None
propdata["ssid"] = 508
propdata["monthlyHoaFee"] = None
propdata["mortgageZHLRates"] = {'fifteenYearFixedBucket': {'rate': 6.12, 'rateSource': 'ZGMI', 'lastUpdated': 1682291409006}, 'thirtyYearFixedBucket':
propdata["propertyTaxRate"] = 0.56
propdata["hiResImageLink"] = https://photos.zillowstatic.com/fp/65b1eb58880e9c69de5bea9a6cbe8c61-p_f.jpg
propdata["hdpTypeDimension"] = ForSale
propdata["mlsid"] = 12300976
propdata["ouid"] = M00000627
propdata["propertyTypeDimension"] = Single Family
propdata["mediumImageLink"] = https://photos.zillowstatic.com/fp/65b1eb58880e9c69de5bea9a6cbe8c61-p_d.jpg
propdata["isZillowOwned"] = False
propdata["enhancedBrokerImageUrl"] = https://photos.zillowstatic.com/fp/353f9650d9c604248c2f43c75968453d-zillow_web_95_35.jpg
propdata["listingAccountUserId"] = X1-ZU10c6c3jng0efd_1ekgp
propdata["tourEligibility"] = {'isPropertyTourEligible': True, 'propertyTourOptions': {'isFinal': True, 'tourAvailability': [{'date': '2023-04-24', 's
propdata["contactFormRenderData"] = {'data': {'agent_module': {'agent_reason': 3, 'badge_type': 'Listing Agent', 'business_name': 'Engel & Voelkers Pa
propdata["responsivePhotos"] = [{'mixedSources': {'jpeg': [{'url': 'https://photos.zillowstatic.com/fp/65b1eb58880e9c69de5bea9a6cbe8c61-cc_ft_192.jpg'
propdata["buildingId"] = None
propdata["virtualTourUrl"] = http://www.2941zenithcir.com/unbranded
propdata["hasApprovedThirdPartyVirtualTourUrl"] = True
propdata["photoCount"] = 46
propdata["livingAreaUnits"] = Square Feet
propdata["lotSize"] = 7405
propdata["lotAreaValue"] = 7405.2
propdata["lotAreaUnits"] = Square Feet
propdata["postingProductType"] = Standard
propdata["marketingName"] = None
propdata["ZoDsFsUpsellTop"] = {'display': False, 'displayCategory': 'none', 'displayAttributes': {'leadType': 'PARTNER_LEADS_INTEREST_LIST'}, 'treatme
propdata["onsiteMessage"] = {'eventId': 'c74c105d-eb3a-4ac0-98c1-2339dbb997d8', 'decisionContext': {}, 'messages': [{'skipDisplayReason': None, 'shoul
propdata["stateId"] = 55
propdata["zipPlusFour"] = 2132
propdata["numberOfUnitsTotal"] = None
propdata["foreclosureDefaultFilingDate"] = None
propdata["foreclosureAuctionFilingDate"] = None
propdata["foreclosureLoanDate"] = None
propdata["foreclosureLoanOriginator"] = None
propdata["foreclosureLoanAmount"] = None
propdata["foreclosurePriorSaleDate"] = None
propdata["foreclosurePriorSaleAmount"] = None
propdata["foreclosureBalanceReportingDate"] = None
propdata["foreclosurePastDueBalance"] = None
propdata["foreclosureUnpaidBalance"] = None
propdata["foreclosureAuctionTime"] = None
propdata["foreclosureAuctionDescription"] = None
propdata["foreclosureAuctionCity"] = None
propdata["foreclosureAuctionLocation"] = None
propdata["foreclosureDate"] = None
propdata["foreclosureAmount"] = None
propdata["foreclosingBank"] = None
propdata["foreclosureJudicialType"] = Non-Judicial
propdata["datePostedString"] = 2023-04-05
propdata["foreclosureTypes"] = {'isBankOwned': False, 'isForeclosedNFS': False, 'isPreforeclosure': False, 'isAnyForeclosure': False, 'wasNonRetailAuc
propdata["foreclosureMoreInfo"] = None
propdata["hasBadGeocode"] = False
propdata["streetViewMetadataUrlMediaWallLatLong"] = https://maps.googleapis.com/maps/api/streetview/metadata?location=40.708138,-111.86154&key=AIzaSyA
propdata["streetViewMetadataUrlMediaWallAddress"] = https://maps.googleapis.com/maps/api/streetview/metadata?location=2941%20S%20Zenith%20Cir%2C%20Sal
propdata["streetViewTileImageUrlMediumLatLong"] = https://maps.googleapis.com/maps/api/streetview?location=40.708138,-111.86154&size=400x250&key=AIzaS
propdata["streetViewTileImageUrlMediumAddress"] = https://maps.googleapis.com/maps/api/streetview?location=2941%20S%20Zenith%20Cir%2C%20Salt%20Lake%20
propdata["streetViewServiceUrl"] = https://proxy.zillowapi.com/street-view-url?zpid=12786046&address=2941%20S%20Zenith%20Cir%2C%20Salt%20Lake%20City%2
propdata["staticMap"] = {'sources': [{'width': 192, 'url': 'https://maps.googleapis.com/maps/api/staticmap?center=40.708138,-111.86154&zoom=15&size=19
propdata["postingUrl"] = None
propdata["richMedia"] = None
propdata["hasPublicVideo"] = False
propdata["primaryPublicVideo"] = None
propdata["richMediaVideos"] = None
propdata["photos"] = [{'caption': '', 'mixedSources': {'jpeg': [{'url': 'https://photos.zillowstatic.com/fp/65b1eb58880e9c69de5bea9a6cbe8c61-cc_ft_192
propdata["listingSubType"] = {'isFSBA': True, 'isFSBO': False, 'isPending': False, 'isNewHome': False, 'isForeclosure': False, 'isBankOwned': False, '
propdata["tourViewCount"] = 0
propdata["postingContact"] = {'name': 'Catherine Richards', 'photo': None}
propdata["vrModel"] = {'vrModelGuid': None, 'revisionId': None}
propdata["thirdPartyVirtualTour"] = {'externalUrl': 'http://www.2941zenithcir.com/unbranded', 'lightboxUrl': None, 'staticUrl': None, 'providerKey': N
propdata["listingAccount"] = None
propdata["topNavJson"] = {'topnav': {'json': {'logo': {'text': 'Zillow Real Estate', 'href': '/'}, 'main': {'sections': [{'link': {'text': 'Buy', 'hre
propdata["listingFeedID"] = None
propdata["livingAreaUnitsShort"] = sqft
propdata["priceChange"] = None
propdata["priceChangeDate"] = None
propdata["priceChangeDateString"] = None
propdata["formattedChip"] = {'location': [{'fullValue': '2941 S Zenith Cir'}, {'fullValue': 'Salt Lake City, UT 84106'}]}
propdata["hideZestimate"] = False
propdata["comingSoonOnMarketDate"] = None
propdata["isPreforeclosureAuction"] = False
propdata["mortgageRates"] = {'thirtyYearFixedRate': 6.177}
propdata["annualHomeownersInsurance"] = 3108
propdata["lastSoldPrice"] = None
propdata["isHousingConnector"] = False
propdata["responsivePhotosOriginalRatio"] = [{'caption': '', 'mixedSources': {'jpeg': [{'url': 'https://photos.zillowstatic.com/fp/65b1eb58880e9c69de5
propdata["streetViewMetadataUrlMapLightboxAddress"] = https://maps.googleapis.com/maps/api/streetview/metadata?location=2941%20S%20Zenith%20Cir%2C%20S
propdata["thumb"] = [{'url': 'https://photos.zillowstatic.com/fp/65b1eb58880e9c69de5bea9a6cbe8c61-p_a.jpg'}]
propdata["isRecentStatusChange"] = False
propdata["isNonOwnerOccupied"] = False
propdata["county"] = Salt Lake County
propdata["isFeatured"] = False
propdata["rentalApplicationsAcceptedType"] = REQUEST_TO_APPLY
propdata["listingTypeDimension"] = For Sale by Agent
propdata["featuredListingTypeDimension"] = organic
propdata["brokerIdDimension"] = For Sale by Agent
propdata["keystoneHomeStatus"] = ForSale
propdata["pageUrlFragment"] = ForSale
propdata["isRentalsLeadCapMet"] = False
propdata["isPaidMultiFamilyBrokerId"] = False
propdata["selfTour"] = {'hasSelfTour': False}

'''




'''
dict_keys(
    'regionIds', 
    'floorPlans', 
    'buildingAttributes', 
    '__typename', 
    'lotId', 
    'bdpUrl', 
    'city', 
    'county', 
    'state', 
    'zipcode', 
    'fullAddress', 
    'isWaitlisted', 
    'listingFeatureType', 
    'breadcrumbs', 
    'ungroupedUnits', 
    'contactInfo', 
    'isInstantTourEnabled', 
    'zpid', 
    'buildingPhoneNumber', 
    'isLandlordLiaisonProgram', 
    'buildingType', 
    'isInstantTourCancellable', 
    'bestGuessTimezone', 
    'rentalInstantTour', 
    'buildingName', 
    'isLowIncome', 
    'isSeniorHousing', 
    'isStudentHousing', 
    'ppcLink', 
    'streetAddress', 
    'reviewsInfo', 
    'housingConnector', 
    'screeningCriteria', 
    'mapTileGoogleMapUrlLocationModule', 
    'mapTileGoogleMapUrlFullWidthMax', 
    'streetViewTileImageUrlLocationModuleLatLong', 
    'streetViewTileImageUrlLocationModuleAddress', 
    'address', 
    'streetViewTileImageUrlHalfWidthLatLong', 
    'streetViewTileImageUrlHalfWidthAddress', 
    'latitude', 
    'longitude', 
    'streetViewMetadataUrlMediaWallLatLong', 
    'streetViewMetadataUrlMediaWallAddress', 
    'photoCount', 
    'amenitiesVRModels', 
    'videos', 
    'galleryPhotos', 
    'galleryAmenityPhotos', 
    'description', 
    'amenityDetails', 
    'bestMatchedUnit', 
    'photos', 
    'amenityPhotos', 
    'staticMap', 
    'staticMapSatellite', 
    'streetViewLatLong', 
    'streetViewAddress', 
    'thirdPartyVirtualTours', 
    'listingMetadata', 
    'currency', 
    'specialOffers', 
    'homeTypes', 
    'walkScore', 
    'engrain', 
    'unitsVRModels'])
'''

'''
propdata['regionIds'] = {'city': 6909, '__typename': 'RegionIds'}
 propdata['floorPlans'] = [{'beds': 0, 'maxPrice': 1549, 'minPrice': 1495, '__typename': 'FloorPlan', 'zpid': '207873109
 propdata['buildingAttributes'] = {'applicationFee': None, 'administrativeFee': None, 'depositFeeMin': None, 'depositFee
 propdata['__typename'] = Building
 propdata['lotId'] = 2355800535
 propdata['bdpUrl'] = /b/brixton-salt-lake-city-ut-BLdyjx/
 propdata['city'] = Salt Lake City
 propdata['county'] = Salt Lake County
 propdata['state'] = UT
 propdata['zipcode'] = 84106
 propdata['fullAddress'] = 660 E Wilmington Ave, Salt Lake City, UT 84106
 propdata['isWaitlisted'] = False
 propdata['listingFeatureType'] = featured
 propdata['breadcrumbs'] = [{'text': 'UT', 'gaLabel': 'State', '__typename': 'Breadcrumb', 'path': 'https://www.zillow.c
 propdata['ungroupedUnits'] = None
 propdata['contactInfo'] = {'providerListingID': '4jdtepq0vc1a8', 'contactType': 'FOR_RENT', 'rentalApplicationsAccepted
 propdata['isInstantTourEnabled'] = False
 propdata['zpid'] = 2067985794
 propdata['buildingPhoneNumber'] = 385-238-1083
 propdata['isLandlordLiaisonProgram'] = False
 propdata['buildingType'] = FOR_RENT
 propdata['isInstantTourCancellable'] = False
 propdata['bestGuessTimezone'] = America/Denver
 propdata['rentalInstantTour'] = None
 propdata['buildingName'] = Brixton
 propdata['isLowIncome'] = False
 propdata['isSeniorHousing'] = False
 propdata['isStudentHousing'] = False
 propdata['ppcLink'] = None
 propdata['streetAddress'] = 660 E Wilmington Ave
 propdata['reviewsInfo'] = None
 propdata['housingConnector'] = {'hcLink': None, '__typename': 'HousingConnector'}
 propdata['screeningCriteria'] = None
 propdata['mapTileGoogleMapUrlLocationModule'] = https://maps.googleapis.com/maps/api/staticmap?center=40.723019,-111.87
 propdata['mapTileGoogleMapUrlFullWidthMax'] = https://maps.googleapis.com/maps/api/staticmap?center=40.723019,-111.8720
 propdata['streetViewTileImageUrlLocationModuleLatLong'] = https://maps.googleapis.com/maps/api/streetview?location=40.7
 propdata['streetViewTileImageUrlLocationModuleAddress'] = https://maps.googleapis.com/maps/api/streetview?location=660%
 propdata['address'] = {'streetAddress': '660 E Wilmington Ave', 'city': 'Salt Lake City', 'state': 'UT', 'zipcode': '84
 propdata['streetViewTileImageUrlHalfWidthLatLong'] = https://maps.googleapis.com/maps/api/streetview?location=40.723019
 propdata['streetViewTileImageUrlHalfWidthAddress'] = https://maps.googleapis.com/maps/api/streetview?location=660%20E%2
 propdata['latitude'] = 40.723019
 propdata['longitude'] = -111.872074
 propdata['streetViewMetadataUrlMediaWallLatLong'] = https://maps.googleapis.com/maps/api/streetview/metadata?location=4
 propdata['streetViewMetadataUrlMediaWallAddress'] = https://maps.googleapis.com/maps/api/streetview/metadata?location=6
 propdata['photoCount'] = 41
 propdata['amenitiesVRModels'] = None
 propdata['videos'] = []
 propdata['galleryPhotos'] = [{'caption': None, 'mixedSources': {'webp': [{'url': 'https://photos.zillowstatic.com/fp/2b
 propdata['galleryAmenityPhotos'] = [{'caption': None, 'mixedSources': {'webp': [{'url': 'https://photos.zillowstatic.co
 propdata['description'] = We are Open! Call Today to Schedule your Tour!
 propdata['amenityDetails'] = {'hours': ['Mon - Fri: 9:00AM - 6:00PM', 'Sat: 10:00AM - 5:00PM', 'Sun: Closed'], '__typen
 propdata['bestMatchedUnit'] = {'hdpUrl': '/homedetails/2067985794_zpid/', 'unitNumber': 'Unit A604', '__typename': 'Uni
 propdata['photos'] = [{'caption': None, 'mixedSources': {'webp': [{'url': 'https://photos.zillowstatic.com/fp/2b469fcca
 propdata['amenityPhotos'] = [{'caption': None, 'mixedSources': {'webp': [{'url': 'https://photos.zillowstatic.com/fp/2b
 propdata['staticMap'] = https://maps.googleapis.com/maps/api/staticmap?center=40.723019,-111.872074&zoom=17&size=768x57
 propdata['staticMapSatellite'] = https://maps.googleapis.com/maps/api/staticmap?center=40.723019,-111.872074&zoom=17&si
 propdata['streetViewLatLong'] = https://maps.googleapis.com/maps/api/streetview?location=40.723019,-111.872074&size=768
 propdata['streetViewAddress'] = https://maps.googleapis.com/maps/api/streetview?location=660%20E%20Wilmington%20Ave%2C%
 propdata['thirdPartyVirtualTours'] = []
 propdata['listingMetadata'] = {'BuildingDataG': 'false', 'BuildingDataH': 'false', 'BuildingDataI': 'false', 'BuildingD
 propdata['currency'] = USD
 propdata['specialOffers'] = [{'description': 'Lease Now & Get Up to $500 Off! *Restrictions apply. Contact office for m
 propdata['homeTypes'] = ['apartment']
 propdata['walkScore'] = {'walkscore': 86, '__typename': 'WalkScoreResponse'}
 propdata['engrain'] = {'mapId': '16530', 'availableBedroomOptions': ['Studio', '1 Bedroom', '2 Bedrooms'], 'levels': [{
 propdata['unitsVRModels'] = None

'''