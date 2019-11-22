import openrouteservice
from openrouteservice import convert
from app import constants
from app import tmw_api_keys

"""
OPEN ROUTE SERVICES FUNCTIONS
"""


def start_ORS_client():
    ORS_api_key = tmw_api_keys.ORS_API_KEY
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

def ORS_query_directions(query, profile='driving-car', _id=0, geometry=True):
    '''
    start (class point)
    end (class point)
    profile= ["driving-car", "driving-hgv", "foot-walking","foot-hiking", "cycling-regular", "cycling-road","cycling-mountain",
    "cycling-electric",]
    '''
    ORS_client = start_ORS_client()
    coord = [query.start_point, query.end_point]
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

