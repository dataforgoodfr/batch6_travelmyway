import requests
import pandas as pd
import json
from datetime import datetime as dt
import copy
from geopy.distance import distance
import tmw_api_keys
import TMW as tmw
import constants
from navitia_client import Client
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
import numpy as np


def get_navitia_coverage(client):
    """
    The navitia API is separated into different coverage region (one for california, one for PAris-IDF ...)
    We call the API to get all those coverage and know which coverage region to call for a given scenario
    """
    # call API for all coverages
    response_cov = client.raw('coverage', multipage=False, page_limit=10, verbose=True)
    # turn coverage into DF
    df_cov = pd.DataFrame.from_dict(response_cov.json()['regions'])

    print(f'{df_cov.shape[0]} regions found, here is an example:\n {df_cov.sample()}')
    # clean the geographical shape
    df_cov['polygon_clean'] = df_cov.apply(clean_polygon_for_coverage, axis=1)
    return df_cov


def clean_polygon_for_coverage(x):
    """
    The API call for coverage returns multipolygons (a list of one or several polygon) for each region
    but it is a string that we must convert to an actual Polygon object (in order to use function is point in polygon)
    Most regions have only one polygon, so we decide to only consider the biggest polygon for each regions
    """
    # split "polygon" as a string
    if x['shape'] == '':
        # Polygon is null
        return None

    # split by '(' to see if there are several shape within polygon
    split_meta = x['shape'].split('(')
    # we want ton only keep the biggest Polygon, first we compute sizes for all "polygon"
    sizes_pol = np.array([])
    for i in split_meta:
        sizes_pol = np.append(sizes_pol, len(sizes_pol))
    # keep the biggest and act like there was only one from the beginning
    split_pol = split_meta[np.argmax(sizes_pol)]

    # Let's split the polygon into a list of geoloc (lat, long)
    split_pol = split_pol.split(',')
    # clean the last point (the first and the last are the same cause the polygon has to be "closed")
    split_pol[-1] = split_pol[0]
    # recreate latitude and longitude list
    lat = np.array([])
    long = np.array([])
    for point in split_pol:
        split_point = point.split(' ')
        lat = np.append(lat, split_point[0])
        long = np.append(long, split_point[1])

    # return the object Polygon
    return Polygon(np.column_stack((long, lat)))


def find_navita_coverage_for_points(point_from, point_to, df_cov):
    """
    This function finds in which coverage regions are the 2 points.
    If any point is not in any region, or the 2 points are in different regions we have an error
    """
    # convert into geopoint
    point_from = Point(point_from[0], point_from[1])
    point_to = Point(point_to[0], point_to[1])
    # test if points are within polygon for each region
    are_points_in_cov = df_cov[~pd.isna(df_cov.polygon_clean)].apply(
        lambda x: (x.polygon_clean.contains(point_from)) & (x.polygon_clean.contains(point_to)), axis=1)
    # find the good region
    id_cov = df_cov[~pd.isna(df_cov.polygon_clean)][are_points_in_cov].id
    if not id_cov.empty:
        return id_cov.values[0]
    else:
        return None

"""
NAVITIA
FUNCTIONS
"""
def start_navitia_client():
    from navitia_client import Client
    navitia_client = Client(user='8ad3db27-5eec-473d-9ff6-50d35fdf0da6')
    return navitia_client

def navitia_query_directions(coord, _id=0):
    navitia_client = start_navitia_client()
    #coord = [query['query']['start']['coord'], query['query']['to']['coord'] ]
    cov_reg = find_navita_coverage_for_points(coord[0], coord[1], _NAVITIA_COV)
    print(f'coverage region for navita is {cov_reg}')
    print(f'coverage region for navita is {cov_reg}')
    if cov_reg is not None:
        url = f'coverage/{cov_reg}/journeys?from={coord[0][1]};{coord[0][0]}&to={coord[1][1]};{coord[1][0]}'
        print(f'url to navitia is {url}')
        # url = url + '&data_freshness=base_schedule&max_nb_journeys=3'
        step = navitia_client.raw(url, multipage=False)
        if step.status_code == 200:
            return navitia_journeys(step.json())
        else:
            return None

    else:
        ValueError('Navitia call between 2 coverage regions')


"""
https: // doc.navitia.io /  # journeys
type = 'waiting' / 'transfer' / 'public_transport' / 'street_network' / 'stay_in' / crow_fly
"""
def navitia_journeys(json, _id=0):
    # all journeys loop
    lst_journeys = list()
    for journey in json['journeys']:
        i = _id

        # journey loop
        lst_sections = list()
        for section in journey['sections']:
            # print(f'pour la section {i}')
            try:
                tmp = navitia_journeys_sections_type(section, _id=i)
                lst_sections.append(tmp)
                # print(f'le step correspondant est {tmp}')
            except:
                print('ERROR : ')
                print('id: {}'.format(i))
                # print(section)
            i = i+1

        lst_journeys.append(lst_sections)
    return lst_journeys

def navitia_journeys_sections_type(json, _id=0):
    switcher_journeys_sections_type = {
        'public_transport': navitia_journeys_sections_type_public_transport,
        'street_network': navitia_journeys_sections_type_street_network,
        'waiting': navitia_journeys_sections_type_waiting,
        'transfer': navitia_journeys_sections_type_transfer,
    }
    tyty = json['type']
    #print(f'on a un type {tyty}')
    func = switcher_journeys_sections_type.get(json['type'], "Invalid navitia type")
    step = func(json, _id)
    return step

def navitia_journeys_sections_type_public_transport(json, _id=0):
    display_information = json['display_informations']
    label = '{} {} / {} / direction: {}'.format(
        display_information['physical_mode'],
        display_information['code'],
        display_information['name'],
        display_information['direction'],
    )
    # print(f'publc transport call')
    step = tmw.journey_step(_id,
                        _type=display_information['network'].lower(),
                        label=label,
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson=json['geojson'],
                        )
    # print(f'publc transport success')
    return step

def navitia_journeys_sections_type_street_network(json, _id=0):
    mode = json['mode']
    mode_to_type = {
        'walking':'walk',
        'bike':'bike',
        'car':'car',
    }
    label = '{} FROM {} TO {}'.format(
        mode_to_type[mode],
        json['from']['name'],
        json['to']['name'],
    )
    # print(f'street call')
    step = tmw.journey_step(_id,
                        _type=mode_to_type[mode],
                        label=label,
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson=json['geojson'],
                        )
    # print(f'street success')
    return step

def navitia_journeys_sections_type_transfer(json, _id=0):
    mode = json['transfer_type']
    mode_to_type = {
        'walking':'walk',
        'bike':'bike',
        'car':'car',
    }
    label = '{} FROM {} TO {}'.format(
        mode_to_type[mode],
        json['from']['name'],
        json['to']['name'],
    )
    # print(f'transfer call')
    step = tmw.journey_step(_id,
                        _type=mode_to_type[mode],
                        label=label,
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson=json['geojson'],
                        )
    # print(f'transfer success')
    return step

def navitia_journeys_sections_type_waiting(json, _id=0):
    # print(f'wait call')
    step = tmw.journey_step(_id,
                        _type='wait',
                        label='wait',
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson='',
                        )
    # print(f'wait success')
    return step

def navitia_journeys_correct(journey, json):
    try:
        if type(j) == journey:
        	True
    except:
        print('ERROR function navitia_journeys_correct() - INPUT Not journey class')
        return False

    return journey


_NAVITIA_COV = get_navitia_coverage(start_navitia_client())
