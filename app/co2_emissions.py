import os
import pandas as pd
from app import constants

def calculate_co2_emissions(type_transport, type_city, fuel, nb_seats, nb_km):
    path = os.path.join(os.getcwd(), constants.ADEME_LOC_DB_PATH)
    try :
        carbon_db = pd.read_excel(path)
    except:
        carbon_db = pd.read_excel(os.path.join(os.getcwd(), 'app/', constants.ADEME_LOC_DB_PATH))
    
    select_type_transport = (carbon_db.loc[:, constants.TYPE_OF_TRANSPORT] == type_transport)
    index_db = select_type_transport
    if type_city != '':
        select_city_size = (carbon_db.loc[:, constants.LOCALISATION] == type_city)
        index_db = index_db & select_city_size
    if fuel != '':
        select_fuel = (carbon_db.loc[:, constants.FUEL] == fuel)
        index_db = index_db & select_fuel
    if nb_seats != '':
        select_nb_seats = (carbon_db.loc[:, constants.NB_SEATS] == nb_seats)
        index_db = index_db & select_nb_seats
    if nb_km != '':
        select_nb_km = (carbon_db.loc[:, constants.NB_KM] == nb_km)
        index_db = index_db & select_nb_km
    return carbon_db.loc[index_db, constants.CO2EQ_PASS_KM].values[0]