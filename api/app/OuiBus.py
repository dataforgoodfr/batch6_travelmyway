import requests
import pandas as pd
import json
# from datetime import datetime as dt
import copy
from loguru import logger
from geopy.distance import distance
from app import tmw_api_keys
from app import TMW as tmw
from app import constants
from app.co2_emissions import calculate_co2_emissions

pd.set_option('display.max_columns', 999)
pd.set_option('display.width', 1000)

_STATION_WAITING_PERIOD = constants.WAITING_PERIOD_OUIBUS


def pandas_explode(df, column_to_explode):
    """
    Similar to Hive's EXPLODE function, take a column with iterable elements, and flatten the iterable to one element
    per observation in the output table

    :param df: A dataframe to explod
    :type df: pandas.DataFrame
    :param column_to_explode:
    :type column_to_explode: str
    :return: An exploded data frame
    :rtype: pandas.DataFrame
    """

    # Create a list of new observations
    new_observations = list()

    # Iterate through existing observations
    for row in df.to_dict(orient='records'):

        # Take out the exploding iterable
        explode_values = row[column_to_explode]
        del row[column_to_explode]

        # Create a new observation for every entry in the exploding iterable & add all of the other columns
        for explode_value in explode_values:

            # Deep copy existing observation
            new_observation = copy.deepcopy(row)

            # Add one (newly flattened) value from exploding iterable
            new_observation[column_to_explode] = explode_value

            # Add to the list of new observations
            new_observations.append(new_observation)

    # Create a DataFrame
    return_df = pd.DataFrame(new_observations)

    # Return
    return return_df


# Get all bus stations available for OuiBus / Needs to be updated regularly
def update_stop_list():
    headers = {
        'Authorization': 'Token ' + tmw_api_keys.OUIBUS_API_KEY,
    }
    # Get v1 stops (all actual stops)
    response = requests.get('https://api.idbus.com/v1/stops', headers=headers)
    stops_df_v1 = pd.DataFrame.from_dict(response.json()['stops'])
    # Get v2 stops (with meta_station like "Paris - All stations")
    response = requests.get('https://api.idbus.com/v2/stops', headers=headers)
    stops_df_v2 = pd.DataFrame.from_dict(response.json()['stops'])

    # Enrich stops list with meta gare infos
    stops_rich = pandas_explode(stops_df_v2[['id', 'stops']], 'stops')
    stops_rich['stops'] = stops_rich.apply(lambda x: x.stops['id'], axis=1)
    stops_rich = stops_df_v1.merge(stops_rich, how='left', left_on='id', right_on='stops',
                                   suffixes=('', '_meta_gare'))
    # If no meta gare, the id is used
    stops_rich['id_meta_gare'] = stops_rich.id_meta_gare.combine_first(stops_rich.id)
    stops_rich['geoloc'] = stops_rich.apply(lambda x: [x.latitude, x.longitude], axis=1)

    logger.info(f'{stops_rich.shape[0]} Ouibus stops were found, here is an example:\n {stops_rich.sample()}')
    return stops_rich


# Fonction to call Ouibus API
def search_for_all_fares(date, origin_id, destination_id, passengers):
    headers = {
        'Authorization': 'Token ' + tmw_api_keys.OUIBUS_API_KEY,
        'Content-Type': 'application/json',
    }
    data = {
        "origin_id": origin_id,
        "destination_id": destination_id,
        "date": date,
        "passengers": passengers
    }
    # timestamp = dt.now()
    r = requests.post('https://api.idbus.com/v1/search', headers=headers, data=json.dumps(data))
    # print(dt.now() - timestamp)
    try:
        return pd.DataFrame.from_dict(r.json()['trips'])
    except:
        return None


# Find the stops close to a geo point
def get_stops_from_geo_loc(geoloc_origin, geoloc_destination, max_distance_km=50):
    stops_tmp = _ALL_BUS_STOPS.copy()
    # compute proxi for distance (since we only need to compare no need to take the earth curve into account...)
    stops_tmp['distance_origin'] = stops_tmp.apply(
        lambda x: distance([x.latitude, x.longitude], geoloc_origin).m, axis=1)
    stops_tmp['distance_destination'] = stops_tmp.apply(
        lambda x: distance([x.latitude, x.longitude], geoloc_destination).m, axis=1)
    # We get the 5 closests station (within max_distance_km)
    stations = {}
    stations['origin'] = stops_tmp[stops_tmp.distance_origin < max_distance_km * 1000].sort_values(by='distance_origin').head(5)
    stations['destination'] = stops_tmp[stops_tmp.distance_destination < max_distance_km * 1000].sort_values(by='distance_destination').head(5)
    return stations


def format_ouibus_response(df_response):
    # enrich information
    df_response['nb_segments'] = df_response.apply(lambda x: len(x.legs), axis=1)
    df_response['arrival'] = pd.to_datetime(df_response['arrival'])
    df_response['departure'] = pd.to_datetime(df_response['departure'])
    df_response['duration_total'] = df_response.apply(lambda x: (x.arrival - x.departure).seconds, axis=1)
    response_rich = pandas_explode(df_response, 'legs')
    response_rich['origin_id_seg'] = response_rich.apply(lambda x: x['legs']['origin_id'], axis=1)
    response_rich['destination_id_seg'] = response_rich.apply(lambda x: x['legs']['destination_id'], axis=1)
    response_rich['departure_seg'] = pd.to_datetime(response_rich.apply(lambda x: x['legs']['departure'], axis=1))
    response_rich['arrival_seg'] = pd.to_datetime(response_rich.apply(lambda x: x['legs']['arrival'], axis=1))
    response_rich['bus_number'] = response_rich.apply(lambda x: x['legs']['bus_number'], axis=1)
    response_rich = response_rich.merge(_ALL_BUS_STOPS[['id', 'geoloc', 'short_name']], left_on='origin_id_seg',
                                        right_on='id', suffixes=['', '_origin_seg'])
    response_rich = response_rich.merge(_ALL_BUS_STOPS[['id', 'geoloc', 'short_name']], left_on='destination_id_seg',
                                        right_on='id', suffixes=['', '_destination_seg'])
    # filter only most relevant itineraries (2 cheapest + 2 fastest)
    limit = min(2, response_rich.shape[0])
    response_rich = response_rich.sort_values(by='price_cents').head(limit).append(response_rich.sort_values(by='duration_total').head(limit))

    return response_rich


def compute_trips(date, passengers, geoloc_origin, geoloc_destination):
    """
    Meta Fonction takes a geopoint for departure and arrival,
       1 finds Ouibus status close from departure and arrival
       2 Call API for all meta station of departure and arrival
       3 Returns all available trips
    """
    # Get all stops close to the origin and destination locations
    all_stops = get_stops_from_geo_loc(geoloc_origin, geoloc_destination)
    # Get the meta gare ids to reduce number of request to API
    origin_meta_gare_ids = all_stops['origin'].id_meta_gare.unique()
    destination_meta_gare_ids = all_stops['destination'].id_meta_gare.unique()
    # Call API for all scenarios
    all_trips = pd.DataFrame()
    for origin_meta_gare_id in origin_meta_gare_ids:
        for destination_meta_gare_id in destination_meta_gare_ids:
            logger.info(f'call OuiBus API from {origin_meta_gare_id} to {destination_meta_gare_id}')
            # make sure we don't call the API for a useless trip
            if origin_meta_gare_id != destination_meta_gare_id:
                all_trips = all_trips.append(
                    search_for_all_fares(date, origin_meta_gare_id, destination_meta_gare_id, passengers))

    # Enrich with stops info
    if all_trips.empty:
        logger.info('no trip found from OuiBus')
        return pd.DataFrame()

    all_trips = all_trips.merge(_ALL_BUS_STOPS[['id', 'geoloc', 'short_name']],
                                left_on='origin_id', right_on='id', suffixes=['', '_origin'])
    all_trips = all_trips.merge(_ALL_BUS_STOPS[['id', 'geoloc', 'short_name']],
                                left_on='destination_id', right_on='id', suffixes=['', '_destination'])

    return format_ouibus_response(all_trips[all_trips.available])


def ouibus_journeys(df_response, departure_point, arrival_point, departure_date, _id=0):
    # affect a price to each leg
    df_response['price_step'] = df_response.price_cents / (df_response.nb_segments * 100)
    # Compute distance for each leg
    # print(df_response.columns)
    df_response['distance_step'] = df_response.apply(lambda x: distance(x.geoloc_origin_seg,
                                                                        x.geoloc_destination_seg).m, axis=1)
    lst_journeys = list()
    # all itineraries :
    # logger.info(f'nb itinerary : {df_response.id.nunique()}')
    for itinerary_id in df_response.id.unique():
        itinerary = df_response[df_response.id == itinerary_id].reset_index(drop=True)
        # boolean to know whether and when there will be a transfer after the leg
        itinerary['next_departure'] = itinerary.departure_seg.shift(-1)
        itinerary['next_stop_name'] = itinerary.short_name_origin_seg.shift(1)
        itinerary['next_geoloc'] = itinerary.geoloc_origin_seg.shift(-1)
        i = _id
        lst_sections = list()
        # We add a waiting period at the station of 15 minutes
        step = tmw.journey_step(i,
                                _type=constants.TYPE_WAIT,
                                label='',
                                distance_m=0,
                                duration_s=_STATION_WAITING_PERIOD,
                                price_EUR=[0],
                                gCO2=0,
                                departure_point=itinerary.geoloc.iloc[0],
                                arrival_point=itinerary.geoloc.iloc[0],
                                geojson=[],
                                )
        lst_sections.append(step)
        i = i + 1
        for index, leg in itinerary.iterrows():
            local_distance_m = leg.distance_step
            local_emissions = calculate_co2_emissions(constants.TYPE_COACH, constants.DEFAULT_CITY,
                                                      constants.DEFAULT_FUEL, constants.DEFAULT_NB_SEATS,
                                                      constants.DEFAULT_NB_KM) *\
                              constants.DEFAULT_NB_PASSENGERS*local_distance_m
            step = tmw.journey_step(i,
                                    _type=constants.TYPE_COACH,
                                    label='',
                                    distance_m=local_distance_m,
                                    duration_s=(leg.arrival_seg - leg.departure_seg).seconds,
                                    price_EUR=[leg.price_step],
                                    gCO2=local_emissions,
                                    departure_point=leg.geoloc_origin_seg,
                                    arrival_point=leg.geoloc_destination_seg,
                                    departure_stop_name=leg.short_name_origin_seg,
                                    arrival_stop_name=leg.short_name_destination_seg,
                                    departure_date=leg.departure_seg,
                                    arrival_date=leg.arrival_seg,
                                    trip_code='OuiBus ' + leg.bus_number,
                                    geojson=[],
                                    )
            lst_sections.append(step)
            i = i + 1
            # add transfer steps
            if not pd.isna(leg.next_departure):
                step = tmw.journey_step(i,
                                        _type=constants.TYPE_TRANSFER,
                                        label='',
                                        distance_m=distance(leg.geoloc_destination_seg, leg.next_geoloc).m,
                                        duration_s=(leg['next_departure'] - leg['arrival_seg']).seconds,
                                        price_EUR=[0],
                                        departure_point=leg.geoloc_destination_seg,
                                        arrival_point=leg.next_geoloc,
                                        departure_stop_name=leg.short_name_destination_seg,
                                        arrival_stop_name=leg.next_stop_name,
                                        gCO2=0,
                                        geojson=[],
                                        )
                lst_sections.append(step)
                i = i + 1

        journey_ouibus = tmw.journey(_id, departure_point, arrival_point, departure_date, steps=lst_sections)
        # Add category
        category_journey = list()
        for step in journey_ouibus.steps:
            if step.type not in [constants.TYPE_TRANSFER, constants.TYPE_WAIT]:
                category_journey.append(step.type)

        journey_ouibus.category = list(set(category_journey))
        lst_journeys.append(journey_ouibus)

        # for journey in lst_journeys:
        #    journey.update()

    return lst_journeys


def main(query):
    all_trips = compute_trips(query.departure_date, _PASSENGER, query.start_point, query.end_point)

    if all_trips.empty:
        return None
    else:
        return ouibus_journeys(all_trips, query.start_point, query.end_point, query.departure_date)


_ALL_BUS_STOPS = update_stop_list()
_PASSENGER = [{"id": 1,  "age": 30,  "price_currency": "EUR"}]

if __name__ == '__main__':
    main()


