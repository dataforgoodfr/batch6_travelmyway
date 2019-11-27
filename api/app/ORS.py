import openrouteservice
from openrouteservice import convert
from app import constants
from app import tmw_api_keys
from datetime import timedelta
from app import TMW as tmw
from app import co2_emissions

"""
OPEN ROUTE SERVICES FUNCTIONS
"""


def start_ORS_client():
    ORS_api_key = tmw_api_keys.ORS_API_KEY
    ORS_client = openrouteservice.Client(key=ORS_api_key) # Specify your personal API key
    return ORS_client


def ORS_profile(profile): # Should be integrated into CONSTANTS.py
    dict_ORS_profile = {
        "driving-car": constants.TYPE_CAR,
        "driving-hgv": "",
        "foot-walking": "walk",
        "foot-hiking": "walk",
        "cycling-regular": "bike",
        "cycling-road": "bike",
        "cycling-mountain": "bike",
        "cycling-electric": "bike"
    }
    return dict_ORS_profile[profile]

def ORS_query_directions(query, profile='driving-car', toll_price=True, _id=0, geometry=True):
    '''
    start (class point)
    end (class point)
    profile= ["driving-car", "driving-hgv", "foot-walking","foot-hiking", "cycling-regular", "cycling-road","cycling-mountain",
    "cycling-electric",]
    '''
    ORS_client = start_ORS_client()
    coord = [query.start_point[::-1], query.end_point[::-1]]   # WARNING it seems that [lon,lat] are not in the same order than for other API.
    ORS_step = ORS_client.directions(
        coord,
        profile=profile,
        instructions=False,
        geometry=geometry,
    )

    geojson = convert.decode_polyline(ORS_step['routes'][0]['geometry'])

    local_distance = ORS_step['routes'][0]['summary']['distance']
    local_emissions = co2_emissions.calculate_co2_emissions(constants.TYPE_COACH, constants.DEFAULT_CITY,
                                              constants.DEFAULT_FUEL, constants.DEFAULT_NB_SEATS,
                                              constants.DEFAULT_NB_KM) * \
                      constants.DEFAULT_NB_PASSENGERS * local_distance

    step = tmw.journey_step(_id,
                        _type=ORS_profile(profile),
                        label=profile,
                        distance_m=local_distance,
                        duration_s=ORS_step['routes'][0]['summary']['duration'],
                        price_EUR=[ORS_gas_price(ORS_step['routes'][0]['summary']['distance'])],
                        gCO2=local_emissions,
                        geojson=geojson,
                        )
    # Correct arrival_date based on departure_date
    step.arrival_date = (step.departure_date + timedelta(seconds=step.duration_s))

    # Add toll price (optional)
    step = ORS_add_toll_price(step) if toll_price else step

    ors_journey = tmw.journey(0, steps=[step])
    # Add category
    category_journey = list()
    for step in ors_journey.steps:
        if step.type not in [constants.TYPE_TRANSFER, constants.TYPE_WAIT]:
            category_journey.append(step.type)

    ors_journey.category = list(set(category_journey))

    return ors_journey.update()

def ORS_gas_price(distance_m, gas_price_EUR=1.5, car_consumption=0.0664):
    distance_km = distance_m / 1000
    price_EUR = gas_price_EUR * (car_consumption * distance_km)
    return price_EUR

def ORS_add_toll_price(step, toll_priceEUR_per_km=0.025):
    distance_km = step.distance_m / 1000
    price_EUR = distance_km * toll_priceEUR_per_km
    step.price_EUR.append(price_EUR)
    return step