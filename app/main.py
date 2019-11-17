import Trainline
import Skyscanner
import OuiBus
import Navitia
import ORS
import constants
import TMW as tmw


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

    # Making sure we hand out at least one journey for each type (if possible)
    type_checks = {constants.CATEGORY_COACH_JOURNEY: False, constants.CATEGORY_TRAIN_JOURNEY: False,
                   constants.CATEGORY_PLANE_JOURNEY: False}
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
    # Delete double entries
    return list(set(filtered_journeys))


def compute_complete_journey(departure_date = '2019-11-25T09:00:00+0200', geoloc_dep=[48.85,2.35], geoloc_arrival=[43.60,1.44]):
    # Let's create the start to finish query
    query_start_finish = tmw.query(0, geoloc_dep, geoloc_arrival, departure_date)
    print(query_start_finish)
    # First we look for intercities journeys
    trainline_journeys = Trainline.main(query_start_finish)
    skyscanner_journeys = Skyscanner.main(query_start_finish)
    ouibus_journeys = OuiBus.main(query_start_finish)
    # ors_step = ORS.ORS_query_directions(query_start_finish)

    all_journeys = trainline_journeys + skyscanner_journeys + ouibus_journeys
    # Then we call Navitia to get the beginning and the end of the journey
    for interurban_journey in all_journeys:
        start_to_station_query = tmw.query(0, geoloc_dep, interurban_journey.steps[0].departure_point, departure_date)
        start_to_station_steps = Navitia.navitia_query_directions(start_to_station_query)
        station_to_arrival_query = tmw.query(0, interurban_journey.steps[-1].arrival_point, geoloc_arrival, departure_date)
        station_to_arrival_steps = Navitia.navitia_query_directions(station_to_arrival_query)
        if (start_to_station_steps is not None) & (station_to_arrival_steps is not None):
            interurban_journey.add_steps(start_to_station_steps[0].steps, start_end=True)
            interurban_journey.add_steps(station_to_arrival_steps[0].steps, start_end=False)
            interurban_journey.update()
        else :
            interurban_journey.reset()

    # all_journeys = all_journeys + ors_step

    # Filter most relevant Journeys
    return filter_and_label_relevant_journey(all_journeys)


def main(departure_date='2019-11-25', geoloc_dep=[48.85, 2.35], geoloc_arrival=[43.59053, 1.42299]):
    all_trips = compute_complete_journey(departure_date, geoloc_dep, geoloc_arrival)

    for i in all_trips:
        print(i.to_json())

_PASSENGER = [{"id": 1, "age": 30, "price_currency": "EUR"}]

if __name__ == '__main__':
    main()
