import os
import pandas as pd
from app import constants
from loguru import logger


path = os.path.join(os.getcwd(), constants.ADEME_LOC_DB_PATH)#
try:
    logger.info(f'before pd.read_excel(path)')

    _CARBON_DB = pd.read_excel(path)
except:
    try :
        tmp = os.path.join(os.getcwd(), 'app/', constants.ADEME_LOC_DB_PATH)
        logger.info(tmp)
        _CARBON_DB = pd.read_csv(os.path.join(os.getcwd(), 'api/app/', constants.ADEME_LOC_DB_PATH),sep = ';')
        logger.info(_CARBON_DB.head(1))
    except:
        tmp = os.path.join(os.getcwd(), 'app/', constants.ADEME_LOC_DB_PATH)
        logger.info(tmp)
        _CARBON_DB = pd.read_csv(os.path.join(os.getcwd(), 'app/', constants.ADEME_LOC_DB_PATH), sep=';')
        logger.info(_CARBON_DB.head(1))

def calculate_co2_emissions_old(type_transport, type_city, fuel, nb_seats, nb_km):

    #path = os.path.join(os.getcwd(), constants.ADEME_LOC_DB_PATH)
    #logger.info(f'apres path')
    ## carbon_db = pd.read_excel(path)
    ## @Baptiste, pq on a besoin de ce try and except??
    #try :
    #    logger.info(f'before pd.read_excel(path)')
#
    #    carbon_db = pd.read_excel(path)
    #except:
    #    logger.info(f'before pd.read_excel(os.path.join(os.getcwd())')
    #    carbon_db = pd.read_excel(os.path.join(os.getcwd(), 'app/', constants.ADEME_LOC_DB_PATH))
    
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


def calculate_co2_emissions(type_transport, type_city, fuel, nb_seats, nb_km):
    # logger.info(f'inside co2')
    # logger.info('djbfk')
    # logger.info(f'constants.ADEME_LOC_DB_PATH {constants.ADEME_LOC_DB_PATH}')
    # path = os.path.join(os.getcwd(), constants.ADEME_LOC_DB_PATH)
    # carbon_db = pd.read_csv(path, delimiter=';')
    carbon_db = _CARBON_DB
    select_type_transport = (carbon_db.loc[:, constants.TYPE_OF_TRANSPORT] == type_transport)
    index_db = select_type_transport
    if type_city != constants.DEFAULT_CITY:
        select_city = (carbon_db.loc[:, constants.CITY] == type_city[0])
        index_db = index_db & select_city
        select_city_size_min = (carbon_db.loc[:, constants.CITY_SIZE_MIN] == float(type_city[1]))
        index_db = index_db & select_city_size_min
        select_city_size_max = (carbon_db.loc[:, constants.CITY_SIZE_MAX] == float(type_city[2]))
        index_db = index_db & select_city_size_max
    if fuel != constants.DEFAULT_FUEL:
        select_fuel = (carbon_db.loc[:, constants.FUEL] == fuel)
        index_db = index_db & select_fuel
    if nb_seats != constants.DEFAULT_NB_SEATS:
        select_nb_seats_min = (carbon_db.loc[:, constants.NB_SEATS_MIN] == float(nb_seats[0]))
        index_db = index_db & select_nb_seats_min
        select_nb_seats_max = (carbon_db.loc[:, constants.NB_SEATS_MAX] == float(nb_seats[1]))
        index_db = index_db & select_nb_seats_max
    if nb_km != constants.DEFAULT_NB_KM:
        select_nb_km_min = (carbon_db.loc[:, constants.NB_KM_MIN] == float(nb_km[0]))
        index_db = index_db & select_nb_km_min
        select_nb_km_max = (carbon_db.loc[:, constants.NB_KM_MAX] == float(nb_km[1]))
        index_db = index_db & select_nb_km_max

    return carbon_db.loc[index_db, 'value'].values[0]

