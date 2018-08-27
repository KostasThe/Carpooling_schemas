import random
import simplejson, urllib
from pygeocoder import Geocoder
from memoizer import memoize



# map of city center mostly
THESS_MAP_MIN_LAT = 40.5794
THESS_MAP_MAX_LAT = 40.6496
THESS_MAP_MIN_LONG = 22.9338
THESS_MAP_MAX_LONG = 22.9647

class MyTime(object):
    def __init__(self, hour, minutes):
        self.hour = hour
        self.minutes = minutes
        
    # representation: If the time given is minutes only, then the representation is "xx mins". if it is equal or more than an hour then it is in "HH:MM" form.
    def __str__(self):
        if self.hour > 0:
            hour = str(self.hour).zfill(2)
            minutes = str(self.minutes).zfill(2)
            return hour + ":" + minutes
        elif self.minutes is 1:
            return str(self.minutes) + " min"
        else:
            return str(self.minutes) + " mins"
    
    def subtractTime(self, time):        
        hour = self.hour - time.hour               # subtract the hours.
        minutes = self.minutes - time.minutes                  # subtract the minutes.

        if minutes < 0:                                            # Possibly correct the time form, if hour or/and minutesutes are negative numbers.
            minutes += 60  # minutes = 60 + minutes, minutes < 0
            hour -= 1
        if hour < 0:
            hour %= 24
        return MyTime(hour, minutes)

    def addTime(self, time):       
        hour = self.hour + time.hour               # add the hours.
        minutes = self.minutes + time.minutes                  # add the minutes.        

        if minutes > 59:                                            # Possibly correct time form, if minutes exceeded 59 or hours exceeded 24.
            hour = hour + (minutes // 60)
            minutes = minutes % 60
        if hour > 23:
            hour = hour % 24
        return MyTime(hour, minutes)      
    
    # Syntax: time1.more_than(time2) --> compares 2 times and checks if time1 is bigger than time2.
    def more_than(self, time):           # time1 > time2
        if self.hour > time.hour:
            return True
        elif self.hour == time.hour:
            if self.minutes > time.minutes:
                return True
            else:
                return False
        else:
            return False
    
    def toInt(self):
        mins = 0
        if self.hour > 0:
            mins = self.hour * 60
        mins += self.minutes
        return mins
        
def getRandomTime():    
    minutes = random.choice([i for i in range(0, 60) if i % 5 == 0])    # "min" should be between 0-59. Here we only use only multiples of 5, so it can be 0, 5, 10 and so on.
    hour = random.randrange(14, 19)                                 # "hour" should be between 14 and 19 (14:00 - 19:00)
    return MyTime(hour, minutes)

def secondsToHours(seconds):        # converts seconds to hour, min
    hour = seconds // 3600
    minutes = (seconds // 60) % 60
    
    return MyTime(hour, minutes)

def subtractTime(time1, time2):        
    hour = time1.hour - time2.hour               # subtract the hours.
    minutes = time1.minutes - time2.minutes                  # subtract the minutes.

    if minutes < 0:                                            # Possibly correct the time form, if hour or/and minutesutes are negative numbers.
        minutes += 60  # min = 60 + min, min < 0
        hour -= 1
    if hour < 0:
        hour %= 24
    return MyTime(hour,minutes)

def addTime(time1, time2):       
    hour = time1.hour + time2.hour               # add the hours.
    minutes = time1.minutes + time2.minutes                  # add the minutes.
        

    if minutes > 59:                                            # Possibly correct time form, if minutes exceeded 59 or hours exceeded 24.
        hour = hour + (minutes // 60)
        minutes = minutes % 60
    if hour > 23:
        hour = hour % 24
    return MyTime(hour, minutes) 
    
def getTimeMargin():        # get a random time margin the client gives as a constraint for departure OR arrival.
    timeMargin = random.choice([i for i in range(5, 31) if i % 5 == 0])
    if timeMargin < 60:
        return MyTime(0, timeMargin)
    else:
        return MyTime(1, 0)        
        
def getNumberOfPassengers():
    return random.choice([1]*80 + [2]*15 + [3]*5)
    
def getCoordinates():
    latitude = round(random.uniform(THESS_MAP_MIN_LAT, THESS_MAP_MAX_LAT), 6)
    longitude = round(random.uniform(THESS_MAP_MIN_LONG, THESS_MAP_MAX_LONG), 6)   
    return latitude, longitude

# Creates a random number of Requests
def getRequests():
    return random.randint(5, 10)

def getRandomPlace():
    while True:                                            # try for coordinates (departure) that correspond to a valid address
        try:        
            location = getCoordinates()                                         # get random coordinates 
            address = Geocoder.reverse_geocode(location[0], location[1])   
            break
        except:
            pass
    return (location, address)

# define that customer wants a constraint on 0: arrival 1: departure
def getConstraintType():
    constraintType = random.choice(['A', 'D']) # Type 0: constraint on arrival Type 1: constraint on departure, 
    return constraintType

def constraintRequest(duration, constraint, margin):
    if constraint is 'A': # case a, constraint on arrival
        maxArrTime = getRandomTime()
        minArrTime = subtractTime(maxArrTime, margin)
        maxDepTime = subtractTime(maxArrTime, duration)
        minDepTime = subtractTime(minArrTime, duration)
    else:                 # case b, constraint on departure
        minDepTime = getRandomTime()
        maxDepTime = addTime(minDepTime, margin)
        minArrTime = addTime(minDepTime, duration)
        maxArrTime = addTime(maxDepTime, duration)
    
    return minDepTime, maxDepTime, minArrTime, maxArrTime
    
@memoize
def distanceMatrix(pointA, pointB):
    url = "http://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false".format(str(pointA),str(pointB))
    result = simplejson.load(urllib.urlopen(url))
    return result


def getDuration(pointA, pointB):
    result = distanceMatrix(pointA, pointB)
    duration_seconds = result['rows'][0]['elements'][0]['duration']['value']
    duration = secondsToHours(duration_seconds)
    return duration
    
def getDistance(pointA, pointB):
    result = distanceMatrix(pointA, pointB)
    distance = result['rows'][0]['elements'][0]['distance']['value']
    return distance

    
""" Request Class """
class Request(object):
    def __init__(self, reqNumber, passengers, departure, 
                arrival, duration, constraint, margin, times):            # constructor creates an object with nil values except for "reqNumber"
        self.reqNumber = reqNumber
        self.passengers = passengers
        self.duration = duration
        self.margin = getTimeMargin()                                        # time margin
        self.minDepTime = times[0]                                    # minimum time of departure
        self.maxDepTime = times[1]                                    # maximum time of departure
        self.minArrTime = times[2]                                    # minimum time of arrival
        self.maxArrTime = times[3]                                    # maximum time of arrival    
        self.departureLoc = departure[0]                            # coordinates of departure point 
        self.departureAddress = departure[1]                        # address of departure point (just for the end user)
        self.arrivalLoc = arrival[0]                                # coordinates of arrival point
        self.arrivalAddress = arrival[1]                            # address of arrival point (just for the end user)
        if constraint is 'A':
            self.constraint = 'A'
            self.constraintStr = "arrival"
        else:
            self.constraint = 'D'
            self.constraintStr = "departure"

    def __str__(self):
        line = '+-----------------------------------------------------------------------------+'
        box = '|'
        m = """
 {space:30} Request {req}:
 
{line}
| Passengers: {passengers}{space:21}Duration: {dur:7}{box:>26}
| Departure: {minDep} - {maxDep}{space:10}Arrival: {minArr} - {maxArr}{box:>21}
| Time Margin: {margin:7}{space:14}Constraint: on {constr:9}{box:>19}
| {box:>77}
| {space:28}Departure Address:{box:>31}
| {depAddr:76}{box:>1}
| {box:>77}
| {space:30}Arrival Address:{box:>31}
| {arrAddr:76}{box:>1}
{line}
""".format(space='', req=self.reqNumber + 1, passengers=self.passengers, \
    minDep=self.minDepTime, maxDep=self.maxDepTime, minArr=self.minArrTime, \
    maxArr=self.maxArrTime, dur=self.duration, constr=self.constraintStr, \
    depAddr=self.departureAddress, depCoord=self.departureLoc, arrAddr=self.arrivalAddress,line=line,\
    box=box, margin=self.margin, arrCoord=self.arrivalLoc)
        return m

   
# First, it creates a random number of requests. Then it creates a list of Request objects and fills them with the request's individual information. 
# Finally it prints out in the console each Request's object info.

def makeRequest():
    numberOfReqs = getRequests()
    print "Total Requests: %s\n" % (str(numberOfReqs))
    requestsList = []                                            # Initialize a list for the Objects (Requests)
    for reqNumber in range(numberOfReqs):                    # Use iteration to fill in each Request values
        passengers = getNumberOfPassengers()                # Start filling in the values of the current Request
        departure = getRandomPlace()    
        arrival = getRandomPlace()
        constraint = getConstraintType()
        margin = getTimeMargin()
        duration = getDuration(departure[0], arrival[0])       
        times = constraintRequest(duration, constraint, margin)
        requestsList.append(Request(reqNumber, passengers, departure, arrival, duration, constraint, margin, times))
    return requestsList

def printRequests(alist):
    for request in alist:
        print request

        