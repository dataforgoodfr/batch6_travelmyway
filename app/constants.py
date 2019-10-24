class constants():
    def __init__(self):
        # USAGES
        self.TYPE_PLANE = "Plane"
        self.TYPE_TRAIN = "Train"
        self.TYPE_COACH = "Coach"   # Inter cities
        self.TYPE_BUS = "Bus"       # Inner agglomeration
        self.TYPE_METRO = "Metro"
        self.TYPE_WAIT = "Waiting"
        self.TYPE_AUTOMOBILE = "Automobile"
        self.TYPE_METRO = "Metro"
        self.TYPE_BIKE = "Bike"
        self.TYPE_WALK = "Walking"
        self.TYPE_TRANSFER = "Transfer"
        self.TYPE_TRAM = "Tram"

        # UNITES
        self.UNIT_CONVERSION = 1

        # UNITES
        self.WAITING_PERIOD_TRAINLINE = 15 * 60
        self.WAITING_PERIOD_AIRPORT = 120 * 60
        self.WAITING_PERIOD_OUIBUS = 15 * 60
