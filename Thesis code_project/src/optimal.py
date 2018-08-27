import request as rq
import routefinder as rt
import numpy as np
import random

def eliminate_combos(feasible_routes):
    for route in feasible_routes:
        if route.number_of_buses is 2:
            last_combo = feasible_routes[len(feasible_routes)-1].combo_ID
    combo_km = []
    combo_delay = []
    
    for x in range(last_combo+1):
        first_bus_routes = []
        second_bus_routes = []
        for route in feasible_routes:
            if route.combo_ID is x:
                if route.is_first_bus():
                    first_bus_routes.append(route)
                elif route.is_second_bus():
                    second_bus_routes.append(route)
                    

        if len(first_bus_routes) > 1:
            min_route = first_bus_routes[0]
            temp_feas = list(feasible_routes)
            for i in range(len(first_bus_routes)):
                if first_bus_routes[i].km_travelled < min_route.km_travelled:
                    min_route = first_bus_routes[i]
            for route in temp_feas:
                if min_route.number is not route.number and route.is_first_bus() and route.combo_ID is x:
                    feasible_routes.remove(route)
            
        if len(second_bus_routes) > 1:
            min_route = second_bus_routes[0]
            temp_feas = list(feasible_routes)
            for j in range(len(second_bus_routes)):
                if second_bus_routes[j].km_travelled < min_route.km_travelled:
                    min_route = second_bus_routes[j]
            for route in temp_feas:
                if min_route.number is not route.number and route.is_second_bus() and route.combo_ID is x:
                    feasible_routes.remove(route)                
    
    for x in range(last_combo+1):
        km = 0
        delay = 0
        for route in feasible_routes:
            if route.combo_ID is x:
                km += route.km_travelled
                delay += route.delay
        combo_km.append(km)
        combo_delay.append(delay)
    for x in range(last_combo+1):
        for route in feasible_routes:
            if route.combo_ID is x:
                route.combo_km = combo_km[x]
                route.combo_delay = combo_delay[x]
    return feasible_routes

def delete_non_optimal_routes(feasible_routes):
    def to_remove(route):
        if route.number_of_buses is 2 and route.optimal is False:
            return True
        else:
            return False
    
    temp_feas = [x for x in feasible_routes if not to_remove(x)]
    
    return temp_feas
    
def choose_optimal_route(feasible_routes, buses):
    one_bus_count = 0

    c_km = []
    c_delay = []
    c_ID = []
    
    km = []
    delay = []
    route_number = []

    if buses is 1:
        for route in feasible_routes:
            if route.is_with_one_bus():
                one_bus_count += 1
                
        # 1 BUS
        if one_bus_count is 1:
            for route in feasible_routes:
                if route.is_with_one_bus():
                    route.optimal = True
        elif one_bus_count > 1:
            for route in feasible_routes:
                if route.number_of_buses is 1:
                    km.append(route.km_travelled)
                    delay.append(route.delay)
                    route_number.append(route.number)        
            best = apply_AHP(km, delay, route_number, 1)
            best_route = best
            for route in feasible_routes:
                if route.number is best_route:
                    route.optimal = True                    

            print "\nNo routes found with 1 bus."
    elif buses is 2:
        # 2 BUSES
        for route in feasible_routes:
            if route.number_of_buses is 2:
                c_km.append(route.combo_km)
                c_delay.append(route.combo_delay)
                c_ID.append(route.combo_ID)
        combo_km = [i for x, i in enumerate(c_km) if x % 2 == 0]
        combo_delay = [i for x, i in enumerate(c_delay) if x % 2 == 0]
        combo_ID = [i for x, i in enumerate(c_ID) if x % 2 == 0]        
        best = apply_AHP(combo_km, combo_delay, combo_ID, 2)
        best_route = best
        for route in feasible_routes:
            if route.combo_ID is best_route:
                route.optimal = True
            if route.combo_ID is not best_route and route.combo_ID is not None:
                route.optimal = False
    else:        
        # CHOOSE OPTIMAL BETWEEN USING 1 OR 2 BUSES:
        km = []
        delay = []
        route_number = []
            
        for route in feasible_routes:
            if route.optimal and route.is_with_one_bus():
                km.append(route.km_travelled)
                delay.append(route.delay)
                route_number.append(route.number)
            
            if route.optimal and route.is_first_bus():
                km.append(route.combo_km)
                delay.append(route.combo_delay)
                route_number.append(route.combo_ID)    
        result = apply_AHP(km, delay, route_number, 3)
        best_result = result
        for route in feasible_routes:
            if route.number is not best_result:
                route.optimal = False
            if route.combo_ID is best_result:
                route.optimal = True
                
    return feasible_routes
    
    
def make_matrix(aList):            # aList could be a) route_km b) delay
    matr_list = []
    n = len(aList)
    
    # make the Routes km Matrix
    for i in range(0, n):
        for j in range(0, n):
            if aList[i] is 0:
                aList[i] = 1
            matr_list.append(float(aList[j]) / float(aList[i]))
    matrix = np.reshape(matr_list, (n, n))        # make it a N x N matrix
    
    return matrix    

def apply_AHP(routes_km, customers_delay, combo_ID, buses):
    criteria_weights = np.array( [[0.9], [0.1]] )        

    km_matrix = make_matrix(routes_km)                        # make the Routes KM Matrix
    sum_km_col = np.sum(km_matrix, axis=0)                    # sum the columns of km_matrix
    km_norm = km_matrix / sum_km_col                        # normalize the km matrix
    km_priorities = np.average(km_norm, axis=1)                # find the priorities array of normalized km matrix
    
    delay_matrix = make_matrix(customers_delay)                # make the Delay Matrix
    sum_delay_col = np.sum(delay_matrix, axis=0)            # sum the columns of delay_matrix
    delay_norm = delay_matrix / sum_delay_col                # normalize the delay_matrix
    delay_priorities = np.average(delay_norm, axis=1)        # find the priorities array (average of rows) of normalized delay matrix    
    
    finalized_matrix = np.array([km_priorities, delay_priorities])        # make a finalized matrix which contains the priorities values of km and delay.
    transposed_final_matrix = np.transpose(finalized_matrix)            # transpose the finalized matrix
    
    result_matrix = np.dot(transposed_final_matrix, criteria_weights)    # find the dot product of trasposed finalized matrix and criteria weights
    maximum = np.amax(result_matrix)    
    result_list = result_matrix.tolist()
    
    pos = [i for i, j in enumerate(result_list) if j == maximum]
    if type(pos) is list:
        position = random.choice(pos)
    if buses is 1:
        print "Checked the routes: %s. Best route is %s." % (str(combo_ID), str(combo_ID[position]))
    elif buses is 2:
        print "Checked the combos: %s. Best route is %s." % (str(combo_ID), str(combo_ID[position]),)
    else:
        if position is 1:
            print "Checked the routes and combos: %s (use of 1 bus and 2 buses respectively). Best route is %s." % (str(combo_ID), str(combo_ID[position]))
        else:
            print "Checked the routes and combos: %s (use of 1 bus and 2 buses respectively). Best combination is %s." % (str(combo_ID), str(combo_ID[position]))
            return (combo_ID[position])
        
    return (combo_ID[position])

def make_swaps(requests):
    print "\nMaking swaps!\n"
    req1 = requests[0]
    req2 = requests[1]
    index = requests[2]
    
    reqs = [[req1, req2, index]]
    for i in range(len(req1)):
        for j in range(len(req2)):
            req1c = list(req1)
            req2c = list(req2)    
            req1c[i], req2c[j] = req2c[j], req1c[i]
            index += 1
            reqs.append([req1c, req2c, index])
    if len(req1) is not 1 and len(req2) is not 1:    
        for i in range(len(req1)):
            req1c = list(req1)
            req2c = list(req2)
            req2c.append(req1c[i])
            req1c.remove(req1c[i])
            index += 1
            reqs.append([req1c, req2c, index])

        for i in range(len(req2)):
            req1c = list(req1)
            req2c = list(req2)
            req1c.append(req2c[i])
            req2c.remove(req2c[i])
            index += 1
            reqs.append([req1c, req2c, index])        
    return reqs
    
def hill_climbing(requestsList, feasible_routes, feas_index):

    combo_ID = 0
    
    # DIVIDE REQUESTS INTO 2 BUSES:
    req1 = requestsList[:len(requestsList)/2]
    req2 = requestsList[len(requestsList)/2:]
    index = 0
    
    requests = [req1, req2, index]
    local_best = -2
    current_best = -1
    
    km_local_best = []
    delay_local_best = []
    
    while local_best is not current_best:
        local_best = current_best
        reqs = make_swaps(requests)
        for item in reqs:
            van1 = item[0]
            van2 = item[1]
            combo_ID = item[2]            # the ID that identifies the feasible routes for a certain swap
            with_two = rt.with_two_vans(requestsList, van1, van2, feasible_routes, feas_index, combo_ID)
            
            # UPDATE LIST feasible_routes, ROUTE INDEX feas_index AND combo_ID
            if with_two[0]:    
                feasible_routes = with_two[1]
                feas_index = with_two[2]
                combo_ID = with_two[3]
        if len(feasible_routes) >= 1 and feasible_routes[len(feasible_routes)-1].number_of_buses is 2:
            # ELIMINATE COMBOS:
            feasible_routes = eliminate_combos(feasible_routes)    
            

            # FIND LOCAL OPTIMAL:
            feasible_routes = choose_optimal_route(feasible_routes, 2)    
            for route in feasible_routes:
                if route.combo_ID is not None and route.optimal is True:
                    current_best = route.combo_ID
                    km_local_best.append(route.combo_km)
                    delay_local_best.append(route.combo_delay)
           
            # DELETE NON-OPTIMAL COMBOS:
            feasible_routes = delete_non_optimal_routes(feasible_routes)
           
            # UPDATE REQUESTS TO SWAP AGAIN:
            req1 = []
            req2 = []
            for route in feasible_routes:
                if route.is_first_bus():
                    for node in route.route_nodes:
                        request = node.match_request(requestsList)
                        if request not in req1:
                            req1.append(request)
                    
                elif route.is_second_bus():
                    for node in route.route_nodes:
                        request = node.match_request(requestsList)
                        if request not in req2:
                            req2.append(request)
                    index = route.combo_ID
            requests = [req1, req2, index]
 
        else:
            print "no combinations found :("
            return feasible_routes
      
    print "\nOptimal combination with 2 buses:"
    for route in feasible_routes:
        if route.optimal and route.combo_ID is not None:            
            print route       
    return feasible_routes

def print_combo(combos, combo_number):
    m = ''
    arrow = '->'
    box = '|'
    n = max(len(combos[0].route_nodes), len(combos[1].route_nodes))
    rows = [[] for _ in range(n)]
    outline = '+-----------------------------------------------------------------------------+'
    line = '-----------------------------------------------------------------------------'
    m += """
{space:10}-------------------> Optimal Combination: {number:<3} <-------------------\n\n
{outline}
| {box:>37}{box:>40}
| {space:13} Bus 1: {space:15}|{space:15} Bus 2: {space:15} |
| {box:>37}{box:>40}
""".format(space='', number=combo_number, outline=outline, box=box)
    bus = 1
    for combo in combos:
        for i, (node, time) in enumerate(zip(combo.route_nodes, combo.timeline)):    
            rows[i].append([bus, node, time])
        bus = 2
    for row in rows:
        for item in row:
            if item[0] is 1 and len(row) is 2:
                for i in item:
                    if type(i) is rt.Node:
                        m += "| " # left |
                        m += "{node:25} {arrow:3}".format(node=i, arrow=arrow)
                    elif type(i) is rq.MyTime:
                        m += "{time:5} ".format(time=i, space='')
                        m += ' {box:<3}'.format(box=box)  # center |
            elif item[0] is 1 and len(row) is 1:
                for i in item:
                    if type(i) is rt.Node:
                        m += "| " # left |
                        m += "{node:25} {arrow:3}".format(node=i, arrow=arrow)
                    elif type(i) is rq.MyTime:
                        m += "{time:5} ".format(time=i, space='')
                        m += ' {box:<3}{space:37}|\n'.format(box=box, space='')  # center and right |
            elif item[0] is 2 and len(row) is 2:
                for i in item:
                    if type(i) is rt.Node:
                        m += " {node:25} {arrow:3}".format(node=i, arrow=arrow)
                    elif type(i) is rq.MyTime:
                        m += "{time:3} ".format(time=i, space='')
                        m += "{box:>2}\n".format(box=box) # right |            
            elif item[0] is 2 and len(row) is 1:            
                for i in item:
                    if type(i) is rt.Node:
                        m += "|{space:36} |   {node:25} {arrow:3}".format(node=i, arrow=arrow, space='')
                    elif type(i) is rq.MyTime:
                        m += "{time:5} ".format(time=i, space='')

                        m += "{box:>2}\n".format(box=box) # right |                
    
    m += """| {box:>37}{box:>40}
|{line}|
|{space:29} Route Information:{box:>30}
| {box:>77}
|{space:20}Total kilometres travelled: {km:>6} km{box:>21}
|{space:20}Total customer waiting time: {time:3} mins{box:>21}
| {box:>77}
{outline}
""".format(line=line, box=box, space='', km=combos[0].combo_km, time=combos[0].combo_delay, outline=outline)    
    print m
    

def print_optimal(feasible_routes):
    combos = []
    combo_number = -1
    for route in feasible_routes:
        if route.combo_ID is None and route.optimal:
            print route
        elif route.combo_ID is not None and route.optimal is True:
            combos.append(route)
            combo_number = route.combo_ID
    if combo_number is not -1:
        print_combo(combos, combo_number)
    