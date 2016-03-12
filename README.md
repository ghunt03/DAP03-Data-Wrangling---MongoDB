# DAP03 - Data Wrangling with MongoDB
This project involves extracting a dataset from the Open Street Map data and reviewing the data for Validity, Consistency and Correctness and applying appropriate data cleaning processes.
Once the data was cleaned it was then imported into MongoDB for analysis.

This repository contains:
- sample.osm - extract of data from main map datafile
- extract_sample_data.py - code used for generating sample.osm
- data_amenity_map.csv - CSV file containing mapping list for amenity types
- data_suburbs.txt - Data file extracted from www.geonames.org containing postcodes, suburbs and GPS coordinates for Australia
- prepData.py - Python file used to audit and clean the data, once the auditing and cleaning was complete the same functions were used to generate the JSON file which could then be imported into MongoDB
- prepData_createAmenityMap.py - Python file which takes a list of amenity types and creates a CSV. Only used to make the prepData.py file more readable
- Exercises folder - contains python files created in Lesson 6 of the Data Wrangling course
- report.pdf - PDF version of report

An online version of the report can be viewed [here][report]

[report]: http://ghunt03.github.io/DAProjects/DAP03/DataAnalysisProject3WrangleOpenStreetMapData.html

