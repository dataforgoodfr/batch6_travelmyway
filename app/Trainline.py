import requests
import pandas as pd
import copy
import json
import io
import TMW as tmw
from datetime import datetime as dt
from geopy.distance import distance
import constants
from co2_emissions import calculate_co2_emissions

# Get all train and bus station from trainline thanks to https://github.com/tducret/trainline-python
_STATIONS_CSV_FILE = "https://raw.githubusercontent.com/trainline-eu/stations/master/stations.csv"
_STATION_WAITING_PERIOD = constants.WAITING_PERIOD_TRAINLINE


def update_trainline_stops(url=_STATIONS_CSV_FILE):
    csv_content = requests.get(url).content
    all_stops = pd.read_csv(io.StringIO(csv_content.decode('utf-8')),
                            sep=';', index_col=0, low_memory=False)
    # filter on station with parnt_station_id (that we can call the API with)
    all_stops = all_stops[~pd.isna(all_stops.parent_station_id)]
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
    print(f'{all_stops.shape[0]} stops were found. Here is an example:\n {all_stops.sample()}')
    return all_stops


_ALL_STATIONS = update_trainline_stops()

_PASSENGER = [{'id': '3c29a998-270e-416b-83f0-936b606638da', 'age': 39,
               'cards': [], 'label': '3c29a998-270e-416b-83f0-936b606638da'}]


# function to get all trainline fares and trips
def search_for_all_fares(date, origin_id, destination_id, passengers, include_bus=True, segment_details=True):
    # Define headers (according to github/trainline)
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'CaptainTrain/43(4302) Android/4.4.2(19)',
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

    tmp = dt.now()
    ret = session.post(url="https://www.trainline.eu/api/v5_1/search",
                       headers=headers,
                       data=post_data)

    # print(f'API call duration {dt.now() - tmp}')

    return format_trainline_response(ret.json(), segment_details=segment_details)


# Fucntion to format the trainline json repsonse
def format_trainline_response(rep_json, segment_details=True, only_sellable=True):
    """
    Format complicated json with information flighing around into a clear dataframe
    """
    # get folders (aggregated outbound or inbound trip)
    folders = pd.DataFrame.from_dict(rep_json['folders'])

    # get places
    stations = pd.DataFrame.from_dict(rep_json['stations'])

    # Filter out legs where there is no itinerary associated (so no price)
    if only_sellable:
        folders = folders[folders.is_sellable]

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

        return folders_rich[
            ['id_global', 'departure_date', 'arrival_date', 'nb_segments', 'name', 'country', 'latitude', 'longitude',
             'name_arrival', 'country_arrival', 'latitude_arrival', 'longitude_arrival',
             'cents', 'currency', 'departure_date_seg', 'name_depart_seg', 'country_depart_seg', 'geoloc_depart_seg',
             'arrival_date_seg', 'name_arrival_seg', 'country_arrival_seg', 'geoloc_arrival_seg',
             'transportation_mean', 'carrier', 'train_name', 'train_number', 'co2_emission',
             'flexibility', 'travel_class_seg']].sort_values(by=['id_global', 'departure_date_seg'])


def trainline_journeys(df_response, _id=0):
    # affect a price to each leg
    df_response['price_step'] = df_response.cents / 100
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
        itinerary = df_response[df_response.id_global == itinerary_id]
        # boolean to know whether and when there will be a transfer after the leg
        itinerary['next_departure'] = itinerary.departure_date_seg.shift(-1)
        itinerary['next_stop_name'] = itinerary.name_depart_seg.shift(-1)
        itinerary['next_geoloc'] = itinerary.geoloc_depart_seg.shift(-1)
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
                                departure_point=[itinerary.latitude.iloc[0], itinerary.longitude.iloc[0]],
                                arrival_point=[itinerary.latitude.iloc[0], itinerary.longitude.iloc[0]],
                                geojson=[],
                                )
        lst_sections.append(step)
        i = i + 1
        for index, leg in itinerary.iterrows():
            local_distance_m = distance(leg.geoloc_depart_seg, leg.geoloc_arrival_seg).m
            local_emissions = calculate_co2_emissions(constants.TYPE_TRAIN, '', '', '', '') * \
                              constants.DEFAULT_NB_PASSENGERS * local_distance_m
            step = tmw.journey_step(i,
                                    _type=tranportation_mean_to_type[leg.transportation_mean],
                                    label='',
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
                                        label='',
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

        journey_sky = tmw.journey(_id,
                                  steps=lst_sections)
        lst_journeys.append(journey_sky)

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
    stops_tmp = _ALL_STATIONS.copy()
    # compute proxi for distance (since we only need to compare no need to take the earth curve into account...)
    stops_tmp['distance_dep'] = stops_tmp.apply(lambda x: distance(geoloc_dep, x.geoloc).m, axis =1)
    stops_tmp['distance_arrival'] = stops_tmp.apply(lambda x: distance(geoloc_arrival, x.geoloc).m, axis =1)

    # We get all station within approx 55 km (<=> 0.5 of distance proxi)
    parent_station_id_list = {}
    parent_station_id_list['departure'] = stops_tmp[stops_tmp.distance_dep < 1000 * max_distance_km].sort_values(
                    by='distance_dep').head().parent_station_id.unique()
    parent_station_id_list['arrival'] = stops_tmp[stops_tmp.distance_arrival < 1000 * max_distance_km].sort_values(
        by='distance_arrival').head().parent_station_id.unique()
    return parent_station_id_list


def main(query):
    stops = get_stops_from_geo_locs(query.start_point, query.end_point)
    # print(f'{len(stops.departure)} departure parent station found ')
    # print(f'{len(stops.arrival)} arrival parent station found ')
    detail_response = pd.DataFrame()
    for departure_station_id in stops['departure']:
        for arrival_station_id in stops['arrival']:
            print(f'call Trainline API from {departure_station_id}, to {arrival_station_id }')
            detail_response = detail_response.append(search_for_all_fares(query.departure_date, int(departure_station_id),
                                                                          int(arrival_station_id), _PASSENGER,
                                                                          segment_details=True))
    all_journeys = trainline_journeys(detail_response)
    # for i in all_journeys:
    #     print(i.to_json())

    return all_journeys


if __name__ == '__main__':
    main()
