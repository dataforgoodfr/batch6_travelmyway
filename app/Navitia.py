import pandas as pd
import tmw_api_keys
import TMW as tmw
import constants
# import folium
from navitia_client import Client
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import numpy as np
import re


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
        raise ValueError("ERROR: NAVITIA query on 2 different regions")



"""
NAVITIA FUNCTIONS
"""


def start_navitia_client():
    Navitia_api_key = tmw_api_keys.NAVITIA_API_KEY
    navitia_client = Client(user=Navitia_api_key)
    return navitia_client


def navitia_query_directions(query, _id=0):
    '''
    start (class point)
    end (class point)
    '''
    navitia_client = start_navitia_client()

    try :
        navitia_region = find_navita_coverage_for_points(query.start_point, query.end_point, _NAVITIA_COV)
    except:
        # coverage issue
        return None
    # if start.navitia['name'] != end.navitia['name']:  # region name (ex: idf-fr)
    #     print('ERROR: NAVITIA query on 2 different regions')

    # start_coord = ";".join(map(str, query.start_point))
    # end_coord = ";".join(map(str, query.end_point))
    start_coord = str(query.start_point[1]) + ";" + str(query.start_point[0])
    end_coord = str(query.end_point[1]) + ";" + str(query.end_point[0])
    url = f'coverage/{navitia_region}/journeys?from={start_coord}&to={end_coord}'
    url = url + '&data_freshness=base_schedule&max_nb_journeys=3'

    step = navitia_client.raw(url, multipage=False)

    if step.status_code == 200:
        return navitia_journeys(step.json())

    else:
        print(f'ERROR {step.status_code} from Navitia')
        return None


def navitia_coverage_global():
    navitia_client = start_navitia_client()
    cov = navitia_client.raw('coverage', multipage=False, page_limit=10, verbose=True)
    coverage = cov.json()
    for i, region in enumerate(coverage['regions']):
        coverage['regions'][i]['shape'] = navitia_geostr_to_polygon(region['shape'])
    return coverage


def navitia_coverage_plot(coverage):
    _map = init_map(center=(48.864716, 2.349014), zoom_start=4)
    for zone in coverage['regions']:
        folium.vector_layers.PolyLine(locations=zone['shape'],  # start converage
                                      tooltip=zone['name'],
                                      smooth_factor=1,
                                      ).add_to(_map)
    return _map


def navitia_coverage_gpspoint(lon, lat):  #
    navitia_client = start_navitia_client()
    cov = navitia_client.raw('coverage/{};{}'.format(lon, lat), multipage=False, page_limit=10, verbose=True)
    coverage = cov.json()
    try:
        for i, region in enumerate(coverage['regions']):
            coverage['regions'][i]['shape'] = navitia_geostr_to_polygon(region['shape'])
    except:
        print('ERROR: AREA NOT COVERED BY NAVITIA (lon:{},lat:{})'.format(lon, lat))
        return False
    return coverage


def navitia_geostr_to_polygon(string):
    regex = "([-]?\d+\.\d+) ([-]?\d+\.\d+)"
    r = re.findall(regex, string)
    r = [(float(coord[1]), float(coord[0])) for coord in r]  # [ (lat, lon) , (), ()]
    return r


def point_in_polygon(point, polygon):
    import shapely
    from shapely.geometry import Polygon
    poly = Polygon(((p[0],p[1])for p in polygon))
    return True

"""
https://doc.navitia.io/#journeys
type = 'waiting' / 'transfer' / 'public_transport' / 'street_network' / 'stay_in' / crow_fly
"""


def navitia_journeys(json, _id=0):
    # all journeys loop
    lst_journeys = list()
    try:
        journeys = json['journeys']
    except:
        print('ERROR {}'.format(json['error']))
        return None
    for j in json['journeys']:
        i = _id
        # journey loop
        lst_sections = list()
        for section in j['sections']:
            try:
                lst_sections.append(navitia_journeys_sections_type(section, _id=i))
            except:
                print('ERROR : ')
                print('id: {}'.format(i))
                print(section)
            i = i + 1
        lst_journeys.append(tmw.journey(_id, lst_sections))
    return lst_journeys



def navitia_journeys_sections_type(json, _id=0):
    switcher_journeys_sections_type = {
        'public_transport': navitia_journeys_sections_type_public_transport,
        'street_network': navitia_journeys_sections_type_street_network,
        'waiting': navitia_journeys_sections_type_waiting,
        'transfer': navitia_journeys_sections_type_transfer,
    }
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
    step = tmw.journey_step(_id,
                        _type=display_information['network'].lower(),
                        label=label,
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson=json['geojson'],
                        )
    return step


def navitia_journeys_sections_type_street_network(json, _id=0):
    mode = json['mode']
    mode_to_type = {
        'walking': constants.TYPE_WALK,
        'bike': constants.TYPE_BIKE,
        'car': constants.TYPE_CAR,
    }
    label = '{} FROM {} TO {}'.format(
        mode_to_type[mode],
        json['from']['name'],
        json['to']['name'],
    )
    step = tmw.journey_step(_id,
                        _type=mode_to_type[mode],
                        label=label,
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson=json['geojson'],
                        )
    return step


def navitia_journeys_sections_type_transfer(json, _id=0):
    mode = json['transfer_type']
    mode_to_type = {
        'walking': constants.TYPE_WALK,
        'bike': constants.TYPE_BIKE,
        'car': constants.TYPE_CAR,
    }
    label = '{} FROM {} TO {}'.format(mode_to_type[mode], json['from']['name'], json['to']['name'])
    step = tmw.journey_step(_id,
                        _type=mode_to_type[mode],
                        label=label,
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson=json['geojson'],
                        )
    return step


def navitia_journeys_sections_type_waiting(json, _id=0):
    step = tmw.journey_step(_id,
                        _type=constants.TYPE_WAIT,
                        label='wait',
                        distance_m=None,
                        duration_s=json['duration'],
                        price_EUR=[0],
                        gCO2=json['co2_emission']['value'],
                        geojson='',
                        )
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
