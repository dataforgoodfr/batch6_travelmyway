import requests
from loguru import logger
import pandas as pd
import copy
import zipfile
import os
import io
from humanfriendly import format_timespan
from time import perf_counter
from app import TMW as tmw
from datetime import datetime as dt, timedelta
from geopy.distance import distance
from app import tmw_api_keys
import time
from app import constants
from app.co2_emissions import calculate_co2_emissions

pd.set_option('display.max_columns', 999)
pd.set_option('display.width', 1000)

# Define the (arbitrary waiting period at the airport
_AIRPORT_WAITING_PERIOD = constants.WAITING_PERIOD_AIRPORT



def load_airport_database():
    """
    Load the airport database used to do smart calls to Skyscanner API.
    This DB can be reconstructed thanks to the recompute_airport_database (see end of file)
    """
    path = os.path.join(os.getcwd(), 'skyscanner_europe_airport_list.csv')  #
    try:
        logger.info(path)
        airport_list = pd.read_csv(path)
        airport_list['geoloc'] = airport_list.apply(lambda x: [x.latitude, x.longitude], axis=1)
        logger.info('load the skyscanner airport db. Here is a random example :')
        logger.info(airport_list.sample(1))
        return airport_list
    except:
        try:
            logger.info(os.path.join(os.getcwd(), 'api/app/', 'data/skyscanner_europe_airport_list.csv'))
            airport_list = pd.read_csv(os.path.join(os.getcwd(), 'api/app/', 'data/skyscanner_europe_airport_list.csv'), sep=',')
            airport_list['geoloc'] = airport_list.apply(lambda x: [x.latitude, x.longitude], axis=1)
            logger.info('load the skyscanner airport db. Here is a random example :')
            logger.info(airport_list.sample(1))
            return airport_list
        except:
            logger.info(os.path.join(os.getcwd(), 'app/', 'data/skyscanner_europe_airport_list.csv'))
            airport_list = pd.read_csv(os.path.join(os.getcwd(), 'app/', 'data/skyscanner_europe_airport_list.csv'))
            airport_list['geoloc'] = airport_list.apply(lambda x: [x.latitude, x.longitude], axis=1)
            logger.info('load the skyscanner airport db. Here is a random example :')
            logger.info(airport_list.sample(1))
            return airport_list

# When the server starts it logs the airport db (only once)
_AIRPORT_DF = load_airport_database()


def skyscanner_query_directions(query, plane_jouney_found=True):
    """
    This function takes an object query and returns a list of journey object thanks to the Skyscanner API
    """
    # extract departure and arrival points
    logger.info(query['query']['start']['coord'])
    # departure_points = ';'.join(query['query']['start']['coord'])
    # arrival_points = ';'.join(query['query']['to']['coord'])
    departure_point = query['query']['start']['coord']
    arrival_point = query['query']['to']['coord']
    # extract departure date as 'yyyy-mm-dd'
    date_departure = query['query']['datetime']
    df_response = get_planes_from_skyscanner(date_departure, None, departure_point, arrival_point, plane_jouney_found, details=True)
    if df_response is None or df_response.empty:
        print('on a rien trouve comme avion')
        return list()
    else:
        return skyscanner_journeys(df_response)


def skyscanner_journeys(df_response, _id=0):
    """
    This function takes in a dataframe with detailled information on the plane journeys returned by Skyscanner API
        and returns a list containing one TMW journey object for each of those plane journey
    """
    # affect a price to each leg
    df_response['price_step'] = df_response.PriceTotal_AR / df_response.nb_segments
    df_response['DepartureDateTime'] = pd.to_datetime(df_response['DepartureDateTime'])
    df_response['ArrivalDateTime'] = pd.to_datetime(df_response['ArrivalDateTime'])
    # Compute distance for each leg
    df_response['distance_step'] = df_response.apply(lambda x: distance(x.geoloc_origin_seg,
                                                                        x.geoloc_destination_seg).m, axis=1)
    print(df_response.itinerary_id.nunique())
    lst_journeys = list()
    # all itineraries :
    for itinerary_id in df_response.itinerary_id.unique():
        itinerary = df_response[df_response.itinerary_id == itinerary_id].reset_index(drop=True)
        i = _id
        # boolean to know whether and when there will be a transfer after the leg
        itinerary['next_departure'] = itinerary.DepartureDateTime.shift(-1)
        itinerary['next_stop_name'] = itinerary.Name_origin_seg.shift(-1)
        itinerary['next_geoloc'] = itinerary.geoloc_origin_seg.shift(-1)
        lst_sections = list()
        # We add a waiting period at the airport of 2 hours
        step = tmw.journey_step(i,
                                _type=constants.TYPE_WAIT,
                                label=f'Arrive at the airport {format_timespan(_AIRPORT_WAITING_PERIOD)} before departure',
                                distance_m=0,
                                duration_s=_AIRPORT_WAITING_PERIOD,
                                price_EUR=[0],
                                gCO2=0,
                                departure_point=itinerary.geoloc.iloc[0],
                                arrival_point=itinerary.geoloc.iloc[0],
                                departure_date=itinerary.DepartureDateTime[0] - timedelta(seconds=_AIRPORT_WAITING_PERIOD),
                                arrival_date=itinerary.DepartureDateTime[0],
                                geojson=[],
                                )
        lst_sections.append(step)
        i = i + 1
        for index, leg in itinerary.sort_values(by='DepartureDateTime').iterrows():
            local_distance_m = leg.distance_step
            local_range_km = get_range_km(local_distance_m)
            local_emissions = calculate_co2_emissions(constants.TYPE_PLANE, constants.DEFAULT_CITY,
                                                      constants.DEFAULT_FUEL, constants.NB_SEATS_TEST,
                                                      local_range_km) * \
                              constants.DEFAULT_NB_PASSENGERS * local_distance_m

            step = tmw.journey_step(i,
                                    _type=constants.TYPE_PLANE,
                                    label=f'Flight {leg.FlightNumber_rich} to {leg.Name}',
                                    distance_m=leg.distance_step,
                                    duration_s=leg.Duration_seg * 60,
                                    price_EUR=[leg.price_step],
                                    gCO2=local_emissions,
                                    departure_point = leg.geoloc_origin_seg,
                                    arrival_point = leg.geoloc_destination_seg,
                                    departure_stop_name=leg.Name_origin_seg,
                                    arrival_stop_name=leg.Name,
                                    departure_date=leg.DepartureDateTime,
                                    arrival_date=leg.ArrivalDateTime,
                                    trip_code=leg.FlightNumber_rich,
                                    geojson=[],
                                    )
            lst_sections.append(step)
            i = i+1
            # add transfer steps
            if not pd.isna(leg.next_departure):
                #duration = dt.strptime(leg['next_departure'], '%Y-%m-%dT%H:%M:%S') - \
                #           dt.strptime(leg['ArrivalDateTime'], '%Y-%m-%dT%H:%M:%S')
                step = tmw.journey_step(i,
                                        _type=constants.TYPE_TRANSFER,
                                        label=f'Transfer at {leg.Name}',
                                        distance_m=0,
                                        duration_s=(leg.next_departure - leg.ArrivalDateTime).seconds,
                                        price_EUR=[0],
                                        departure_point=leg.geoloc_destination_seg,
                                        arrival_point=leg.next_geoloc,
                                        departure_date=leg.ArrivalDateTime,
                                        arrival_date=leg.next_departure,
                                        departure_stop_name=leg.Name,
                                        arrival_stop_name=leg.next_stop_name,
                                        gCO2=0,
                                        geojson=[],
                                        )
                lst_sections.append(step)
                i = i+1

        journey_sky = tmw.journey(_id, steps=lst_sections,
                                    departure_date= lst_sections[0].departure_date,
                                    arrival_date= lst_sections[-1].arrival_date)
        # journey_sky = tmw.journey(_id, steps=lst_sections)
        # Add category
        category_journey = list()
        for step in journey_sky.steps:
            if step.type not in [constants.TYPE_TRANSFER, constants.TYPE_WAIT]:
                category_journey.append(step.type)

        journey_sky.category = list(set(category_journey))
        lst_journeys.append(journey_sky)

        for journey in lst_journeys:
            journey.update()

    return lst_journeys


def get_price_from_itineraries(x):
    # there is a possibility of having multiple price options, if that's the case let's return the min price
    if len(x.PricingOptions) == 1:
        return x.PricingOptions[0]['Price']
    else:
        # get minimum price
        prices = []
        for price_option in x.PricingOptions:
            prices.append(price_option['Price'])
        return min(prices)


def get_planes_from_skyscanner(date_departure, date_return, departure, arrival, plane_jouney_found=True, details=False, try_number=1):
    """
    Here we actually call the Skyscanner API with all the relevant information asked by the user
    First we create a session with the first POST request, then we read the results with the 2nd GET request
    For each of the calls we try to deal with all the potential errors the API could return, most importantly
        we want to wait and try again if the API says it's too busy right now
    """
    # format date as yyy-mm-dd
    date_formated = str(date_departure)[0:10]
    url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/pricing/v1.0"
    logger.info(f'get_planes try nb {try_number}')
    one_way = date_return is None
    # If another call to Skyscanner has already been successful, we don't want to waste too much time
    # so we decrease the max number of retries
    if plane_jouney_found:
        max_retries = 2
    else :
        max_retries = 5
    if one_way:
        payload = f'cabinClass=economy&children=0&infants=0&country=FR&currency=EUR&locale=en-US&originPlace={departure}&destinationPlace={arrival}&outboundDate={date_formated}&adults=1'
    else:
        payload = f'inboundDate={date_return}&cabinClass=economy&children=0&infants=0&country=FR&currency=USD&locale=en-US&originPlace={departure}&destinationPlace={arrival}&outboundDate={date_departure}&adults=1'

    headers = {
        'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        'x-rapidapi-key': tmw_api_keys.SKYSCANNER_API_KEY,
        'content-type': "application/x-www-form-urlencoded"
    }
    # First POST request to create session
    response = requests.request("POST", url, data=payload, headers=headers)
    # get session key
    # In some cases the API won't give a session key "Location" so we try and except
    try:
        # print(response.headers)
        key = response.headers['Location'].split('/')[-1]
    except :
        # Retry calling API 3 times
        try:
            # Let's look at the error from the API
            error = response.json()['ValidationErrors']
            logger.warning(error)
            # When the API says it's too busy, if we haven't past the max number of retires
            if (error[0]['Message'] == 'Rate limit has been exceeded: 400 PerMinute for PricingSession')&(try_number < max_retries):
                time.sleep(1)
                logger.info(f'we try our luck for chance {try_number + 1} out of 3 with Skyscanner')
                # We call this same function again with the try_number increased by one
                return get_planes_from_skyscanner(date_departure, date_return, departure, arrival,
                                           details=True, try_number=try_number + 1)
            else:
                # we couldn't find any trips through the API so we return an empty DF
                logger.info(f'out because {error}')
                return pd.DataFrame()
        except:
            # If the API said we called too much, we wait a little bit more and try again (YOLO)
            if (response.status_code == 429) & (try_number < max_retries):
                time.sleep(1.5)
                # We call this same function again with the try_number increased by one
                return get_planes_from_skyscanner(date_departure, date_return, departure, arrival,
                                                  details=True, try_number=try_number+1)

            # Otherwise we return an empty DF
            logger.warning('The Skyscanner API returned an unknown error')
            return pd.DataFrame()

    # Now we construct the 2nd request to extract the results from the session we just created
    url = 'https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/pricing/uk2/v1.0/' + key
    # We only take the first page, 100 first results
    querystring = {"pageIndex": "0", "pageSize": "100"}

    headers = {
        'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        'x-rapidapi-key': tmw_api_keys.SKYSCANNER_API_KEY
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    logger.info(response.status_code)
    # logger.info(response.content)
    waiting_start_time = perf_counter()
    waiting_time = perf_counter()
    try:
        # When the API says it's too busy, or if the response is not complete yet we send the request again
        # However we don't exceed the max number of retry and we don't wait for more than 5 sec
        #   for the response to be completed
        while ((response.status_code == 429) or (response.json()['Status'] != 'UpdatesComplete')) &\
                (waiting_time-waiting_start_time < 5):
            response = requests.request("GET", url, headers=headers, params=querystring)
            if response.status_code == 429:
                time.sleep(1)
            waiting_time = perf_counter()
    except:
        if response.status_code == 429:
            logger.info('weirdosse')
        if response.status_code == 200:
            # Should not happen
            logger.info('out because chai po')
            logger.info(response.json()['Status'])
            logger.info(response.json()['Legs'])
        return pd.DataFrame()

    try :
        # When the response actually contains something we call the fromat fonction to
        #    regroup all the necessary infos
        if len(response.json()['Legs']) > 0:
            return format_skyscanner_response(response.json(), date_departure, one_way, details)
        else :
            # The API could not find any trips
            logger.info('out because no legs. Looked like this though')
            logger.info(response.json())
            return pd.DataFrame()
    except:
        # Should not happen
        return pd.DataFrame()


def format_skyscanner_response(rep_json, date_departure, one_way=False, segment_details=True, only_with_price=True):
    """
    Format complicated json with information flighing around into a clear dataframe
    See Skyscanner API doc for more info https://skyscanner.github.io/slate/?_ga=1.104705984.172843296.1446781555#polling-the-results
    """
    logger.info('into format planes')
    # get legs (aggregated outbound or inbound trip)
    legs = pd.DataFrame.from_dict(rep_json['Legs'])
    # get itineraries (vector of 2 legs with the total price and price info)
    itineraries = pd.DataFrame.from_dict(rep_json['Itineraries'])
    # reset_index to get an unique id for each itinerary
    itineraries.reset_index(inplace=True)
    itineraries = itineraries.rename(columns={'index': 'itinerary_id'})

    legs['nb_segments'] = legs.apply(lambda x: len(x['SegmentIds']), axis=1)
    # get a single price for each itinary (might have more than 1)
    itineraries['PriceTotal_AR'] = itineraries.apply(get_price_from_itineraries, axis=1)

    # get places (airport codes)
    places = pd.DataFrame.from_dict(rep_json['Places'])
    places = places.merge(_AIRPORT_DF[['Code', 'geoloc']], on='Code')
    # print(f'we got {places.shape[0]} places')
    # We merge to get price for both the inbound and outbound legs
    legs = legs.merge(itineraries[['itinerary_id', 'OutboundLegId', 'PriceTotal_AR']], how='left', left_on='Id',
                      right_on='OutboundLegId', suffixes=['', '_out'])

    if not one_way:
        legs = legs.merge(itineraries[['itinerary_id', 'InboundLegId', 'PriceTotal_AR']], how='left',
                          left_on='Id', right_on='InboundLegId', suffixes=['', '_in'])
    # Filter out legs where there is no itinerary associated (so no price)
    if only_with_price & one_way:
        legs = legs[(legs.Id.isin(itineraries.OutboundLegId.unique()))]
    elif only_with_price:
        legs = legs[
            (legs.Id.isin(itineraries.OutboundLegId.unique())) | (legs.Id.isin(itineraries.InboundLegId.unique()))]

    # filter according to departure time
    legs['Departure'] = pd.to_datetime(legs.Departure)
    legs = legs[legs.Departure >= date_departure]
    # filter only most relevant itineraries (2 cheapest + 2 fastest + 2 soonest)
    limit = min(3, legs.shape[0])
    legs = legs.sort_values(by='PriceTotal_AR').head(limit).append(legs.sort_values(by='Duration').head(limit))\
        .append(legs.sort_values(by='Departure').head(limit))

    # We merge to get both the premiere departure airport and the final airport
    legs = legs.merge(places[['Id', 'Code', 'geoloc']], left_on='OriginStation', right_on='Id',
                      suffixes=['', '_origin'])
    legs = legs.merge(places[['Id', 'Code', 'geoloc']], left_on='DestinationStation', right_on='Id',
                      suffixes=['', '_destination'])

    if not one_way:
        # Reunite the price and the index in the same column for inbound and outbound
        legs['PriceTotal_AR'] = legs.PriceTotal_AR.combine_first(legs.PriceTotal_AR_in)
        legs['itinerary_id'] = legs['itinerary_id'].combine_first(legs.itinerary_id_in)

    # If no details asked we stay at leg granularity
    if not segment_details:
        return legs[
            ['itinerary_id', 'Directionality', 'Id', 'Arrival', 'Departure', 'Duration', 'JourneyMode', 'SegmentIds',
             'nb_segments', 'PriceTotal_AR', 'Code', 'geoloc', 'Code_destination',
             'geoloc_destination']].sort_values(by=['itinerary_id', 'Id'])
    # else we break it down to each segment
    else:
        # get segments (each unique actual flight)
        segments = pd.DataFrame.from_dict(rep_json['Segments'])
        # get carriers (flight companies)
        carriers = pd.DataFrame.from_dict(rep_json['Carriers'])
        # Explode the list of segment associated to each leg to have one line per segment
        segments_rich = pandas_explode(legs, 'SegmentIds')

        # Add relevant segment info to the exploded df (already containing all the leg and itinary infos)
        segments_rich = segments_rich.merge(segments, left_on='SegmentIds', right_on='Id',
                                            suffixes=['_global', '_seg'])
        segments_rich = segments_rich.merge(places[['Id', 'Code', 'Type', 'Name', 'geoloc']],
                                            left_on='DestinationStation_seg', right_on='Id',
                                            suffixes=['', '_destination_seg'])
        segments_rich = segments_rich.merge(places[['Id', 'Code', 'Type', 'Name', 'geoloc']],
                                            left_on='OriginStation_seg', right_on='Id',
                                            suffixes=['', '_origin_seg'])
        segments_rich = segments_rich.merge(carriers[['Id', 'Code']], left_on='Carrier', right_on='Id',
                                            suffixes=['', '_carrier'])

        # Recreate the usual Flight number (like AF10 for CDG to JFK)
        segments_rich['FlightNumber_rich'] = segments_rich['Code_carrier'] + segments_rich['FlightNumber']
        # Recreate the order of the segment (not working so far)
        # segments_rich['seg_rank'] = segments_rich.groupby('Id_global')["value"].rank("dense", ascending=False)
        # keep only the relevant information
        return segments_rich[
            ['itinerary_id', 'Arrival', 'Departure', 'Code', 'geoloc', 'Code_destination',
             'geoloc_destination', 'Duration_global',
             'Id_global', 'PriceTotal_AR', 'nb_segments', 'ArrivalDateTime', 'DepartureDateTime',
             'Duration_seg', 'JourneyMode_seg', 'Name_origin_seg', 'Name',
             'Id', 'Id_seg', 'Code_origin_seg', 'geoloc_origin_seg', 'Code_destination_seg', 'geoloc_destination_seg',
             'FlightNumber_rich']].drop_duplicates(subset=['Id_seg', 'itinerary_id']).sort_values(by=['itinerary_id', 'DepartureDateTime'], ascending=[True,True])


# Custom function to handle DF
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


# Find the stops close to a geo point
def get_airports_from_geo_locs(geoloc_dep, geoloc_arrival):
    """
    This function takes in the departure and arrival points of the TMW journey and returns
        the most relevant corresponding Skyscanner cities to build a plane journey
    We first look at the closest airport, if the city is big enough we keep only one city,
        if not we add the next closest airport and if this 2nd city is big enough we keep only the two first
        else we look at the 3rd and final airports
    """
    stops_tmp = _AIRPORT_DF.copy()
    # compute proxi for distance (since we only need to compare no need to take the earth curve into account...)
    stops_tmp['distance_dep'] = stops_tmp.apply(lambda x: distance(geoloc_dep, x.geoloc).m, axis=1)
    stops_tmp['distance_arrival'] = stops_tmp.apply(lambda x: distance(geoloc_arrival, x.geoloc).m, axis=1)

    # We get the 2 closest airports for departure and arrival + 1 one if they are small
    airport_list = dict()
    tmp_close_airports = stops_tmp.sort_values(by='distance_dep').head(1)
    if tmp_close_airports[tmp_close_airports.bigger_city].shape[0] == 0:
        tmp_close_airports = stops_tmp.sort_values(by='distance_dep').head(2)
        if tmp_close_airports[tmp_close_airports.bigger_city].shape[0] == 0:
            tmp_close_airports = stops_tmp.sort_values(by='distance_dep').head(3)
    airport_list['departure'] = tmp_close_airports.city_sky.unique()
    tmp_close_airports = stops_tmp.sort_values(by='distance_arrival').head(1)
    if tmp_close_airports[tmp_close_airports.bigger_city].shape[0]==0:
        tmp_close_airports = stops_tmp.sort_values(by='distance_arrival').head(2)
        if tmp_close_airports[tmp_close_airports.bigger_city].shape[0] == 0:
            tmp_close_airports = stops_tmp.sort_values(by='distance_arrival').head(3)
    airport_list['arrival'] = tmp_close_airports.city_sky.unique()
    logger.info(f'airports {airport_list}')
    return airport_list


def get_range_km(local_distance_m):
    thousands_km_min = int(local_distance_m/1e6)
    if thousands_km_min == 0:
        range_km = ('0', '1000')
    else:
        thousands_km_max = thousands_km_min + 1
        range_km = (str(thousands_km_min) + '000', str(thousands_km_max) + '000')
    return range_km


def main(query):
    """
    This is a the function called from app/main.py. It takes a query object and returns a list of journey objects
    First we find which skyscanner cities to call, then we call the API and format the response into a list of journey objects
    """
    airports = get_airports_from_geo_locs(query.start_point, query.end_point)
    all_responses = list()
    some_journey_found = False
    # Let's call the API for every couple cities departure and arrival
    for airport_dep in airports['departure']:
        for airport_arrival in airports['arrival']:
            logger.info(f'call Skyscanner from {airport_dep} to {airport_arrival}')
            json_query = {
                'query': {
                    'start': {
                        'coord': airport_dep,
                    },
                    'to': {
                        'coord': airport_arrival,
                    },
                    'datetime': query.departure_date
                    }
            }
            single_route = skyscanner_query_directions(json_query, some_journey_found)
            if single_route is not None:
                some_journey_found = True
                for trip in single_route:
                    all_responses.append(trip)

    all_reponses_json = list()
    for journey_sky in all_responses:
        all_reponses_json.append(journey_sky.to_json())

    return all_responses


################# Recompute airport database (not run each time) ##############################@
def recompute_airport_database():
    airport_list_world = download_airport_database()
    # Keep relevant europe airports
    europe_countries = ['FRANCE', 'SPAIN', 'BELGIUM', 'GERMANY', 'ITALY', 'LUXEMBOURG', 'NORWAY', 'SWEDEN',
                        'DENMARK', 'ENGLAND', 'IRELAND', 'SCOTLAND', 'SWITZERLAND', 'FINLAND', 'SLOVENIA',
                        'AUSTRIA', 'POLAND', 'NETHERLANDS', 'PORTUGAL', 'CZECHIA', 'HUNGARY']

    europe_airports = airport_list_world[airport_list_world.Country.isin(europe_countries)]
    europe_airports = europe_airports[~pd.isna(europe_airports.Code)]
    europe_airports['city_sky'] = europe_airports.apply(return_city, axis=1)
    # to be completed manually
    europe_airports['bigger_city'] = False
    europe_airports_final = europe_airports[europe_airports.city_sky != 'not found']
    europe_airports_final.to_csv('skyscanner_europe_airport_list.csv', index=False)
    return True


def get_place_from_airport(air_code):
    url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/autosuggest/v1.0/UK/GBP/en-GB/"

    querystring = {"query": air_code, "pageIndex": "1", "pageSize": "100"}

    headers = {
        'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        'x-rapidapi-key': "c8568b20bdmsha7927470ad4afdbp13559djsn5c9a0c383cc2"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    tmp = pd.DataFrame.from_dict(response.json()['Places'])

    return tmp


def return_city(x):
    tmp = get_place_from_airport(x.Code)
    print(x.Code)
    ff = tmp[tmp.PlaceId == x.Code + '-sky']
    if not ff.empty:
        # print(';n')
        return ff.CityId.get_values()[0]
    else:
        return 'not found'


def download_airport_database():
    # Create an Airport Database to link a airport code to it's location
    # get airport db from http://www.partow.net/downloads/GlobalAirportDatabase.zip
    r = requests.get('http://www.partow.net/downloads/GlobalAirportDatabase.zip')
    csv_buffer = io.BytesIO(r.content)
    z = zipfile.ZipFile(csv_buffer)
    with z:
        with z.open("GlobalAirportDatabase.txt") as f:
            airports = pd.read_csv(f, header=None, sep=':')

    airports = airports.rename(columns={1: 'Code', 2: 'AirportName', 3: 'City', 4: 'Country', 14: 'latitude',
                                        15: 'longitude'})
    airports = airports[['Code', 'AirportName', 'City', 'Country', 'latitude', 'longitude']]
    # Filter airports with no Code (not very useful)
    airports = airports[~pd.isna(airports.Code)]
    airports['geoloc'] = airports.apply(lambda x: [x.latitude,x.longitude], axis=1)
    airports['Code_sky'] = airports.apply(lambda x: x.Code + '-sky', axis=1)

    logger.info(f'found {airports.shape[0]} airports, here is an example: \n {airports[airports.latitude!=0.0].sample()} ')
    return airports


if __name__ == '__main__':
    main()
