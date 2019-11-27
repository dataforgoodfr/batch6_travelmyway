from loguru import logger
from app import Trainline
from app import Skyscanner
from app import OuiBus
from app import Navitia
from app import ORS
from app import constants
from app import TMW as tmw
from time import perf_counter

"""
Build a multi-modal journey
"""

def filter_and_label_relevant_journey(journey_list):
    filtered_journeys = list()
    nb_journey_per_label = min(len(journey_list), 2)
    # Label the complete journeys
    journey_list.sort(key=lambda x: x.total_price_EUR, reverse=False)
    journey_list[0].label = constants.LABEL_CHEAPEST_JOURNEY
    filtered_journeys = filtered_journeys + journey_list[0:nb_journey_per_label]
    journey_list.sort(key=lambda x: x.total_duration, reverse=False)
    journey_list[0].label = constants.LABEL_FASTEST_JOURNEY
    filtered_journeys = filtered_journeys + journey_list[0:nb_journey_per_label]
    journey_list.sort(key=lambda x: x.total_gCO2, reverse=False)
    journey_list[0].label = constants.LABEL_CLEANEST_JOURNEY
    filtered_journeys = filtered_journeys + journey_list[0:nb_journey_per_label]
    logger.info(f'after labels we have {len(filtered_journeys)} journeys in the filter')
    # Making sure we hand out at least one journey for each type (if possible)
    type_checks = {constants.CATEGORY_COACH_JOURNEY: False, constants.CATEGORY_TRAIN_JOURNEY: False,
                   constants.CATEGORY_PLANE_JOURNEY: False, constants.CATEGORY_CAR_JOURNEY: False}
    for journey in journey_list:
        if (constants.CATEGORY_COACH_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_COACH_JOURNEY]):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_COACH_JOURNEY] = True
        if (constants.CATEGORY_TRAIN_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_TRAIN_JOURNEY]):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_TRAIN_JOURNEY] = True
        if (constants.CATEGORY_PLANE_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_PLANE_JOURNEY]):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_PLANE_JOURNEY] = True
        if (constants.CATEGORY_CAR_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_CAR_JOURNEY]):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_CAR_JOURNEY] = True
    logger.info(f'after type check we have {len(filtered_journeys)} journeys in the filter')
    # Delete double entries
    return list(set(filtered_journeys))


def compute_complete_journey(departure_date = '2019-11-28', geoloc_dep=[48.85,2.35], geoloc_arrival=[43.60,1.44]):
    # Let's create the start to finish query
    query_start_finish = tmw.query(geoloc_dep, geoloc_arrival, departure_date)
    logger.info(f'query_start_finish{query_start_finish.to_json()}')

    # First we look for intercities journeys
    trainline_journeys = Trainline.main(query_start_finish)
    logger.info('trainline good')
    skyscanner_journeys = Skyscanner.main(query_start_finish)
    logger.info('sky good')
    ouibus_journeys = OuiBus.main(query_start_finish)
    logger.info('ouibus good')
    ors_journey = ORS.ORS_query_directions(query_start_finish)
    logger.info('ors good')

    all_journeys = trainline_journeys + skyscanner_journeys + ouibus_journeys
    logger.info(f'we found {len(all_journeys)} inter urban journeys')

    # Start the stopwatch / counter
    t1_start = perf_counter()
    # Then we call Navitia to get the beginning and the end of the journey
    for i_, interurban_journey in enumerate(all_journeys):
        interurban_journey.id = i_
        update_interurban_journey(interurban_journey)
    # WIP IGOR
    # from multiprocessing import Pool
    # with Pool(5) as p:
    #     p.map(update_interurban_journey, all_journeys)
    # Stop the stopwatch / counter
    t1_stop = perf_counter()
    delta_time = t1_stop - t1_start
    logger.info(f'Elapsed time during the whole program in seconds: {delta_time}')

    all_journeys.append(ors_journey)

    # Filter most relevant Journeys
    filtered_journeys = filter_and_label_relevant_journey(all_journeys)
    filtered_journeys = [filtered_journey.to_json() for filtered_journey in filtered_journeys]
    return filtered_journeys


def update_interurban_journey(interurban_journey):
    start_to_station_query = tmw.query(interurban_journey.departure_point, interurban_journey.steps[0].departure_point,
                                       interurban_journey.departure_date)
    logger.info(f'start_to_station_query{start_to_station_query.to_json()}')
    start_to_station_steps = Navitia.navitia_query_directions(start_to_station_query)
    station_to_arrival_query = tmw.query(interurban_journey.steps[-1].arrival_point, interurban_journey.arrival_point,
                                         interurban_journey.steps[-1].arrival_date)
    logger.info(f'station_to_arrival_query{station_to_arrival_query.to_json()}')
    station_to_arrival_steps = Navitia.navitia_query_directions(station_to_arrival_query)
    if (start_to_station_steps is not None) & (station_to_arrival_steps is not None):
        interurban_journey.add_steps(start_to_station_steps[0].steps, start_end=True)
        interurban_journey.add_steps(station_to_arrival_steps[0].steps, start_end=False)
        interurban_journey.update()
    else:
        logger.info(f'remove {interurban_journey.category}')
        # TODO IGOR
        # all_journeys.remove(interurban_journey)
        #interurban_journey.reset()
    return

def main(departure_date='2019-11-28', geoloc_dep=[48.85, 2.35], geoloc_arrival=[43.59053, 1.42299]):
    all_trips = compute_complete_journey(departure_date, geoloc_dep, geoloc_arrival)

    for i in all_trips:
        print(type(i))
        print(i)
        #print(i.to_json())

_PASSENGER = [{"id": 1, "age": 30, "price_currency": "EUR"}]

if __name__ == '__main__':
    main()
