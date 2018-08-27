import request
from memoizer import memoize

busCapacity = 12
VAN_BASE = (40.635701, 22.944152)

##############################################################################################        

class Node(object):
    def __init__(self, number, constraint_type):
        self.number = number 
        self.constraint_type = constraint_type        # A, D
    
    def match_request(self, requestsList):
        for req in requestsList:
            if req.reqNumber is self.number:
                return req
    
    def __str__(self):    
        m = "%d" % (self.number + 1)
        if self.number+1 % 10 is 1:
            m += "st Customer's "
        elif self.number+1 % 10 is 2:
            m+= "nd Customer's "
        elif self.number+1 % 10 is 3:
            m+= "rd Customer's "
        else:
            m += "th Customer's "
            
        if self.constraint_type is 'A':
            m += "Arrival"
        else:
            m += "Departure"
        return m
        
##############################################################################################        
        
class FeasibleRoute(object):    
    def __init__(self, number, route_nodes, timeline, number_of_buses, km_travelled, delay, \
                bus1=None, bus2=None, optimal=False, combo_ID=None, combo_km=None, combo_delay=None, score=None):    
        
        self.number = number
        self.route_nodes = route_nodes
        self.timeline = timeline
        self.number_of_buses = number_of_buses
        self.km_travelled = km_travelled
        self.delay = delay
        self.bus1 = bus1
        self.bus2 = bus2
        self.optimal = optimal
        self.combo_ID = combo_ID
        self.combo_km = combo_km
        self.combo_delay = combo_delay
        self.score = score
        
    def __str__(self):
        arrow = '->'
        m = ''
        if self.combo_ID is None:
            m += "{space:10}--------------------> Feasible Route {number:<2} <--------------------\n\n".format(space='', number=self.number+1)
            if self.optimal is True:
                m += "{space:22} (Optimal route if we use 1 bus)\n".format(space='')
        else:
            m += "{space:10}--------------------> Feasible Route {number:<2} <--------------------\n\n".format(space='', number=self.number)
            if self.optimal:
                m += "{space:22} (OPTIMAL COMBINATION IF WE USE 2 BUS. Combo {combo})\n\n".format(space='', combo=self.combo_ID)
        for node, time in zip(self.route_nodes, self.timeline):        
            m += "    {space:16}{node:26} {arrow:4} {time:8}\n".format(
                    space='',node=node, arrow=arrow, time=time)    
        m += """
                    Route Information: 
        
                    Kilometers travelled: {km}
                    Customer waiting time: {delay}           
        """.format(delay=self.combo_delay, km=self.combo_km)
        return m
            
          
    def is_with_one_bus(self):
        if self.number_of_buses is 1:
            return True
        else:
            return False
            
    def print_optimal(self):
        if self.optimal is True:
            if self.number_of_buses is 1:
                print "Route %d is optimal if we use 1 bus." % (self.number)
            elif self.number_of_buses is 2:
                if self.bus1 is True:
                    print "Route %d is optimal for the first bus, if we use 2 buses." % (self.number)
                elif self.bus2 is True:
                    print "Route %d is optimal for the second bus, if we use 2 buses." % (self.number)
        else:
            print self.number, "Not optimal"
            
    def is_first_bus(self):
        if self.number_of_buses is 2 and self.bus1 is True:
            return True
        else:
            return False
            
    def is_second_bus(self):
        if self.number_of_buses is 2 and self.bus2 is True:
            return True
        else:
            return False
    

##############################################################################################        
#
#                    FUNCTIONS
#
############################################################################################## 

def getNode2Node(requestsList, nodeA, nodeB, quest):
    if type(nodeA) is Node: # if it's a route node (and not the starting point) match it to the long & lat of the request
        nodeA_req = nodeA.match_request(requestsList)
        
        if nodeA.constraint_type is 'D':                                        # if we are at a departure point
            locA = nodeA_req.departureLoc            
        else:                                                            # if we are at an arrival point
            locA = nodeA_req.arrivalLoc
    else:                #else it's the starting point
        locA = nodeA
    
    if type(nodeB) is Node:
        nodeB_req = nodeB.match_request(requestsList)
    
        if nodeB.constraint_type is 'D':                                            # if we are going at a departure point
            locB = nodeB_req.departureLoc                
        else:                                                            # if we are going at an arrival point
            locB = nodeB_req.arrivalLoc                
    else:
        locB = nodeB

    if quest == 'Duration':
        return request.getDuration(locA, locB)
    else:                                                     #quest == 'Distance':
        return request.getDistance(locA, locB)
        

def isPossible(newRoute, time, requestsList):        # checks if a route is possible
    
    bus = []                                    # initializations:
    busPassengers = 0
    route = []
            
    for item in newRoute:
        if type(item) is Node:
            route.append(item)
            
    lengthOfRoute = len(route)
    lastNode = route[lengthOfRoute-1]                # this the most recently added node. 
    lastNode_req = lastNode.match_request(requestsList)
    if lengthOfRoute is 1: 
        if lastNode.constraint_type is 'A':                    # if this a route with only one node (the beginning of a possible route) 
            return False, time                            # this node MUST be a departure. (we can't start from an arrival point)
        else: 
            time = lastNode_req.minDepTime            
    else:        
        for station in route:                    # check every station that is already in route
            if station.constraint_type is 'D':                
                bus.append(station.number)                                    # add to bus the clients (or else the so far visited departure nodes), in order to know which arrival points we can visit next.
                req = station.match_request(requestsList)    
                busPassengers += req.passengers    # add the passengers number (we can receive more than 1 passenger per departure location)
        if busPassengers > busCapacity:                        # check if passengers exceed bus capacity. If true, reject the route.
            errorMsg = "Route impossible: Bus is full"
            return False, errorMsg
        busPosition = route[lengthOfRoute - 2]                # bus position is on the previous node of "lastNode". We need to check if moving to the new one makes the route impossible.
        dur = getNode2Node(requestsList, busPosition, lastNode, "Duration")        
        time = request.addTime(time, dur)  # time = time + the duration from bus position to the new node.

        if lastNode.constraint_type is 'A':                                                            # check if the new "time" satisfies the time constraints. If it is a departure node:
            if time.more_than(lastNode_req.maxArrTime): # check if time is more than max arrival time. If true, reject the route.
                errorMsg = "Route impossible: Time exceeds client's max arrival time"
                return False, errorMsg
        else:
            if time.more_than(lastNode_req.maxDepTime): # check if time is more than the max Departure time, and if true reject the route.
                errorMsg = "Route impossible: Time exceeds client's max departure time"
                return False, errorMsg                
            elif not time.more_than(lastNode_req.minDepTime): # check if new time is less than min Departure time. if true, the bus has to wait to this node to pickup the client.
                time = lastNode_req.minDepTime                # so replace time with the nodes min departure time.                                                            
    return True, time                                                        # if all of the constraints are satisfied, the route is possible

#this is where the possible route lists are being populated.

def nextRoute(route, requestsList):
    finalResult = []
    allNodes = []
    bus = []
    
    for req in requestsList:                            # populate the list "allNodes" with all the nodes.
        allNodes.append(Node(req.reqNumber, 'D'))
        allNodes.append(Node(req.reqNumber, 'A'))
        
    if len(route) is not 1:                            # if len(route) is 1, then we don't need to check if a node is already added to the route.
        newNodes = list(allNodes)                    #create a copy of allNodes
        for node in newNodes:        
            for station in route:
                if type(station) is Node:
                    if (node.number == station.number) and (node.constraint_type == station.constraint_type):    # if a node from allNodes is already in the route (we have visited it)    
                        allNodes.remove(node)                                            # we have to remove it.
    
    for station in route:                    # check every station that is already in route
        if type(station) is Node:
            if station.constraint_type is 'D':                
                bus.append(station.number)                                    # add the clients to bus (or else the so far visited departure nodes)
    
    newNodes = list(allNodes)
    for node in newNodes:
        if node.constraint_type is 'A' and node.number not in bus and node in allNodes:
            allNodes.remove(node)
    
    for node in allNodes:                        
        newRoute = list(route)                # copy the nodes from route to newRoute
        newRoute.append(node)                # append the new node to newRoute

        if len(newRoute) is 1:
            node_req = node.match_request(requestsList)
            time = node_req.minDepTime
        else:                                    # if there are more than 1 node in newRoute    
            for item in newRoute:                # find the time (MyTime type) in this list, name it "time" and remove it from newRoute
                if type(item) is request.MyTime:    
                    time = item


        results = isPossible(newRoute, time, requestsList) # check if the newRoute is possible (satisfies the constraints)
        if results[0]:                                # results[0] is True/False, depending on whether newRoute is a possible route. If it is:
            time = results[1]                                # results[1] is the new time (time which we are on the next feasible node)
            newRoute.append(time)        # --> [D1, D2, time] 
            finalResult.append(newRoute)
    return finalResult
    
def calcRoutes(requestsList):
    target_length = (len(requestsList) * 4)     
    result = []                                                        # this will be the final result of complete routes
    times = []
    timeline = []
    possibleRoutes = [ [] ]                                            # the empty route is the first possible route,
    while possibleRoutes:                                            # while possibleRoutes is not an empty list 
        route = possibleRoutes.pop()                                # route = to teleutaio stoixeio ths listas possibleRoutes  # take a possible route
        nextPossibleRoutes = nextRoute(route, requestsList)            # create possible routes by adding all the stations that can be added to `route`
        for next_route in nextPossibleRoutes:                        # if the route is complete, add to result
            if len(next_route) == target_length:                    
                temp_route = list(next_route)        
                for item in temp_route:
                    if type(item) is request.MyTime:                        # remove "time" from the route
                        times.append(item)
                        next_route.remove(item)    
                result.append(next_route)                            # and add it to the result with the feasible routes.
                timeline.append(times)
                times = []
            else:                                                    # else add back for processing
                possibleRoutes.append(next_route)                    
    return result, timeline
            
def find_routes_km(requestsList, route):
    route_length = len(route)
    meters = 0
    
    base_to_first_node = getNode2Node(requestsList, VAN_BASE, route[0], "Distance")                #adding the km from the starting point to the 1st node        
    return_to_base = getNode2Node(requestsList, route[route_length-1], VAN_BASE, "Distance")    
    if route_length is 2:
        nodeA = route[0]
        nodeB = route[1]
        meters += getNode2Node(requestsList, nodeA, nodeB, "Distance")
    else:
        for i in range(route_length - 2):
            nodeA = route[i]
            nodeB = route[i+1]
            meters += getNode2Node(requestsList, nodeA, nodeB, "Distance")
    km_travelled = float(meters + base_to_first_node + return_to_base) / 1000
    return km_travelled

def find_customers_delay(requestsList, route, timeline):
    delay = 0
    for node, time in zip(route, timeline):
        req = node.match_request(requestsList)      # e.g requestsList[1]
        constraint = req.constraint
        if node.constraint_type == constraint:
            if constraint is 'A':
                delay += request.subtractTime(req.maxArrTime, time).toInt()
            else:
                delay += request.subtractTime(time, req.minDepTime).toInt()    
    return delay
    
    
def with_one_van(requests, feasible_routes, feas_index):

    result = calcRoutes(requests)
    possRoutes = result[0]
    timelines = result[1]
    if possRoutes:
        for route, timeline in zip(possRoutes, timelines):
            km = find_routes_km(requests, route)
            delay = find_customers_delay(requests, route, timeline)
            feasible_routes.append(FeasibleRoute(feas_index, route, timeline, 1, km, delay, combo_km=km, combo_delay=delay))
            feas_index += 1
        return (True, feasible_routes, feas_index)
    else:
        return (False, 0, 0)

def with_two_vans(requests, van1, van2, feasible_routes, feas_index, combo):
    
    result1 = calcRoutes(van1)
    possRoutesVan1 = result1[0]
    timelinesVan1 = result1[1]
    
    result2 = calcRoutes(van2)
    possRoutesVan2 = result2[0]
    timelinesVan2 = result2[1]
    
    if possRoutesVan1 and possRoutesVan2:
        # for the first van
        for route, timeline in zip(possRoutesVan1, timelinesVan1):
            km = find_routes_km(requests, route)
            delay = find_customers_delay(requests, route, timeline)
            feasible_routes.append(FeasibleRoute(feas_index, route, timeline, 2, km, delay, bus1=True, combo_ID=combo))
            feas_index += 1
        
        # for the second van
        for route, timeline in zip(possRoutesVan2, timelinesVan2):
            km = find_routes_km(requests, route)
            delay = find_customers_delay(requests, route, timeline)
            feasible_routes.append(FeasibleRoute(feas_index, route, timeline, 2, km, delay, bus2=True, combo_ID=combo))
            feas_index += 1    
        return (True, feasible_routes, feas_index, combo)
    else:
        return (False, 0, 0, 0)
    
