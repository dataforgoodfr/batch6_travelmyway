import flask
from flask import request
from flask import json
from flask_json import json_response
from app import main
from loguru import logger

app = flask.Flask(__name__)
app.config["DEBUG"] = True


def generate_fake_steps():
    json = {'id': 0,
            'type': '',
            'label': '',
            'distance_m': '',
            'duration_s': '',
            'price_EUR': '',
            'departure_point': '',
            'arrival_point': '',
            'departure_stop_name': '',
            'arrival_stop_name': '',
            'departure_date': '',
            'arrival_date': '',
            'trip_code': '',
            'gCO2': '',
            'geojson': '',
            }
    return json


def generate_fake_journey():
    # array_steps = generate_fake_steps()
    json = {'id':0,'label':'Cheapest Journey','category':['Coach'],'score':0,'total_distance':584927.5507267849,'total_duration':36751,'total_price_EUR':18.99,'departure_point':[0,0],'arrival_point':[0,0],'departure_date':'2019-11-17 18:18:47.764185','arrival_date':'2019-11-17 18:18:47.764192','total_gCO2':2435.5156621818364,
            'journey_steps':[{'id':0,'type':'Walking','label':'Walking FROM 52 Boulevard Saint-Germain (Paris) TO Maubert - Mutualité (Paris)','distance_m':None,'duration_s':45,'price_EUR':[0],'departure_point':[0.0],'arrival_point':[0.0],'departure_stop_name':'','arrival_stop_name':'','departure_date':'2019-11-17 18:18:14.866097','arrival_date':'2019-11-17 18:18:14.866102','trip_code':'','gCO2':0.0},
                             {'id':1,'type':'ratp','label':'Bus 63 / Gare de Lyon - Porte de la Muette / direction: Gare de Lyon - Maison de la RATP (Paris)','distance_m':None,'duration_s':600,'price_EUR':[0],'departure_point':[0.0],'arrival_point':[0.0],'departure_stop_name':'','arrival_stop_name':'','departure_date':'2019-11-17 18:18:14.866097','arrival_date':'2019-11-17 18:18:14.866102','trip_code':'','gCO2':263.291},
                             {'id':2,'type':'Walking','label':'Walking FROM Gare de Lyon - Maison de la RATP (Paris) TO 180 Quai de Bercy (Paris)','distance_m':None,'duration_s':1073,'price_EUR':[0],'departure_point':[0.0],'arrival_point':[0.0],'departure_stop_name':'','arrival_stop_name':'','departure_date':'2019-11-17 18:18:14.866097','arrival_date':'2019-11-17 18:18:14.866102','trip_code':'','gCO2':0.0},
                             {'id':3,'type':'Waiting','label':'','distance_m':0,'duration_s':900,'price_EUR':[0],'departure_point':[48.835318,2.380519],'arrival_point':[48.835318,2.380519],'departure_stop_name':'','arrival_stop_name':'','departure_date':'2019-11-17 18:18:14.866097','arrival_date':'2019-11-17 18:18:14.866102','trip_code':'','gCO2':0},
                             {'id':4,'type':'Coach','label':'','distance_m':584927.5507267849,'duration_s':32700,'price_EUR':[18.99],'departure_point':[48.835318,2.380519],'arrival_point':[43.612522,1.452612],'departure_stop_name':'Paris (Bercy Seine)','arrival_stop_name':'Toulouse','departure_date':'2019-11-25 03:25:00+01:00','arrival_date':'2019-11-25 12:30:00+01:00','trip_code':'Car ','gCO2':2158.382662181836},
                             {'id':5,'type':'Walking','label':'Walking FROM 68 Boulevard Pierre Semard (Toulouse) TO Marengo-SNCF (Toulouse)','distance_m':None,'duration_s':397,'price_EUR':[0],'departure_point':[0.0],'arrival_point':[0.0],'departure_stop_name':'','arrival_stop_name':'','departure_date':'2019-11-17 18:18:14.866097','arrival_date':'2019-11-17 18:18:14.866102','trip_code':'','gCO2':0.0},
                             {'id':6,'type':'tisséo','label':'Métro A / Basso Cambo / Balma - Gramont / direction: Basso Cambo (Toulouse)','distance_m':None,'duration_s':540,'price_EUR':[0],'departure_point':[0.0],'arrival_point':[0.0],'departure_stop_name':'','arrival_stop_name':'','departure_date':'2019-11-17 18:18:14.866097','arrival_date':'2019-11-17 18:18:14.866102','trip_code':'','gCO2':13.842},
                             {'id':7,'type':'Walking','label':'Walking FROM Fontaine Lestang (Toulouse) TO 1 Rue Yvan Lacassagne (Toulouse)','distance_m':None,'duration_s':496,'price_EUR':[0],'departure_point':[0.0],'arrival_point':[0.0],'departure_stop_name':'','arrival_stop_name':'','departure_date':'2019-11-17 18:18:14.866097','arrival_date':'2019-11-17 18:18:14.866102','trip_code':'','gCO2':0.0}
                             ]
            }
    return json


@app.route('/', methods=['GET'])
def status():
    return "<h1>OK</h1><p>API is up and running.</p>", 200


@app.route('/journey', methods=['GET'])
def compute_journey():
    start = request.args.get('from')
    end = request.args.get('to')
    date_time = request.args.get('start')
    if start is None or end is None or date_time is None:
        return "<h1>KO</h1><p>Missing mandatory parameters</p>", 500
    logger.info(f'end {end}, start {start} date {date_time}')
    try:
        end = end.split(',')
        end[0] = float(end[0])
        end[1] = float(end[1])
        start = start.split(',')
        start[0] = float(start[0])
        start[1] = float(start[1])
        logger.info(f'start {start}')
        logger.info(f'end {end}')
    except:
        return "<h1>KO</h1><p>geoloc format not recognized</p>"
    try:
        #result = json.dumps(generate_fake_journey())
        result = json.dumps(main.compute_complete_journey(date_time, start, end))
        return result, 200
    except Exception:
        return "Server error", 500


@app.route('/fake_journey', methods=['GET'])
def compute_fake_journey():
    start = request.args.get('from')
    end = request.args.get('to')
    date_time = request.args.get('start')
    if start is None or end is None or date_time is None:
        return "<h1>KO</h1><p>Missing mandatory parameters</p>", 500
    logger.info(f'end {end}, start {start} date {date_time}')
    try:
        end = end.split(',')
        end[0] = float(end[0])
        end[1] = float(end[1])
        start = start.split(',')
        start[0] = float(start[0])
        start[1] = float(start[1])
        logger.info(f'start {start}')
        logger.info(f'end {end}')
    except:
        return "<h1>KO</h1><p>geoloc format not recognized</p>"
    try:
        result = json.dumps(generate_fake_journey())
        # logger.info(result)
        return json_response(status_=200, data_=result)
    except Exception:
        return "Server error", 500


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


app.run()
