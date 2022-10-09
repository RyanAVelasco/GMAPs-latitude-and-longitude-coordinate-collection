import time
import os
import re
import requests as r
import string

from bs4 import BeautifulSoup as bs
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.wait import WebDriverWait
 

def collect_county_names(navigate_to_url):
    list_of_countries = []
    
    resp = r.get(navigate_to_url)

    # Parse HTML using BeautifulSoup
    # and collect all listed countries
    soup = bs(resp.text, 'lxml')
    table = soup.find('tbody')
    rows = table.find_all('td')
    for row in rows:
        if row.string[0] in string.ascii_letters: 
            list_of_countries.append(row.string)   
    
    return list_of_countries


def match_cities_to_countries(csv_to_read):    
    # Drop unneeded columns from geonames csvfile
    return drop_columns(csv_to_read)


def drop_columns(csv_to_read):
    return csv_to_read.drop(labels=[
                                'Geoname ID', 
                                'ASCII Name', 
                                'Alternate Names', 
                                'Feature Class',
                                'Feature Code', 
                                'Country Code', 
                                'Country Code 2',
                                'Admin1 Code', 
                                'Admin2 Code', 
                                'Admin3 Code', 
                                'Admin4 Code',
                                'Population', 
                                'Elevation', 
                                'DIgital Elevation Model', 
                                'Timezone',
                                'Modification date', 
                                'LABEL EN', 
                                'Coordinates'
                                ], axis=1)


def get_gmap_latitude_and_longitude(city_to_find, country_to_search):
    try:
        firefox.get(URL_GMAP + city_to_find + ',' + country_to_search)
    except TimeoutError:
        return TimeoutError + f' for {city_to_find}'
        
    url_check = firefox.current_url

    # Using this as the means of keeping
    # the program going if the 
    # url_check fails
    start_time = time.localtime()[4]
    end_time = time.localtime()[4] + 1
    if end_time >= 60:
        end_time -= 60

    # Continues waiting for current url to
    # change to the proper one with
    # latitude and longitude in url.
    while firefox.current_url == url_check:
        if time.localtime()[4] == end_time:
            break
        continue

    latitude, longitude, depth = firefox.current_url.split('@')[1].split('/')[0].split(',')
    return latitude, longitude, depth


# Set main path
PWD = os.getcwd() + '/'

# Make file structure
for folders_to_create in ['data', 
                         'data/raw', 
                         'data/backup',  
                         'deliverable']:
    try:os.mkdir(PWD + folders_to_create)
    except FileExistsError: pass

# Set variables
URL_COUNTRY_LIST = r'https://www.worldometers.info/geography/alphabetical-list-of-countries/'
URL_GMAP = r'https://www.google.com/maps/place/'
CSV_LIST_OF_CITIES = pd.read_csv(f'{PWD}geonames-all-cities-with-a-population-1000.csv', delimiter=';')

# Begin collection here prior to using GMAPS
COUNTRIES = collect_county_names(URL_COUNTRY_LIST)
country_and_city_names = match_cities_to_countries(CSV_LIST_OF_CITIES)
country_and_city_names.to_csv(f'{PWD}data/raw/city_countries.csv', sep=';', index=False, mode='w')

#Create a backup of the new csv
os.system(f'cp "{PWD}data/raw/city_countries.csv" "{PWD}data/backup/city_countries.csv"')

search_terms_for_gmaps = {}

# Begin by turning the countries into dict keys
with open(f'{PWD}data/raw/city_countries.csv', 'r') as f:
    lines = f.readlines()

    # Use country name as keys
    for line in lines[1:]:
        if line.split(';')[1].rstrip() == '':
            continue
        search_terms_for_gmaps[line.split(';')[1].rstrip()] = ''
        
    # Concate city names for future processing
    for line in lines[1:]:
        if line.split(';')[1].rstrip() == '':
            continue
        search_terms_for_gmaps[line.split(';')[1].rstrip()] += line.split(';')[0] + '~~'

# Take city names and cast to list
# remove empty values and sort
for country, city in search_terms_for_gmaps.items():
    city = city.split('~~')        
    if '' in city:
        empty_value = city.index('')
        city.pop(empty_value)
        city.insert(empty_value, 'NaN')
    city.sort()
    
    search_terms_for_gmaps[country] = city

# Start selenium for latitude and
# longitude collecting
firefoxoptions = webdriver.FirefoxOptions()
firefoxoptions.headless = True
firefox = webdriver.Firefox(options=firefoxoptions)
firefox.set_page_load_timeout(90)

# Create lists and dictionary for delivery
cities = []
countries = []
latitudes = []
longitudes = []

# Write to deliverable information.csv

with open(f'{PWD}deliverable/deliverable_information.csv', 'r') as f:
    current_listings = f.readlines()

for country, city_list in search_terms_for_gmaps.items():
    for city in city_list:
        reset = False
        
        # if cities is recoreded then check next
        for listings in current_listings:
            if re.search(f'{country},{city}*', listings) is not None:
                reset = True
                break
        
        if reset is False:
            latitude, longitude, depth = get_gmap_latitude_and_longitude(city, country)
            if city == '':
                city = 'NaN'
            if country == '':
                country = 'NaN'
                
            with open(f'{PWD}deliverable/deliverable_information.csv', 'a') as f:
                f.write(f'{country},{city},{latitude},{longitude}\n')

# Close webdriver once program is complete.
firefox.close()

# Read the created CSV file for inspection.
delivery = pd.read_csv('deliverable/deliverable_information.csv')
delivery


