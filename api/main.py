import flask
from flask import request
from flask import jsonify
from flask_json import json_response
from app import main
from loguru import logger
import json

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
    json = {'id': 5, 'label': 'Cleanest Journey', 'category': ['Train'], 'score': 0, 'total_distance': 924599.84036874, 'total_duration': 34590, 'total_price_EUR': 354.0, 'departure_point': [0, 0], 'arrival_point': [0, 0], 'departure_date': '2019-11-27 20:12:43.319095', 'arrival_date': '2019-11-27 20:12:43.319100', 'total_gCO2': 5162.341506064944,
            'journey_steps': [{'id': 0, 'type': 'Walking', 'label': 'Walking FROM 9 Rue de la Commune (Nantes) TO Bouffay (Nantes)', 'distance_m': 582, 'duration_s': 520, 'price_EUR': [0], 'departure_point': '9 Rue de la Commune (Nantes)', 'arrival_point': 'Bouffay (Nantes)', 'departure_stop_name': '9 Rue de la Commune (Nantes)', 'arrival_stop_name': 'Bouffay (Nantes)', 'departure_date': '2019-11-27 20:14:20', 'arrival_date': '2019-11-27 20:23:00', 'trip_code': '', 'gCO2': 0.0},
                              {'id': 1, 'type': 'tan - nantes métropole', 'label': 'Tramway 1 / François Mitterrand / Jamet - Beaujoire / Ranzay / direction: Beaujoire (Nantes)', 'distance_m': 823, 'duration_s': 180, 'price_EUR': [0], 'departure_point': 'Bouffay (Nantes)', 'arrival_point': 'Gare Nord (Nantes)', 'departure_stop_name': 'Bouffay (Nantes)', 'arrival_stop_name': 'Gare Nord (Nantes)', 'departure_date': '2019-11-27 20:23:00', 'arrival_date': '2019-11-27 20:26:00', 'trip_code': '', 'gCO2': 3.292},
                              {'id': 2, 'type': 'Walking', 'label': 'Walking FROM Gare Nord (Nantes) TO 6 Rue de Lourmel (Nantes)', 'distance_m': 257, 'duration_s': 230, 'price_EUR': [0], 'departure_point': 'Gare Nord (Nantes)', 'arrival_point': '6 Rue de Lourmel (Nantes)', 'departure_stop_name': 'Gare Nord (Nantes)', 'arrival_stop_name': '6 Rue de Lourmel (Nantes)', 'departure_date': '2019-11-27 20:26:00', 'arrival_date': '2019-11-27 20:29:50', 'trip_code': '', 'gCO2': 0.0},
                              {'id': 3, 'type': 'Waiting', 'label': '', 'distance_m': 0, 'duration_s': 900, 'price_EUR': [0], 'departure_point': [47.216148, -1.542356], 'arrival_point': [47.216148, -1.542356], 'departure_stop_name': '', 'arrival_stop_name': '', 'departure_date': '2019-11-27 20:12:23.124732', 'arrival_date': '2019-11-27 20:12:23.124738', 'trip_code': '', 'gCO2': 0},
                              {'id': 4, 'type': 'Train', 'label': '', 'distance_m': 340016.01178404916, 'duration_s': 7140, 'price_EUR': [177.0], 'departure_point': [47.216148, -1.542356], 'arrival_point': [48.841172, 2.320514], 'departure_stop_name': 'Nantes', 'arrival_stop_name': 'Paris Montparnasse', 'departure_date': '2019-11-28 07:39:00+01:00', 'arrival_date': '2019-11-28 09:38:00+01:00', 'trip_code': 'TGV 8806', 'gCO2': 1904.0896659906753},
                              {'id': 5, 'type': 'Transfer', 'label': '', 'distance_m': 0, 'duration_s': 3540, 'price_EUR': [0], 'departure_point': [48.841172, 2.320514], 'arrival_point': [48.844888, 2.37352], 'departure_stop_name': 'Nantes', 'arrival_stop_name': 'Paris Montparnasse', 'departure_date': '2019-11-28 09:38:00+01:00', 'arrival_date': '2019-11-28 10:37:00+01:00', 'trip_code': '', 'gCO2': 0},
                              {'id': 6, 'type': 'Train', 'label': '', 'distance_m': 581242.8285846909, 'duration_s': 20580, 'price_EUR': [177.0], 'departure_point': [48.844888, 2.37352], 'arrival_point': [45.071832, 7.665164], 'departure_stop_name': 'Paris Gare de Lyon', 'arrival_stop_name': 'Torino Porta Susa', 'departure_date': '2019-11-28 10:37:00+01:00', 'arrival_date': '2019-11-28 16:20:00+01:00', 'trip_code': 'TGV 9245', 'gCO2': 3254.9598400742693},
                              {'id': 7, 'type': 'Walking', 'label': 'Walking FROM 19 Corso Inghilterra (Torino) TO Via Roma (Torino)', 'distance_m': 1679, 'duration_s': 1500, 'price_EUR': [0], 'departure_point': '19 Corso Inghilterra (Torino)', 'arrival_point': 'Via Roma (Torino)', 'departure_stop_name': '19 Corso Inghilterra (Torino)', 'arrival_stop_name': 'Via Roma (Torino)', 'departure_date': '2019-11-27 20:13:11', 'arrival_date': '2019-11-27 20:38:11', 'trip_code': '', 'gCO2': 0.0}]}

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
        result = main.compute_complete_journey(date_time, start, end)
        js = json.dumps(result)
        resp = flask.Response(js, status=200, mimetype='application/json')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except Exception:
        return "Server error", 500


@app.route('/fake_journey', methods=['GET'])
def compute_fake_journey():
    start = request.args.get('from')
    end = request.args.get('to')
    date_time = request.args.get('start')
    result = generate_fake_journey()
    logger.info('result')
    logger.info(result)
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
        # result = json.dumps(generate_fake_journey())
        result = generate_fake_journey()
        logger.info(result)
        js = json.dumps(result)
        resp = flask.Response(js, status=200, mimetype='application/json')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
        # logger.info(result)
        #return response
        # return json_response(status_=200, data_=result)
    except Exception:
        return "Server error", 500


@app.route('/hello', methods = ['GET'])
def api_hello():
    result = generate_fake_journey()
    logger.info(result)
    js = json.dumps(result)
    logger.info(js)
    resp = flask.Response(js, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


app.run()
