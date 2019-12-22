import requests
import pandas as pd
from loguru import logger
import time
import copy
import json
import io
from threading import Thread
from humanfriendly import format_timespan
from app import TMW as tmw
from datetime import datetime as dt, timedelta
from geopy.distance import distance
from app import constants
from app import co2_emissions

# Get all train and bus station from trainline thanks to https://github.com/tducret/trainline-python
_STATIONS_CSV_FILE = "https://raw.githubusercontent.com/trainline-eu/stations/master/stations.csv"
_STATION_WAITING_PERIOD = constants.WAITING_PERIOD_TRAINLINE


class ThreadApiCall(Thread):
    """
    The class helps parallelize the computation journeys
    """
    def __init__(self, departure_date, origin_id, destination_id, origin_slug, destination_slug, passengers):
        Thread.__init__(self)
        self._return = None
        self.departure_date = departure_date
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.origin_slug = origin_slug
        self.destination_slug = destination_slug
        self.passengers = passengers

    def run(self):
        journeys = search_for_all_fares(self.departure_date, self.origin_id, self.destination_id, self.passengers)
        journeys['origin_slug'] = self.origin_slug
        journeys['destination_slug'] = self.destination_slug
        self._return = journeys

    def join(self):
        Thread.join(self)
        return self._return


def update_trainline_stops(url=_STATIONS_CSV_FILE):
    """
        This function loads the DB containing all the Trainline station we can call
        It's downloaded from a github account and enriched to match TMW's needs
        We return the list of all stops used for the API call
            + the list of corresponding slugs to build the booking URL
     """
    csv_content = requests.get(url).content
    all_stops_raw = pd.read_csv(io.StringIO(csv_content.decode('utf-8')),
                            sep=';', index_col=0, low_memory=False)
    # filter on station with parnt_station_id (that we can call the API with)
    all_stops = all_stops_raw[~pd.isna(all_stops_raw.parent_station_id)]
    parent_stations =  all_stops_raw[pd.isna(all_stops_raw.parent_station_id)]
    # Group info on bus or train
    all_stops['is_bus_station'] = all_stops.apply(
        lambda x: (x.busbud_is_enabled == 't') or (x.flixbus_is_enabled == 't'), axis=1)
    all_stops['is_train_station'] = all_stops.apply(lambda x: (x.sncf_is_enabled == 't') or (x.idtgv_is_enabled == 't')
                                                              or (x.db_is_enabled == 't') or (x.cff_is_enabled == 't')
                                                              or (x.leoexpress_is_enabled == 't') or (
                                                                          x.obb_is_enabled == 't')
                                                              or (x.ntv_is_enabled == 't') or (x.hkx_is_enabled == 't')
                                                              or (x.renfe_is_enabled == 't') or (
                                                                          x.atoc_is_enabled == 't')
                                                              or (x.benerail_is_enabled == 't') or (
                                                                          x.westbahn_is_enabled == 't')
                                                              or (x.ouigo_is_enabled == 't') or (
                                                                          x.trenitalia_is_enabled == 't'), axis=1)
    all_stops['geoloc'] = all_stops.apply(lambda x: [x.latitude, x.longitude], axis=1)
    # Keep only relevant columns
    all_stops = all_stops[['name', 'slug', 'country', 'latitude', 'longitude', 'geoloc', 'parent_station_id',
                           'is_bus_station', 'is_train_station']]
    all_stops['geoloc_good'] = all_stops.apply(lambda x: not(pd.isna(x.geoloc[0]) or pd.isna(x.geoloc[1])),axis=1)
    all_stops = all_stops[all_stops.geoloc_good]
    logger.info(f'{all_stops.shape[0]} stops were found. Here is an example:\n {all_stops.sample()}')
    # keep only relevant columns for parent station as well
    parent_stations = parent_stations[['slug']]
    return all_stops, parent_stations


# When the server starts we load the station DB
_ALL_STATIONS, _PARENT_STATION_SLUGS = update_trainline_stops()
# This is the regular format for regular passenger information to be sent to Trainline API
_PASSENGER = [{'id': '3c29a998-270e-416b-83f0-936b606638da', 'age': 39,
               'cards': [], 'label': '3c29a998-270e-416b-83f0-936b606638da'}]


# function to get all trainline fares and trips
def search_for_all_fares(date, origin_id, destination_id, passengers, include_bus=True, segment_details=True):
    """
        This function takes in all the relevant information for the API call and returns a
            dataframe containing all the information from Trainline API
         """
    # Define headers (according to github/trainline)
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'CaptainTrain/1574360965(web) (Ember 3.5.1)',
        'Accept-Language': 'fr',
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': 'www.trainline.eu',
    }

    session = requests.session()
    systems = ['sncf', 'db', 'idtgv', 'ouigo', 'trenitalia', 'ntv', 'hkx', 'renfe', 'cff', 'benerail', 'ocebo',
               'westbahn', 'leoexpress', 'locomore', 'distribusion', 'cityairporttrain', 'obb', 'timetable']
    if include_bus:
        systems.append('busbud')
        systems.append('flixbus')

    data = {'local_currency': 'EUR',
            'search': {'passengers': passengers,
                       'arrival_station_id': destination_id,
                       'departure_date': date,
                       'departure_station_id': origin_id,
                       'systems': systems
                       }
            }
    post_data = json.dumps(data)

    time_before_call = time.perf_counter()
    # logger.info('juste avant le post trainline')
    ret = session.post(url="https://www.trainline.eu/api/v5_1/search",
                       headers=headers,
                       data=post_data)
    logger.info(f'Trainline API call duration {time.perf_counter() - time_before_call}')
    # logger.info('avant le format')

    return format_trainline_response(ret.json(), segment_details=segment_details)


# Fucntion to format the trainline json repsonse
def format_trainline_response(rep_json, segment_details=True, only_sellable=True):
    """
    Format complicated json with information flighing around into a clear dataframe
    """
    time_start_format = time.perf_counter()
    # logger.info(rep_json)
    # get folders (aggregated outbound or inbound trip)
    folders = pd.DataFrame.from_dict(rep_json['folders'])
    logger.info(f'on a {(folders.shape)} trains')
    # get places
    stations = pd.DataFrame.from_dict(rep_json['stations'])

    # Filter out legs where there is no itinerary associated (so no price)
    if only_sellable:
        folders = folders[folders.is_sellable]
        if folders.empty:
            return None
    # Compute duration
    folders['departure_date'] = pd.to_datetime(folders.departure_date)
    folders['arrival_date'] = pd.to_datetime(folders.arrival_date)
    folders['duration_s'] = folders.apply(lambda x: (x.arrival_date - x.departure_date).seconds, axis=1)
    # Filter most relevant trips
    folders = folders.sort_values(by='cents').head(5).append(folders.sort_values(by='duration_s').head(5))
    folders = folders.drop_duplicates(subset='id')

    # We merge to get both the premiere departure station and the final station
    folders = folders.merge(stations[['id', 'name', 'country', 'latitude', 'longitude']],
                            left_on='departure_station_id', right_on='id', suffixes=['', '_depart'])
    folders = folders.merge(stations[['id', 'name', 'country', 'latitude', 'longitude']], left_on='arrival_station_id',
                            right_on='id', suffixes=['', '_arrival'])
    # If no details asked we stay at leg granularity
    if not segment_details:
        return folders[
            ['id', 'departure_date', 'arrival_date', 'nb_segments', 'name', 'country', 'latitude', 'longitude',
             'name_arrival', 'country_arrival', 'latitude_arrival', 'longitude_arrival',
             'cents', 'currency', 'comfort', 'flexibility', 'travel_class']].sort_values(by=['departure_date'])
    # else we break it down to each segment
    else:
        # get segments (each unique actual train)
        trips = pd.DataFrame.from_dict(rep_json['trips'])
        segments = pd.DataFrame.from_dict(rep_json['segments'])
        # Explode the list of segment associated to each leg to have one lie per segment
        folders_rich = pandas_explode(folders, 'trip_ids')
        folders_rich = folders_rich.merge(trips[['id', 'segment_ids']], left_on='trip_ids', right_on='id',
                                          suffixes=['_global', '_trip'])
        folders_rich['nb_segments'] = folders_rich.apply(lambda x: len(x['segment_ids']), axis=1)
        folders_rich = pandas_explode(folders_rich, 'segment_ids')
        folders_rich = folders_rich.merge(segments, left_on='segment_ids', right_on='id', suffixes=['', '_seg'])

        # Add relevant segment info to the exploded df (already containing all the leg and itinary infos)
        folders_rich = folders_rich.merge(stations[['id', 'name', 'country', 'latitude', 'longitude']],
                                          left_on='departure_station_id_seg', right_on='id',
                                          suffixes=['', '_depart_seg'])
        folders_rich = folders_rich.merge(stations[['id', 'name', 'country', 'latitude', 'longitude']],
                                          left_on='arrival_station_id_seg', right_on='id',
                                          suffixes=['', '_arrival_seg'])

        # Recreate the order of the segment (not working so far)
        # folders_rich['seg_rank'] = folders_rich.groupby('id')["departure_date_seg"].rank("dense")
        # keep only the relevant information

        folders_rich['geoloc_depart_seg'] = folders_rich.apply(
            lambda x: [x.latitude_depart_seg, x.longitude_depart_seg], axis=1)
        folders_rich['geoloc_arrival_seg'] = folders_rich.apply(
            lambda x: [x.latitude_arrival_seg, x.longitude_arrival_seg], axis=1)
        folders_rich['departure_date_seg'] = pd.to_datetime(folders_rich.departure_date_seg)
        folders_rich['arrival_date_seg'] = pd.to_datetime(folders_rich.arrival_date_seg)

        logger.info(f'Trainline format {time.perf_counter() - time_start_format}')
        return folders_rich[
            ['id_global', 'departure_date', 'arrival_date', 'nb_segments', 'name', 'country', 'latitude', 'longitude',
             'name_arrival', 'country_arrival', 'latitude_arrival', 'longitude_arrival',
             'cents', 'currency', 'departure_date_seg', 'name_depart_seg', 'country_depart_seg', 'geoloc_depart_seg',
             'arrival_date_seg', 'name_arrival_seg', 'country_arrival_seg', 'geoloc_arrival_seg',
             'transportation_mean', 'carrier', 'train_name', 'train_number', 'co2_emission',
             'flexibility', 'travel_class_seg']].sort_values(by=['id_global', 'departure_date_seg'])


def trainline_journeys(df_response, _id=0):
    """
        This function takes in a DF with detailled info about all the Trainline trips
        It returns a list of TMW journey objects
    """
    # affect a price to each leg (otherwise we would multiply the price by the number of legs
    df_response['price_step'] = df_response.cents / (df_response.nb_segments*100)

    # Compute distance for each leg
    # print(df_response.columns)
    df_response['distance_step'] = df_response.apply(lambda x: distance(x.geoloc_depart_seg, x.geoloc_arrival_seg).m,
                                                     axis=1)
    df_response['trip_code'] = df_response.train_name + ' ' + df_response.train_number
    tranportation_mean_to_type = {
        'coach': constants.TYPE_COACH,
        'train': constants.TYPE_TRAIN,
    }

    lst_journeys = list()
    # all itineraries :
    # print(f'nb itinerary : {df_response.id_global.nunique()}')
    for itinerary_id in df_response.id_global.unique():
        itinerary = df_response[df_response.id_global == itinerary_id].reset_index(drop=True)
        # boolean to know whether and when there will be a transfer after the leg
        itinerary['next_departure'] = itinerary.departure_date_seg.shift(-1)
        itinerary['next_stop_name'] = itinerary.name_depart_seg.shift(-1)
        itinerary['next_geoloc'] = itinerary.geoloc_depart_seg.shift(-1)
        # get the slugs to create the booking link
        origin_slug = itinerary.origin_slug.unique()[0]
        destination_slug = itinerary.destination_slug.unique()[0]

        i = _id
        lst_sections = list()
        # We add a waiting period at the station of 15 minutes
        step = tmw.journey_step(i,
                                _type=constants.TYPE_WAIT,
                                label=f'Arrive at the station {format_timespan(_STATION_WAITING_PERIOD)} before departure',
                                distance_m=0,
                                duration_s=_STATION_WAITING_PERIOD,
                                price_EUR=[0],
                                gCO2=0,
                                departure_point=[itinerary.latitude.iloc[0], itinerary.longitude.iloc[0]],
                                arrival_point=[itinerary.latitude.iloc[0], itinerary.longitude.iloc[0]],
                                departure_date=itinerary.departure_date_seg[0] - timedelta(seconds=_STATION_WAITING_PERIOD),
                                arrival_date=itinerary.departure_date_seg[0],
                                geojson=[],
                                )

        lst_sections.append(step)
        i = i + 1
        # Go through all steps of the journey
        for index, leg in itinerary.iterrows():
            local_distance_m = distance(leg.geoloc_depart_seg, leg.geoloc_arrival_seg).m
            local_transportation_type = tranportation_mean_to_type[leg.transportation_mean]
            local_emissions = co2_emissions.calculate_co2_emissions(local_transportation_type, constants.DEFAULT_CITY,
                                                      constants.DEFAULT_FUEL, constants.DEFAULT_NB_SEATS,
                                                      constants.DEFAULT_NB_KM) * \
                              constants.DEFAULT_NB_PASSENGERS * local_distance_m
            step = tmw.journey_step(i,
                                    _type=local_transportation_type,
                                    label=f'{leg.trip_code} to {leg.name_arrival_seg}',
                                    distance_m=local_distance_m,
                                    duration_s=(leg.arrival_date_seg - leg.departure_date_seg).seconds,
                                    price_EUR=[leg.price_step],
                                    gCO2=local_emissions,
                                    departure_point=leg.geoloc_depart_seg,
                                    arrival_point=leg.geoloc_arrival_seg,
                                    departure_stop_name=leg.name_depart_seg,
                                    arrival_stop_name=leg.name_arrival_seg,
                                    departure_date=leg.departure_date_seg,
                                    arrival_date=leg.arrival_date_seg,
                                    trip_code=leg.trip_code,
                                    geojson=[],
                                    )
            lst_sections.append(step)
            i = i + 1
            # add transfer steps
            if not pd.isna(leg.next_departure):
                step = tmw.journey_step(i,
                                        _type=constants.TYPE_TRANSFER,
                                        label=f'Transfer at {leg.name_arrival_seg}',
                                        distance_m=0,
                                        duration_s=(leg['next_departure'] - leg['arrival_date_seg']).seconds,
                                        price_EUR=[0],
                                        departure_point=leg.geoloc_arrival_seg,
                                        arrival_point=leg.next_geoloc,
                                        departure_stop_name=leg.name_depart_seg,
                                        arrival_stop_name=leg.name_arrival_seg,
                                        departure_date=leg.arrival_date_seg,
                                        arrival_date=leg.next_departure,
                                        gCO2=0,
                                        geojson=[],
                                        )
                lst_sections.append(step)
                i = i + 1
        departure_date_formated = dt.strptime(str(lst_sections[0].departure_date)[0:15], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:00')
        journey_train = tmw.journey(_id, steps=lst_sections,
                                    departure_date= lst_sections[0].departure_date,
                                    arrival_date= lst_sections[-1].arrival_date,
                                    booking_link=f'https://www.trainline.fr/search/{origin_slug}/{destination_slug}/{departure_date_formated}')
        # Add category
        category_journey = list()
        for step in journey_train.steps:
            if step.type not in [constants.TYPE_TRANSFER, constants.TYPE_WAIT]:
                category_journey.append(step.type)

        journey_train.category = list(set(category_journey))
        lst_journeys.append(journey_train)

        # for journey in lst_journeys:
        #    journey.update()

    return lst_journeys


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
def get_stops_from_geo_locs(geoloc_dep, geoloc_arrival, max_distance_km=50):
    """
        This function takes in the departure and arrival points of the TMW journey and returns
            the 3 closest stations within 50 km
    """
    # We filter only on the closest stops to have a smaller df (thus better perfs)
    stops_tmp = _ALL_STATIONS[(((_ALL_STATIONS.latitude-geoloc_dep[0])**2<0.6) & ((_ALL_STATIONS.longitude-geoloc_dep[1])**2<0.6)) |
                              (((_ALL_STATIONS.latitude-geoloc_arrival[0])**2<0.6) & ((_ALL_STATIONS.longitude-geoloc_arrival[1])**2<0.6))]\
                            [['geoloc', 'parent_station_id']].copy()

    stops_tmp['distance_dep'] = stops_tmp.apply(lambda x: (geoloc_dep[0]- x.geoloc[0])**2 + (geoloc_dep[1]- x.geoloc[1])**2, axis =1)
    stops_tmp['distance_arrival'] = stops_tmp.apply(lambda x: (geoloc_arrival[0]- x.geoloc[0])**2 + (geoloc_arrival[1]- x.geoloc[1])**2, axis =1)

    # We get all station within approx 55 km (<=> 0.5 of distance proxi)
    parent_station_id_list = {}
    parent_station_id_list['departure'] = stops_tmp[stops_tmp.distance_dep < 1000 * max_distance_km].sort_values(
                    by='distance_dep').head().parent_station_id.unique()
    parent_station_id_list['arrival'] = stops_tmp[stops_tmp.distance_arrival < 1000 * max_distance_km].sort_values(
        by='distance_arrival').head().parent_station_id.unique()
    return parent_station_id_list


def main(query):
    """
       This function is called from app/main.py
       It takes a query object and returns a list of journey objects
   """
    stops = get_stops_from_geo_locs(query.start_point, query.end_point)
    # print(f'{len(stops.departure)} departure parent station found ')
    # print(f'{len(stops.arrival)} arrival parent station found ')
    detail_response = pd.DataFrame()
    thread_list = list()
    i = 0
    departure_date_train = query.departure_date
    if len(str(departure_date_train)) == 10:
        # no hour specified we call the API for 8 AM
        departure_date_train = str(query.departure_date) + 'T08:00:00'
    for departure_station_id in stops['departure']:
        departure_slug = _PARENT_STATION_SLUGS.loc[departure_station_id,:].slug
        for arrival_station_id in stops['arrival']:
            arrival_slug = _PARENT_STATION_SLUGS.loc[arrival_station_id, :].slug
            logger.info(f'call Trainline API from {departure_slug}, to {arrival_slug }')
            thread_list.append(ThreadApiCall(departure_date_train, int(departure_station_id),
                                             int(arrival_station_id), departure_slug, arrival_slug ,
                                             _PASSENGER))
            thread_list[i].start()
            i = i+1

    for api_call in thread_list:
        fares = api_call.join()
        detail_response = detail_response.append(fares)
    time_after_API_call = time.perf_counter()
    # Make sure we don't have duplicates (due to the 2 calls)
    detail_response = detail_response.drop_duplicates(['departure_date', 'arrival_date', 'nb_segments', 'name', 'latitude', 'longitude',
                                                       'name_arrival', 'cents', 'departure_date_seg', 'name_depart_seg', 'arrival_date_seg', 'name_arrival_seg',
                                                       'train_name', 'train_number'])
    all_journeys = trainline_journeys(detail_response)
    # for i in all_journeys:
    #     print(i.to_json())

    return all_journeys


if __name__ == '__main__':
    main()
