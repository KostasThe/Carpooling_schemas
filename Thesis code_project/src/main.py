import routefinder as rt
import request as rq
import optimal as opt
import time


if __name__ == "__main__":    
    feasible_routes = []
    feas_index = 0
    combos = []

    program_start = time.clock()
    requests = rq.makeRequest()
    rq.printRequests(requests)
    requests_end = time.clock()

    # FIND FEASIBLE WITH ONE BUS:
    with_one = rt.with_one_van(requests, feasible_routes, feas_index)
    calc_routes_1_end = time.clock()
    if with_one[0]:            
        feasible_routes = with_one[1]
        feas_index = with_one[2]
        print "Printing the optimal route with 1 bus...\n"
    feasible_routes = opt.choose_optimal_route(feasible_routes, 1)
    opt.print_optimal(feasible_routes)
    
    # FIND FEASIBLE WITH TWO BUSES:
    feasible_routes = opt.hill_climbing(requests, feasible_routes, feas_index)

    # CHOOSE BETWEEN 1 OR 2 BUSES
    for route in feasible_routes:
        if route.is_with_one_bus() and route.optimal:
            feasible_routes = opt.choose_optimal_route(feasible_routes, "both")
            
    program_end = time.clock()
    if len(feasible_routes) >= 1:
        print "Printing the final optimal route/combination...\n"
        opt.print_optimal(feasible_routes)
    print "Total speed: ", program_end - program_start