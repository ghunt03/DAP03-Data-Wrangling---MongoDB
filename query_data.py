
from pymongo import MongoClient
import pprint

def getBounds():
	bounds = {
		'minLat': -34.0151,
		'minLon': 150.643,
		'maxLat': -33.6706,
		'maxLon': 151.32
	}
	return bounds
	



def get_db():
    client = MongoClient('localhost:27017')
    db = client.osm
    return db

def get_results(db, query):
	return db.sydney.aggregate(query)

def print_results(results):
	for row in results:
		print row


def number_of_documents(db):
	return db.sydney.find().count() 

def number_of_element_types(db, element_type):
	return db.sydney.find({"type":element_type}).count()

def distinct_users(db):
	return db.sydney.find().distinct("created.user")

def amenity_query():
	query = [
		{"$group" : {"_id": "$amenity_type", "count": { "$sum" : 1}}},
		{"$sort"  : {"count": -1}},
		{"$limit" : 10}
	]

	return query

def sports_query():
	query = [
		{"$group" : {"_id": "$sport_type", "count": { "$sum" : 1}}},
		{"$sort"  : {"count": -1}}
	]
	return query




if __name__ == "__main__":
    # For local use
	db = get_db()
	print "Map Bounds: ", getBounds()
	print "Number of Documents: ", number_of_documents(db)
	print "Number of nodes: ", number_of_element_types(db, "node")
	print "Number of ways: ", number_of_element_types(db, "way")

	users = distinct_users(db)
	pprint.pprint(users)
	print "Number of Distinct users:", len(users)

	amenities = get_results(db, amenity_query())
	print_results(amenities)

	sports = get_results(db, sports_query())
	print_results(sports)
