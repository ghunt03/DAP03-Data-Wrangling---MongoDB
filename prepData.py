import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import csv
import numpy as np
import codecs
import json

# Change UPDATE to False to see original data format
UPDATE = True
# Change GEOCODE to False to skip Geo-coding (helps with speed)
GEOCODE = True

# Change PREPDATA to True to generate JSON file otherwise change to false for auditing
PREPDATA = False

CITYDATAFILE = "data_suburbs.txt"
AMENITYDATAFILE = "data_amenity_map.csv"
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
OSMFILE = "sample.osm"

cityData = []
coordinates = []
amenity_map = {}
AMENITYTAGS = ('amenity', "bus", "bus_stop", "ferry", "rail", "railway", "historic", "leisure", "tourism") 
address_error_count = 0


tag_keys = {}
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_type_expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
          "Trail", "Parkway", "Commons", "Streets", "Close", "Broadway", "Circuit", "Parade", "Terrace", 
          "Way", "Boulevarde", "Arcade", "Crescent", "Highway", "Esplanade", "Plaza", "Mall"]

# UPDATE THIS VARIABLE
street_type_maps = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "Street)": "Street",
            "street": "Street",
            "underpass": "",
            "West": "",
            "North": "",
            "South": "",
            "East": "",
            "st": "Street"
            }
street_direct_replacements = {
    "Church and Market Street Corner": "Cnr Church and Market Street",
    "ApplegumCrescent": "Applegum Crescent",
    "2150": "Phillip Street",
    "Addison road, nr East street, marrickville": "Cnr Addison Road and East Street",
    "Argyle Street, Level 2 Dining Precinct": "Argyle Street",
    "Centenary": "Centenary Drive",
    "Church Street Mall": "Church Street",
    "Clarance Street": "Clarence Street",
    "Cnr Nardoo & Norfolk Streets": "Cnr Nardoo and Norfolk Street",
    "Cnr Station & Woodriff Streets": "Cnr Station and Woodriff Street",
    "Corner of Botany and O'riordan Street": "Cnr of Botany and O'riordan Street",
    "Cox Road": "Coxs Road",
    "Douglast Street": "Douglas Street",
    "Edward": "Edward Street",
    "Greenwood Plaza Shopping Centre, 36 Blue Street": "Blue Street",
    "118 Railway Parade": "Railway Parade",
    "3 Park Street": "Park Street",
    "390-392 Pittwater Road": "Pittwater Road",
    "536 New South Head Road": "New South Head Road",
    "730 Parramatta Road": "Parramatta Road",
    "Hawksebury Road": "Hawkesbury Road",
    "Holt Street (enter via Gladstone Street": "Holt Street",
    "Jersy Road": "Jersey Road",
    "Jones": "Jones Street",
    "Middleton Street, Petersham, nr Stanmore Street": "Cnr Middleton and Stanmore Street",
    "Mulgoa Road & Wolseley Street": "Cnr Mulgoa Road and Wolseley Street",
    "Ogilve": "Ogilvie Street",
    "Rooty Hill Road North, Plumpton": "Rooty Hill Road North",
    "Victoria Street, Revesby": "Victoria Street",
    "WIlford Street": "Wilford Street",
    "WIlliam Street": "William Street",
    "Wolli": "Wolli Street",
    "Wollit": "Wolli Street",
    "cnr Great Western Highway & Carlisle Avenue": "Cnr Great Western Highway and Carlisle Avenue",
    "cnr The Ponds Boulevard and Riverbank Drive": "Cnr The Ponds Boulevard and Riverbank Drive",
    "corner Fletcher and Dellview Street": "Cnr Fletcher and Dellview Street",
    "ingleby Street": "Ingleby Street",
    "topping": "Topping Street"    
}



suburb_maps = {
    "1": "Sydney",
    "Bella Visa": "Bella Vista",
    "Beverly Hills - Sydney NSW": "Beverly Hills",
    "CROYDON": "Croydon",
    "Camerdown": "Camperdown",
    "Gulidford": "Guildford",
    "Mascot, Sydney": "Mascot",
    "Mascot Airport": "Mascot",
    "North Willoghby": "North Willoughby",
    "Orchard Hills, New South Wales": "Orchard Hills",
    "Rosebay": "Rose Bay",
    "Roseberry": "Rosebery",
    "Werrinton": "Werrington",
    "kensington": "Kensington",
    "st Ives": "St Ives",
    "sydney": "Sydney",
    "turrella": "Turrella",
    "waterloo": "Waterloo",
    "wentworthville": "Wentworthville",
    "wollstonecraft": "Wollstonecraft"
}

postcode_maps = {
    "Phillip Street": "2150"
}

sports_map = {
    "10pin": "bowling",
    "aussie rules": "football",
    "basketball half court": "basketball",
    "beachvolleyball": "volleyball",
    "bmx": "bicycle motocross",
    "boules": "bowls",
    "canoe/kayak": "canoe",
    "climbing adventure": "climbing",
    "crikcet": "cricket",
    "criket": "cricket",
    "exercise": "fitness",
    "gym": "fitness",
    "australian football": "football",
    "long jump": "athletics",
    "motocross": "bicycle motocross",
    "rc car racing": "rc car",
    "rugby league": "rugby",
    "rugby union": "rugby",
    "skate park": "skateboard",
    "racquet": "squash",
    "sw": "swimming"

}

def matches_tag_type(elem, tag_type):
    return (elem.attrib['k'] == tag_type)

def matches_tags(elem, tags):
    return (elem.attrib['k'] in tags)

def update_street_name(address):
    street_name = address['street']
    if street_name in street_direct_replacements:
        street_name = street_direct_replacements[street_name]
    else:
        m = street_type_re.search(street_name)
        if m:
            street_type = m.group()
            if street_type not in street_type_expected and street_type in street_type_maps:
                try:
                    street_name = re.sub(street_type_re, street_type_maps[street_type], street_name)
                except:
                    pass
    return street_name.rstrip(' \t\r\n\0')

def update_suburb_name(address):
    suburb_name = address['city']
    if suburb_name in suburb_maps:
        suburb_name = suburb_maps[suburb_name]
    return suburb_name

def update_postcode(address):
    postcode = address['postcode']
    if postcode in postcode_maps:
        postcode = postcode_maps[postcode]
    postcode = postcode.replace("NSW ", "")
    return postcode



def getCityData():
    data = []
    coordinateList= []    
    with open(CITYDATAFILE) as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)
        for row in rows:
            #filter for records in NSW only
            if row[4] == 'NSW':
                item = {}
                coords = [0,0]
                item['postcode'] = row[1]
                item['city'] = row[2]
                coords =  [float(row[9]), float(row[10])]
                coordinateList.append(coords)
                item['pos'] = coords
                data.append(item)
    return data, coordinateList

def getAmenityData():
    data = {}
    with open(AMENITYDATAFILE) as f:
        reader = csv.reader(f, delimiter=",")
        rows = list(reader)
        for row in rows:
            data[row[0]] = row[1]
    return data

def getPostcodeCity(to_find, fieldname, data):
    if to_find == '':
        return None
    else:
        my_item = next((item for item in data if item[fieldname] == to_find), None)
        return my_item

def getClosestSuburb(node, nodes):
    nodes = np.asarray(nodes)
    dist_2 = np.sum((nodes - node)**2, axis=1)
    return np.argmin(dist_2)


def validCoords(coords):
    return (not coords[0] == 0 and not coords[1] == 0)

def fixAddress(node):
    address = node['address']
    address['street'] = update_street_name(address)
    address['city'] = update_suburb_name(address)
    address['postcode'] = update_postcode(address)
    if address['city'] == '' and address['postcode'] == '':
        pos = node['pos']
        # geocode pos
        if validCoords(pos) and GEOCODE:
            pos_index = getClosestSuburb(pos, coordinates)
            address['city'] = cityData[pos_index]['city']
            address['postcode'] = cityData[pos_index]['postcode']
    else:
        # check if city is empty and postcode exists then search for city from postcodeCityList
        if address['city'] == '' and not address['postcode'] == '':
            result = getPostcodeCity(address['postcode'], 'postcode', cityData)
            if result:
                address['city'] = result['city']
        # check if postcode is empty and city exists then search for city from postcodeCityList
        if address['postcode'] == '' and not address['city'] == '':
            result = getPostcodeCity(address['city'], 'city', cityData)
            if result:
                address['postcode'] = result['postcode']
    return address



def fixAmenity(amenity):
    if amenity in amenity_map:
        amenity = amenity_map[amenity]
    return amenity




def fixMaxSpeeed(value):
    value = re.sub(r'[^0-9]',' ', value)
    try:
        return int(value)
    except ValueError:
        return 0

def fixFloat(value):
    value = ''.join([c for c in value if c in '1234567890.'])
    try:
        return float(value)
    except:
        return 0

def addToKeyCheck(value):
    if value in tag_keys:
        tag_keys[value] = tag_keys[value] + 1
    else:
        tag_keys[value] = 1


def fixSports(tag_value):
    sports = tag_value.replace("_"," ").replace(",",";").lower()
    sports = sports.split(';')
    results = []
    for sport in sports:
        sport = sport.strip()
        if sport in sports_map:
            sport = sports_map[sport]
        results.append(sport)
    return results

def shape_element(element):
    node = {}
    address = { 
            'street': '',
            'city': '',
            'postcode': '',
            'housenumber': ''
        }
    node["id"] = element.get("id")
    node["type"] = element.tag
    # Get latitude and longitude
    try:
        node["pos"] = [float(element.get("lat")), float(element.get("lon"))]
    except:
        node["pos"] = [0, 0]

    # Get details of creation for current node
    node["created"] = {}
    for created_att in CREATED:
        node['created'][created_att] = element.get(created_att)

    
    
    amenity_type = ""
    has_address = False
    is_amentity = False
    # Loop through tags and include if required
    for tag in element.iter("tag"):
        tag_value = tag.attrib['v']
        if matches_tags(tag, ("addr:street",)):
            address['street'] = tag_value
            has_address = True
        elif matches_tags(tag, ("addr:city", "addr:suburb")):
            address['city'] = tag_value
            has_address = True
        elif matches_tags(tag, ("addr:postcode",)):
            address['postcode'] = tag_value
            has_address = True
        elif matches_tags(tag, ("addr:housenumber",)):
            address['housenumber'] = tag_value
            has_address = True
        elif matches_tags(tag, AMENITYTAGS):
            is_amentity = True
            amenity_type = tag_value
        elif matches_tag_type(tag, "cuisine"):
            node['cuisine'] = tag_value
        elif matches_tag_type(tag, "name"):
            node['name'] = tag_value
        elif matches_tag_type(tag, "sport"):
            node['sport_type'] = fixSports(tag_value)

        elif matches_tag_type(tag, "maxspeed"):
            tag_value = fixMaxSpeeed(tag_value)
            if tag_value > 0:
                node['maxspeed'] = tag_value
        elif matches_tags(tag, ("maxheight","maxheightphysical")):
            tag_value = fixFloat(tag_value)
            if tag_value > 0:
                node['maxheight'] = tag_value
        elif matches_tag_type(tag, "maxlength"):
            tag_value = fixFloat(tag_value)
            if tag_value > 0:
                node['maxlength'] = tag_value
        elif matches_tag_type(tag, "maxweight"):
            tag_value = fixFloat(tag_value)
            if tag_value > 0:
                node['maxweight'] = tag_value
           
    # loop through nd elements and extract node references
    if element.tag == "way":
        nd_refs = []
        for nd in element.iter("nd"):
            nd_refs.append(nd.get("ref"))
        if nd_refs:
            node["node_refs"] = nd_refs       
    
    if has_address or validCoords(node['pos']):
        node['address'] = address
        if UPDATE:               
            node['address'] = fixAddress(node) 

    if is_amentity:
        if UPDATE:
            amenity_type = fixAmenity(amenity_type)
        node['amenity_type'] = amenity_type

    
    
    return node

def audit_map(file_in):
    ''' Function for auditing data
    tag_keys allows for data to be grouped / audited. 
    To populate tag_keys add addToKeyCheck(value) to the relevant field 
    that needs to be audited
    '''
    nodes = []
    context = ET.iterparse(file_in, events=("start", "end"))
    context = iter(context)
    event, root = context.next()
    counter = 0
    for event, element in context:
        if event == "end" and element.tag in ("node", "way"):
            node = shape_element(element)
            nodes.append(node)
            element.clear()
        
    root.clear()
    pprint.pprint(tag_keys)    


def process_map(file_in):
    file_out = "{0}.json".format(file_in)
    with codecs.open(file_out, "w") as fo:
        context = ET.iterparse(file_in, events=("start", "end"))
        context = iter(context)
        event, root = context.next()
        for event, element in context:
            if event == "end" and element.tag in ("node", "way"):
                node = shape_element(element)
                if node:
                    fo.write(json.dumps(node, indent=2)+"\n")
                element.clear()
        root.clear()



if __name__ == '__main__':
    cityData, coordinates = getCityData()
    amenity_map = getAmenityData()
    if PREPDATA:
        process_map(OSMFILE)
    else:
        audit_map(OSMFILE)