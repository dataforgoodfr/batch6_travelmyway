import requests
from loguru import logger
import pandas as pd
import copy
import zipfile
import io
from app import TMW as tmw
from datetime import datetime as dt
from geopy.distance import distance
from app import tmw_api_keys
import time
from app import constants
from app.co2_emissions import calculate_co2_emissions

pd.set_option('display.max_columns', 999)
pd.set_option('display.width', 1000)

# Define the (arbitrary waiting period at the airport
_AIRPORT_WAITING_PERIOD = 7200


def create_airport_database():
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


_AIRPORT_DF = create_airport_database()


def skyscanner_query_directions(query):
    # extract departure and arrival points
    logger.info(query['query']['start']['coord'])
    # departure_points = ';'.join(query['query']['start']['coord'])
    # arrival_points = ';'.join(query['query']['to']['coord'])
    departure_point = query['query']['start']['coord']
    arrival_point = query['query']['to']['coord']
    # extract departure date
    date_departure = query['query']['datetime']
    df_response = get_planes_from_skyscanner(date_departure, None, departure_point, arrival_point, details=True)
    if df_response.empty:
        return list()
    else:
        return skyscanner_journeys(df_response)


def skyscanner_journeys(df_response, _id=0):
    # affect a price to each leg
    df_response['price_step'] = df_response.PriceTotal_AR / df_response.nb_segments
    # Compute distance for each leg
    df_response['distance_step'] = df_response.apply(lambda x: distance(x.geoloc_origin_seg,
                                                                        x.geoloc_destination_seg).m, axis=1)
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
                                label='',
                                distance_m=0,
                                duration_s=_AIRPORT_WAITING_PERIOD,
                                price_EUR=[0],
                                gCO2=0,
                                departure_point=itinerary.geoloc.iloc[0],
                                arrival_point=itinerary.geoloc.iloc[0],
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
                                    label='',
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
                duration = dt.strptime(leg['next_departure'], '%Y-%m-%dT%H:%M:%S') - \
                           dt.strptime(leg['ArrivalDateTime'], '%Y-%m-%dT%H:%M:%S')
                step = tmw.journey_step(i,
                                        _type=constants.TYPE_TRANSFER,
                                        label='',
                                        distance_m=0,
                                        duration_s=duration.seconds,
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

        journey_sky = tmw.journey(_id, steps=lst_sections)
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


def get_planes_from_skyscanner(date_departure, date_return, departure, arrival, details=False, try_number=1):
    url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/pricing/v1.0"
    one_way = date_return is None
    if one_way:
        payload = f'cabinClass=economy&children=0&infants=0&country=FR&currency=EUR&locale=en-US&originPlace={departure}&destinationPlace={arrival}&outboundDate={date_departure}&adults=1'
    else:
        payload = f'inboundDate={date_return}&cabinClass=economy&children=0&infants=0&country=FR&currency=USD&locale=en-US&originPlace={departure}&destinationPlace={arrival}&outboundDate={date_departure}&adults=1'

    headers = {
        'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        'x-rapidapi-key': tmw_api_keys.SKYSCANNER_API_KEY,
        'content-type': "application/x-www-form-urlencoded"
    }
    # create session
    # print(f'request session for {departure} to {arrival}')
    response = requests.request("POST", url, data=payload, headers=headers)
    # get session key
    try:
        # print(response.headers)
        key = response.headers['Location'].split('/')[-1]
    except KeyError:
        # Retry calling API 3 times
        try:
            # Is there an error with the query ?
            error = response.json()['ValidationErrors']
            logger.warning(error)
            return pd.DataFrame()
        except KeyError:
            if try_number < 3:
                time.sleep(2)
                get_planes_from_skyscanner(date_departure, date_return, departure, arrival,
                                           details=False, try_number=try_number+1)
            else :
                raise KeyError('The API did not allow for session creation 3 times in a row')
    url = 'https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/pricing/uk2/v1.0/' + key
    querystring = {"pageIndex": "0", "pageSize": "100"}

    headers = {
        'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        'x-rapidapi-key': tmw_api_keys.SKYSCANNER_API_KEY
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    logger.info(response.status_code)
    # logger.info(response.content)
    while response.json()['Status'] != 'UpdatesComplete':
        response = requests.request("GET", url, headers=headers, params=querystring)
    # print('le statut de la reponse est ' + response.json()['Status'])
    if len(response.json()['Legs']) > 0:
        return format_skyscanner_response(response.json(), one_way, details)
    else :
        # print(f'no flight found lets move on {response}')
        return pd.DataFrame()


def format_skyscanner_response(rep_json, one_way=False, segment_details=True, only_with_price=True):
    """
    Format complicated json with information flighing around into a clear dataframe
    See Skyscanner API doc for more info https://skyscanner.github.io/slate/?_ga=1.104705984.172843296.1446781555#polling-the-results
    """
    # get legs (aggregated outbound or inbound trip)
    legs = pd.DataFrame.from_dict(rep_json['Legs'])
    # get itineraries (vector of 2 legs with the total price and price info)
    itineraries = pd.DataFrame.from_dict(rep_json['Itineraries'])
    # reset_index to get an unique id for each itinary
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
    # filter only most relevant itineraries (2 cheapest + 2 fastest)
    limit = min(2, legs.shape[0])
    legs = legs.sort_values(by='PriceTotal_AR').head(limit).append(legs.sort_values(by='Duration').head(limit))

    if not one_way:
        legs = legs.merge(itineraries[['itinerary_id', 'InboundLegId', 'PriceTotal_AR']], how='left',
                          left_on='Id', right_on='InboundLegId', suffixes=['', '_in'])
    # Filter out legs where there is no itinary associated (so no price)
    if only_with_price & one_way:
        legs = legs[(legs.Id.isin(itineraries.OutboundLegId.unique()))]
    elif only_with_price:
        legs = legs[
            (legs.Id.isin(itineraries.OutboundLegId.unique())) | (legs.Id.isin(itineraries.InboundLegId.unique()))]

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
             'Id', 'Code_origin_seg', 'geoloc_origin_seg', 'Code_destination_seg', 'geoloc_destination_seg',
             'FlightNumber_rich']].drop_duplicates(subset='Id').sort_values(by=['itinerary_id', 'Id_global'])


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
    stops_tmp = _AIRPORT_DF.copy()
    # compute proxi for distance (since we only need to compare no need to take the earth curve into account...)
    stops_tmp['distance_dep'] = stops_tmp.apply(lambda x: distance(geoloc_dep, x.geoloc).m, axis=1)
    stops_tmp['distance_arrival'] = stops_tmp.apply(lambda x: distance(geoloc_arrival, x.geoloc).m, axis=1)

    # We get the 3 closest airports for departure and arrival
    airport_list = dict()
    airport_list['departure'] = stops_tmp.sort_values(by='distance_dep').Code_sky.head(3).get_values()
    airport_list['arrival'] = stops_tmp.sort_values(by='distance_arrival').Code_sky.head(3).get_values()
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
    airports = get_airports_from_geo_locs(query.start_point, query.end_point)
    all_responses = list()
    # Let's try calling API for several airports at a time
    #json_query = {
    #                'query': {
    #                    'start': {
    #                        'coord': airports['departure'],
    #                    },
    #                    'to': {
    #                        'coord': airports['arrival'],
    #                    },
    #                    'datetime': query.departure_date
    #                    }
    #            }
    #all_responses = skyscanner_query_directions(json_query)

    # Let's call the API for every couple airport departure and arrival
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
            single_route = skyscanner_query_directions(json_query)
            if single_route is not None:
                for trip in single_route:
                    all_responses.append(trip)
            # print(f'all good from {airport_dep} to {airport_arrival}')


    all_reponses_json = list()
    for journey_sky in all_responses:
        all_reponses_json.append(journey_sky.to_json())

    return all_responses


if __name__ == '__main__':
    main()
