import numpy as np
import pandas as pd
import itertools
from ast import literal_eval

# Calculate Picker Route Distance between two locations
def distance_picking(Loc1, Loc2, x_low, x_high):

    # Start Point
    x1, y1 = Loc1[0], Loc1[1]
    # End Point
    x2, y2 = Loc2[0], Loc2[1]


    # Set x_low and x_high
    if (x1 <= 30) and (x2 < 30):
        x_high = 30
        x_high = 
    # Distance x-axis
    distance_y = abs(y2 - y1)
    # Distance y-axis
    if y1 == y2:
        distance_x1 = abs(x2 - x1)
        distance_x2 = distance_x1
    else:
        distance_x1 = (x_high - x1) + (x_high - x2)
        distance_x2 = (x1 - x_low) + (x2 - x_low)
    # Minimum distance on y-axis 
    distance_x = min(distance_x1, distance_x2)    
    # Total distance
    distance = distance_x + distance_y

    return distance

# Find closest next location 
def next_location(start_loc, list_locs, y_low, y_high):

    # Distance to every next points candidate
    list_dist = [distance_picking(start_loc, i, y_low, y_high) for i in list_locs]
    # Minimum Distance 
    distance_next = min(list_dist)
    # Location of minimum distance
    index_min = list_dist.index(min(list_dist))
    next_loc = list_locs[index_min] # Next location is the first location with distance = min (**)
    list_locs.remove(next_loc)      # Next location is removed from the list of candidates
    
    return list_locs, start_loc, next_loc, distance_next

# Calculate total distance to cover for a list of locations
def create_picking_route(origin_loc, list_locs, y_low, y_high):

    # Total distance variable
    wave_distance = 0
    # Current location variable 
    start_loc = origin_loc
    # Store routes
    list_chemin = []
    list_chemin.append(start_loc)
    
    while len(list_locs) > 0: # Looping until all locations are picked
        # Going to next location
        list_locs, start_loc, next_loc, distance_next = next_location(start_loc, list_locs, y_low, y_high)
        # Update start_loc 
        start_loc = next_loc
        list_chemin.append(start_loc)
        # Update distance
        wave_distance = wave_distance + distance_next 

    # Final distance from last storage location to origin
    wave_distance = wave_distance + distance_picking(start_loc, origin_loc, y_low, y_high)
    list_chemin.append(origin_loc)
    
    return wave_distance, list_chemin

# Mapping orders by wave number 
def orderlines_mapping(df_orderlines, orders_number):

	# Order dataframe by timeframe
	df_orderlines = df_orderlines.sort_values(by='TimeStamp', ascending = True)
	# Unique order numbers list
	list_orders = df_orderlines.OrderNumber.unique()
	# Dictionnary for mapping
	dict_map = dict(zip(list_orders, [i for i in range(1, len(list_orders))]))
	# Order ID mapping
	df_orderlines['OrderID'] = df_orderlines['OrderNumber'].map(dict_map)
	# Grouping Orders by Wave of orders_number 
	df_orderlines['WaveID'] = (df_orderlines.OrderID%orders_number == 0).shift(1).fillna(0).cumsum()
	# Counting number of Waves
	waves_number = df_orderlines.WaveID.max() + 1

	return df_orderlines, waves_number

# Getting storage locations to cover for a wave of orders
def locations_listing(df_orderlines, wave_id):

	# Filter by wave_id
	df = df_orderlines[df_orderlines.WaveID == wave_id]
	# Create coordinates listing
	list_locs = list(df['Coord'].apply(lambda t: literal_eval(t)).values)
	list_locs.sort()
	# Get unique Unique coordinates
	list_locs = list(k for k,_ in itertools.groupby(list_locs))
	n_locs = len(list_locs)

	return list_locs, n_locs