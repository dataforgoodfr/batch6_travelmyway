"""
INITIATE CLASSES
"""
import os
import pandas as pd
from datetime import datetime as dt
from app import Trainline
from app import Skyscanner
from app import OuiBus
import folium
from app import tmw_api_keys
import openrouteservice
from openrouteservice import convert
from app import constants


class journey:
    def __init__(self, _id, steps=[]):
        self.id = _id
        self.category = '' # car/train/plane
        self.label = ''
        self.api_list = []
        self.score = 0
        self.total_distance = 0
        self.total_duration = 0
        self.total_price_EUR = 0
        self.total_gCO2 = 0
        self.departure_point = [0, 0]
        self.arrival_point = [0, 0]
        self.departure_date = dt.now()
        self.arrival_date  = dt.now()
        self.steps = steps

    def add(self, steps=[]):
        self.steps.append(steps)
    
    def to_json(self):
        json = {'id': self.id,
                'label': self.label,
                'score': self.score,
                'total_distance': self.total_distance,
                'total_duration': self.total_duration,
                'total_price_EUR': self.total_price_EUR,
                'departure_point': self.departure_point,
                'arrival_point': self.arrival_point,
                'departure_date': self.departure_date,
                'arrival_date': self.arrival_date,
                'total_gCO2': self.total_gCO2,
                'journey': [step.to_json() for step in self.steps]
                }
        return json
    
    def reset(self):
        self.score = 0
        self.total_distance = 0
        self.total_duration = 0
        self.total_price_EUR = 0
        self.total_gCO2 = 0
        return self
    
    def update(self):
        self.score = 0
        self.total_distance = sum(filter(None,[step.distance_m for step in self.steps]))
        self.total_duration = sum(filter(None,[step.duration_s for step in self.steps]))
        self.total_price_EUR = sum(filter(None,[sum(step.price_EUR) for step in self.steps]))
        self.total_gCO2 = sum(filter(None,[step.gCO2 for step in self.steps]))
        return self
    
    def plot_map(self, center=(48.864716,2.349014), tiles = 'Stamen Toner', zoom_start = 4, _map=None):
        import folium
        _map = init_map(center, zoom_start) if _map == None else _map

        for step in self.steps:
            try:
                step.plot_map(center=center, _map=_map)
            except:
                print('ERROR plot map: step id: {} / type: {}'.format(step.id, step.type))
        return _map


class journey_step:
    def __init__(self, _id, _type, label='', distance_m=0, duration_s=0, price_EUR=[0.0], gCO2 = 0, departure_point=[0.0],
                 arrival_point=[0.0], departure_stop_name='', arrival_stop_name='', departure_date=dt.now()
                 , arrival_date=dt.now(), transportation_final_destination='', trip_code='', geojson=''):
        self.id = _id
        self.type = _type
        self.label = label
        self.distance_m = distance_m
        self.duration_s = duration_s
        self.price_EUR = price_EUR
        self.gCO2 = gCO2
        self.departure_point = departure_point
        self.arrival_point = arrival_point
        self.departure_stop_name = departure_stop_name
        self.arrival_stop_name = arrival_stop_name
        self.departure_date = departure_date
        self.arrival_date = arrival_date
        self.trip_code = trip_code #AF350 / TGV8342 / Métro Ligne 2 ect...
        self.transportation_final_destination = transportation_final_destination # Direction of metro / final stop on train ect..
        self.geojson = geojson
        
    def to_json(self):
        json = {'id': self.id,
                'type': self.type,
                'label': self.label,
                'distance_m': self.distance_m,
                'duration_s': self.duration_s,
                'price_EUR': self.price_EUR,
                'departure_point': self.departure_point,
                'arrival_point': self.arrival_point,
                'departure_stop_name': self.departure_stop_name,
                'arrival_stop_name': self.arrival_stop_name,
                'departure_date': self.departure_date,
                'arrival_date': self.arrival_date,
                'trip_code': self.trip_code,
                'gCO2': self.gCO2,
                'geojson': self.geojson,
                }
        return json
    
    def plot_map(self, center=(48.864716,2.349014), zoom_start=4, _map=None):
        import folium
        _map = init_map(center, zoom_start) if _map == None else _map
        
        folium.features.GeoJson(data=self.geojson,
                        name=self.label,
                        overlay=True).add_to(_map)
        return _map

class query:
    def __init__(self, _id, start_point, end_point, datetime=None):
        self.id = _id
        self.start_point = start_point
        self.end_point = end_point
        self.datetime =  ''        # example of format (based on navitia): 20191012T063700

    def to_json(self):
        json = {'id':self.id,
                 'start':self.start_point.to_json(),
                 'end':self.end_point.to_json(),
                 'datetime':self.datetime,
                }
        return json

    def plot_navitia_coverage(self, center=(48.864716,2.349014), zoom_start = 4,_map=None):
        import folium
        _map = init_map(center, zoom_start) if _map == None else _map

        _map = self.start_point.plot_navitia_coverage(_map=_map)
        _map = self.end_point.plot_navitia_coverage(_map=_map)
        return _map

class point:
    def __init__(self, address, near=False):
        self.address = address
        self.coord = geocode_address(address)  # [lon,lat]
        self.navitia = self.navitia_coverage(self.coord[0], self.coord[1]) # [lon,lat]
        self.near_flag = near
        if near == True:
            self.near_airports = None # TO BE COMPLETED --> [point, point...]
            self.near_train_stations = None # TO BE COMPLETED --> [point, point...]
            self.near_bus_stations = None # TO BE COMPLETED --> [point, point...]

    def to_json(self):
        json =  {
                    'address':self.address,
                    'coord':self.coord,
                    'navitia':self.navitia,
                }
        if self.near_flag == True:
            json['near_airports'] = self.near_airports
            json['near_train_stations'] = self.near_train_stations
            json['near_bus_stations'] = self.near_bus_stations
        return json

    def navitia_coverage(self, lon, lat):
        coverage = navitia_coverage_gpspoint(lon, lat)
        if coverage == False:
            return False

        cov_json = {
            'name':coverage['regions'][0]['id'],
            'polygon':coverage['regions'][0]['shape'],
        }
        return cov_json

    def plot_navitia_coverage(self, center=(48.864716,2.349014), zoom_start = 4,_map=None):
        import folium
        _map = init_map(center, zoom_start) if _map == None else _map

        if self.navitia != False:
            folium.vector_layers.Polygon(locations=self.navitia['polygon'],
                                tooltip=self.navitia['name'],
                                ).add_to(_map)
            folium.map.Marker(location=self.coord[::-1],
                                tooltip=self.address).add_to(_map)
        return _map

"""
BASIC FUNCTIONS
"""


def get_api_keys():
    api_keys = {'ORS_api_key': tmw_api_keys.ORS_api_key,
                'OuiBus_api_key': tmw_api_keys.OuiBus_api_key,
                'SkyScanner_api_key': tmw_api_keys.SkyScanner_api_key,
                'Navitia_api_key': tmw_api_keys.Navitia_api_key
                }
    return api_keys


def init_map(center, zoom_start, tiles = 'Stamen Toner'):
        import folium
        map_params = {'tiles':tiles,
              'location':center,
              'zoom_start': zoom_start}
        _map = folium.Map(**map_params)
        return _map

def geocode_address(address):
    '''
    address: string
    coord : [lon, lat]
    '''
    ORS_client = start_ORS_client()
    lon, lat = ORS_client.pelias_search(address,size=1)['features'][0]['geometry']['coordinates']
    return lon, lat

def point_in_polygon(point, polygon):
    import shapely
    from shapely.geometry import Polygon
    poly = Polygon(((p[0],p[1])for p in polygon))
    return True

#def create_query(start, to, datetime=''):
#    json_query = {
#        'query':{
#            'start':{
#                'address':start,
#                'coord':geocode_address(start),  # [lon,lat]
#            },
#            'to':{
#                'address':to,
#                'coord':geocode_address(to),
#            },
#            'datetime':datetime          # example of format (based on navitia): 20191012T063700
#            } 
#    }
#    return json_query

def get_CO2(travel_type, distance, param={}):
    # Calculate CO2 emissions based on travel_type and distance
    # Import csv database (ADEME)
    # param = {col:value}
    """
    import pandas as pd
    EF_filepath = 'EmissionFactor.csv'
    df_EF = pd.read_csv(EF_filepath,sep=';')
    
    for col in param.keys():
        df_EF = df_EF[df_EF[col] == param[col]]

    print(df_EF)
    print('ERROR get_CO2() --> param variable did not ') if df_EF.size!=1 else True
    EF = df_EF[value]
    """

    dict_EF = {             # Emision factor (EF)
        'walk':0.0,
        'wait':0.0,
        'car':0.255,
        'bus':0.167,
        'metro':0.006,
        'tram':0.006,
        'train':0.037,
        'TGV':0.00369,
        'plane':0.23,
    }
    try:
        EF = dict_EF[travel_type]
    except:
        print('ERROR: travel_type "{}" is not listed in Emission Factor.'.format(travel_type))
        print('Returning 0.0 kgCO2/passenger')
        return 0
    emission = EF * distance
    return emission


"""
Build a multi-modal journey
"""
# WIP WIP WIP
def compute_complete_journey(departure_date = '2019-10-25T09:00:00+0200', geoloc_dep=[48.85,2.35], geoloc_arrival=[43.60,1.44]):
    # First we look for intercities journeys
    trainline_journeys = Trainline.main(departure_date, geoloc_dep, geoloc_arrival)
    skyscanner_journeys = Skyscanner.main(departure_date, geoloc_dep, geoloc_arrival)
    ouibus_journey = OuiBus.main(departure_date, geoloc_dep, geoloc_arrival)
    ors_step = ORS_query_directions(create_query(geoloc_dep, geoloc_arrival, departure_date))

    # Then we call Navitia to get
    return None


"""
OPEN ROUTE SERVICES FUNCTIONS
"""


def start_ORS_client():
    import openrouteservice
    api = get_api_keys()
    ORS_api_key = api['ORS_api_key']
    ORS_client = openrouteservice.Client(key=ORS_api_key) # Specify your personal API key
    return ORS_client


def ORS_profile(profile):
    dict_ORS_profile = {
        "driving-car": "car",
        "driving-hgv": "",
        "foot-walking": "walk",
        "foot-hiking": "walk",
        "cycling-regular": "bike",
        "cycling-road": "bike",
        "cycling-mountain": "bike",
        "cycling-electric": "bike"
        }
    return dict_ORS_profile[profile]

def ORS_query_directions(start, end, profile='driving-car', _id=0, geometry=True):
    '''
    start (class point)
    end (class point)
    profile= ["driving-car", "driving-hgv", "foot-walking","foot-hiking", "cycling-regular", "cycling-road","cycling-mountain",
    "cycling-electric",]
    '''
    ORS_client = start_ORS_client()
    coord = [start.coord, end.coord]
    ORS_step = ORS_client.directions(
        coord,
        profile=profile,
        instructions=False,
        geometry=geometry,
        )
    
    geojson = convert.decode_polyline(ORS_step['routes'][0]['geometry'])

    step = journey_step(_id, 
                        _type=ORS_profile(profile),
                        label=profile, 
                        distance_m=ORS_step['routes'][0]['summary']['distance'], 
                        duration_s=ORS_step['routes'][0]['summary']['duration'],
                        price_EUR=[0],
                        gCO2=0,
                        geojson=geojson,
                        )
    return step


"""
NAVITIA FUNCTIONS
"""


def start_navitia_client():
    from navitia_client import Client
    api = get_api_keys()
    Navitia_api_key = api['Navitia_api_key']
    navitia_client = Client(user=Navitia_api_key)
    return navitia_client

def navitia_query_directions(start, end, _id=0):
    '''
    start (class point)
    end (class point)
    '''
    navitia_client = start_navitia_client()

    if start.navitia['name'] != end.navitia['name']:    # region name (ex: idf-fr)
        print('ERROR: NAVITIA query on 2 different regions')
    
    start_coord = ";".join(map(str, start.coord))
    end_coord = ";".join(map(str, end.coord)) 
    url = 'coverage/{}/journeys?from={}&to={}'.format(start.navitia['name'], start_coord,end_coord)
    url = url + '&data_freshness=base_schedule&max_nb_journeys=3'
    
    step = navitia_client.raw(url, multipage=False)

    return step.json()

def navitia_coverage_global():
    navitia_client = start_navitia_client()
    cov = navitia_client.raw('coverage', multipage=False, page_limit=10, verbose=True)
    coverage = cov.json()
    for i, region in enumerate(coverage['regions']):
        coverage['regions'][i]['shape'] = navitia_geostr_to_polygon(region['shape'])
    return coverage

def navitia_coverage_plot(coverage):
    import folium
    _map = init_map(center=(48.864716,2.349014), zoom_start = 4)
    for zone in coverage['regions']:
        folium.vector_layers.PolyLine(locations=zone['shape'],         # start converage
                            tooltip=zone['name'],
                            smooth_factor=1,
                            ).add_to(_map)
    return _map

def navitia_coverage_gpspoint(lon,lat):   # 
    navitia_client = start_navitia_client()
    cov = navitia_client.raw('coverage/{};{}'.format(lon,lat), multipage=False, page_limit=10, verbose=True)
    coverage = cov.json()
    try:
        for i, region in enumerate(coverage['regions']):
            coverage['regions'][i]['shape'] = navitia_geostr_to_polygon(region['shape'])
    except:
        print('ERROR: AREA NOT COVERED BY NAVITIA (lon:{},lat:{})'.format(lon,lat))
        return False
    return coverage

def navitia_geostr_to_polygon(string):
    import re
    regex = "([-]?\d+\.\d+) ([-]?\d+\.\d+)"
    r = re.findall(regex, string)
    r = [(float(coord[1]), float(coord[0])) for coord in r]    # [ (lat, lon) , (), ()]
    return r

"""
https://doc.navitia.io/#journeys
type = 'waiting' / 'transfer' / 'public_transport' / 'street_network' / 'stay_in' / crow_fly
"""


def navitia_journeys(json, _id=0):
    # all journeys loop
    lst_journeys = list()
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
            i = i+1
        lst_journeys.append(journey(_id, lst_sections))
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
    step = journey_step(_id, 
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
        'walking': 'walk',
        'bike': 'bike',
        'car': 'car',
    }
    label = '{} FROM {} TO {}'.format(
        mode_to_type[mode],
        json['from']['name'],
        json['to']['name'],
    )
    step = journey_step(_id, 
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
        'walking': 'walk',
        'bike': 'bike',
        'car': 'car',
    }
    label = '{} FROM {} TO {}'.format(mode_to_type[mode], json['from']['name'], json['to']['name'])
    step = journey_step(_id, 
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
    step = journey_step(_id, 
                        _type='wait',
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
