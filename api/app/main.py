from loguru import logger
# from app import Trainline
# from app import Skyscanner
# from app import OuiBus
from app import Navitia
# from app import ORS
from app import constants
from app import TMW as tmw
from time import perf_counter

"""
Build a multi-modal journey
"""


def filter_and_label_relevant_journey(journey_list):
    """
    We want to filter the most relevant journeys we want to display to the user
    We show the 3 cheapest, 3 fastest and 3 cleanest +
    we make sure that we have at least one journey of each type (if possible)
    """
    filtered_journeys = list()
    nb_journey_per_label = min(len(journey_list), 3)
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
    # logger.info(f'after labels we have {len(filtered_journeys)} journeys in the filter')
    # Making sure we hand out at least one journey for each type (if possible)
    type_checks = {constants.CATEGORY_COACH_JOURNEY: 0, constants.CATEGORY_TRAIN_JOURNEY: 0,
                   constants.CATEGORY_PLANE_JOURNEY: 0, constants.CATEGORY_CAR_JOURNEY: 0}
    for journey in journey_list:
        if (constants.CATEGORY_COACH_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_COACH_JOURNEY] < 2):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_COACH_JOURNEY] = type_checks[constants.CATEGORY_COACH_JOURNEY] + 1
        if (constants.CATEGORY_TRAIN_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_TRAIN_JOURNEY] < 2):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_TRAIN_JOURNEY] = type_checks[constants.CATEGORY_TRAIN_JOURNEY] + 1
        if (constants.CATEGORY_PLANE_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_PLANE_JOURNEY] < 2):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_PLANE_JOURNEY] = type_checks[constants.CATEGORY_PLANE_JOURNEY] + 1
        if (constants.CATEGORY_CAR_JOURNEY in journey.category) & (not type_checks[constants.CATEGORY_CAR_JOURNEY] < 2):
            filtered_journeys.append(journey)
            type_checks[constants.CATEGORY_CAR_JOURNEY] = type_checks[constants.CATEGORY_CAR_JOURNEY] + 1
    logger.info(f'after type check we have {len(filtered_journeys)} journeys in the filter')
    # Delete double entries
    return list(set(filtered_journeys))


def compute_complete_journey(departure_date = '2019-11-28', geoloc_dep=[48.85,2.35], geoloc_arrival=[43.60,1.44]):
    """
    Build a multi-modal journey:
    First we call each API to get a few journeys for each type of transportation
    Then we create a multi-modal trip by calling NAvitia between the departure point and departure station
        and between arrival station and arrival point.
    To limit the nb of Navitia calls, we first create all the necessary Navitia queries, and deduplicate them
        to make sure we call Navitia only once for each query
    Finally we call the filter function to choose which journeys we keep
    """
    # Let's create the start to finish query
    query_start_finish = tmw.query(0, geoloc_dep, geoloc_arrival, departure_date)
    # logger.info(f'query_start_finish{query_start_finish.to_json()}')
    # Start the stopwatch / counter
    t1_start = perf_counter()
    # First we look for intercities journeys
    #train_start = perf_counter()
    #trainline_journeys = Trainline.main(query_start_finish)
    #train_stop = perf_counter()
    #logger.info(f'found {len(trainline_journeys)} trainline journeys')
    #sky_start = perf_counter()
    #skyscanner_journeys = Skyscanner.main(query_start_finish)
    #sky_stop = perf_counter()
    #logger.info(f'found {len(skyscanner_journeys)} skyscanner journeys')
    #ouibus_start = perf_counter()
    #ouibus_journeys = OuiBus.main(query_start_finish)
    #ouibus_stop = perf_counter()
    #logger.info(f'found {len(ouibus_journeys)} ouibus journeys')
    #ors_start = perf_counter()
    #ors_journey = ORS.ORS_query_directions(query_start_finish)
    #ors_stop = perf_counter()
    #logger.info(f'ors good')

    # Création des threads
    thread_trainline = tmw.ThreadComputeJourney(api='Trainline', query=query_start_finish)
    thread_skyscanner = tmw.ThreadComputeJourney(api='Skyscanner', query=query_start_finish)
    thread_ouibus = tmw.ThreadComputeJourney(api='OuiBus', query=query_start_finish)
    thread_ors = tmw.ThreadComputeJourney(api='ORS', query=query_start_finish)

    # Lancement des threads
    thread_trainline.start()
    thread_skyscanner.start()
    thread_ouibus.start()
    thread_ors.start()

    # Attendre que les threads se terminent
    trainline_journeys, time_trainline = thread_trainline.join()
    skyscanner_journeys, time_skyscanner = thread_skyscanner.join()
    ouibus_journeys, time_ouibus = thread_ouibus.join()
    ors_journey, time_or = thread_ors.join()

    all_journeys = trainline_journeys + skyscanner_journeys + ouibus_journeys
    # all_journeys = skyscanner_journeys
    i = 0
    # logger.info(f'we found {len(all_journeys)} inter urban journeys')
    # Then we call Navitia to get the beginning and the end of the journey
    # Let's record all the query we need to send to Navitia, deduplicate them and call NAvitia only once
    navitia_queries = list()
    for interurban_journey in all_journeys:
        interurban_journey.id = i
        i = i + 1
        navitia_queries.append(tmw.query(0, geoloc_dep, interurban_journey.steps[0].departure_point, departure_date))
        navitia_queries.append(tmw.query(0, interurban_journey.steps[-1].arrival_point, geoloc_arrival, departure_date))

    # Call Navitia only once each time:
    navitia_dict = {}
    navitia_query_done = list()
    for navitia_query in navitia_queries:
        if navitia_query.to_json() in navitia_query_done:
            # if query has been called then skip
            continue
        # logger.info(f'call Navitia with {navitia_query.to_json()}')
        navitia_steps = Navitia.navitia_query_directions(navitia_query)
        navitia_dict[str(navitia_query.to_json())] = navitia_steps
        navitia_query_done.append(navitia_query.to_json())
        # navitia_dict_list.append(navitia_dict)

    nav_start = perf_counter()
    # Reconsiliate between navitia queries and interrurban journeys
    for interurban_journey in all_journeys:
        # Get start to station query
        start_to_station_query = tmw.query(0, geoloc_dep, interurban_journey.steps[0].departure_point, departure_date)
        start_to_station_steps = navitia_dict[str(start_to_station_query.to_json())]
        station_to_arrival_query = tmw.query(0, interurban_journey.steps[-1].arrival_point, geoloc_arrival, departure_date)
        station_to_arrival_steps = navitia_dict[str(station_to_arrival_query.to_json())]
        if (start_to_station_steps is not None) & (station_to_arrival_steps is not None):
            interurban_journey.add_steps(start_to_station_steps[0].steps, start_end=True)
            interurban_journey.add_steps(station_to_arrival_steps[0].steps, start_end=False)
            interurban_journey.update()
        else:
            # logger.info(f'remove category {interurban_journey.category}')
            # logger.info(f'remove price {interurban_journey.total_price_EUR}')#
            # logger.info(f'remove price {interurban_journey.total_distance}')
            # logger.info(f'remove legs nb {len(interurban_journey.steps)}')
            # logger.info(f'last leg departs from {interurban_journey.steps[-1].departure_stop_name}')
            # logger.info(f'last leg arrives in  {interurban_journey.steps[-1].arrival_stop_name}')
            all_journeys.remove(interurban_journey)
    nav_stop = perf_counter()

    all_journeys.append(ors_journey)

    # Filter most relevant Journeys
    filtered_journeys = filter_and_label_relevant_journey(all_journeys)
    filtered_journeys = [filtered_journey.to_json() for filtered_journey in filtered_journeys]
    t1_stop = perf_counter()
    logger.info(f'Elapsed time during computation: {t1_stop-t1_start} s')
    logger.info(f'including: {time_trainline}s for trainline ')
    logger.info(f'including: {time_skyscanner}s for skyscanner ')
    logger.info(f'including: {time_ouibus}s for ouibus ')
    logger.info(f'including: {time_or}s for ors ')
    logger.info(f'including: {nav_stop - nav_start}s for navitia ')
    return filtered_journeys


# This function only serves to run locally in debug
def main(departure_date='2019-12-18T10:00:00', geoloc_dep=[48.85,2.35], geoloc_arrival=[43.5994, 1.4337]):
    all_trips = compute_complete_journey(departure_date, geoloc_dep, geoloc_arrival)

    for i in all_trips:
        print(type(i))
        print(i)
        #print(i.to_json())

if __name__ == '__main__':
    main()
