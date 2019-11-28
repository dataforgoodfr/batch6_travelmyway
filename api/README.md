# Prerequisites:

Version python 3

```shell
pip install -r requirements.txt
```

# Launch the API:

From your terminal 
```shell
cd api
python main.py
```

# Test the API:

2 end_points 
## Journey
The main endpoint, which will call all the travel APIs and bring them together thanks to the TravelMyWay magic
From your browser launch the URL : http://127.0.0.1:5000/journey?from=48.85,2.35&to=52.517,13.388&start=2019-11-28.

The format has to be 
from = latitude,longitude (of the departure point)
to = latitude,longitude (of the arrival point)
start = date (departure date)

The response shall be a json containing all the informations regarding the journeys computed by TravelMyWay

Please note that the response time might be a bit long 

## Fake_journey
Returns a pre-computed json, allways the same and with no delay.
From your browser launch the URL : http://127.0.0.1:5000/fake_journey?from=48.85,2.35&to=52.517,13.388&start=2019-11-28.

The format has to be 
from = any string
to = any string
start = any string
