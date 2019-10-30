import flask
from flask import request
from flask import json

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
    array_steps = generate_fake_steps()
    json = {'id': 1,
            'label': '',
            'score': '',
            'total_distance': '',
            'total_duration': '',
            'total_price_EUR': '',
            'departure_point': '',
            'arrival_point': '',
            'departure_date': '',
            'arrival_date': '',
            'total_gCO2': '',
            'journey': array_steps}
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

    try:
        result = json.dumps(generate_fake_journey())
        return result, 200
    except Exception:
        return "Server error", 500


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


app.run()
