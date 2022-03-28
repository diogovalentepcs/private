from __future__ import division
from os import set_inheritable
import six
import sys
sys.modules['sklearn.externals.six'] = six
import mlrose
import numpy as np
import random
from gsheetcoms import GSH
import pandas as pd

class RouteOptimzer():

    ##########################################
    # Default Values
    #########################################
    _WORKBOOK = 'RoutingModel'
    _TEMP_SKU_DICT = {}

    ##########################################
    # Googel Sheet Communication / Fetch Tables as Dataframes
    #########################################
    _GSH = GSH()
    print('Fetching data...')
    _ASSUMPTIONS = _GSH.generateDataframe(_WORKBOOK, 'Assumptions')
    _ORDERS = _GSH.generateDataframe(_WORKBOOK, 'Orders')
    _SKUS = _GSH.generateDataframe(_WORKBOOK, 'SKUs')
    _ORDERS_SKUS = _GSH.generateDataframe(_WORKBOOK, 'Orders_SKUs')
    _LAYOUT = _GSH.generateDataframe(_WORKBOOK, 'Layout')

    ##########################################
    # General Assumptions
    #########################################
    print('Setting Assumptions...')
    _STABILIZE_TIME = int(_ASSUMPTIONS.loc[_ASSUMPTIONS['Assumption'] == 'Stabilize Time'].iloc[0]['Value'])
    _PICKING_TIME = int(_ASSUMPTIONS.loc[_ASSUMPTIONS['Assumption'] == 'Picking Time'].iloc[0]['Value'])
    _PICKER_SPEED = int(_ASSUMPTIONS.loc[_ASSUMPTIONS['Assumption'] == 'Picker Speed'].iloc[0]['Value'])
    _PICKER_COST = int(_ASSUMPTIONS.loc[_ASSUMPTIONS['Assumption'] == 'Picker Cost'].iloc[0]['Value'])
    _STABILIZE_TIME = int(_ASSUMPTIONS.loc[_ASSUMPTIONS['Assumption'] == 'Stabilize Time'].iloc[0]['Value'])

    ##########################################
    # Layout Specific Assumptions
    #########################################
    _X_LIMIT= _ASSUMPTIONS.loc[_ASSUMPTIONS['Assumption'] == 'X Limit'].iloc[0]['Value']
    _X_MIDDLE= _ASSUMPTIONS.loc[_ASSUMPTIONS['Assumption'] == 'X Middle'].iloc[0]['Value']


    #########################################
    # Constructor and Destroyer
    #########################################
    def __init__(self):
        pass
    
    def __del__(self):
        pass


    # Define alternative N-Routes fitness function for minimization problem (fitness = count)
    def route_min_cost(self, state_input):

        # Prevent Duplicate states
        unique = np.unique(state_input, return_inverse=True, return_counts=True)
        if len(unique) < len(state_input):
            return 10^12

        state = state_input
        #insert initial operator position in state, each state value is the sku ID, and ID = 0 is the inital position
        state = np.insert(state, 0, 0, axis=0)
        
        #insert final operator position in state, each state value is the sku ID, and ID = 0 is the final position
        state = np.append(state, 0)

        # Initialize time tracker (s)
        time = 0


        for i in range(1, len(state) - 1):
            # Calculate travel disctance time
            if i == 1:
                sku1 = 0
                sku2 = int(self._TEMP_SKU_DICT[state[i]] )
            elif i == len(state):
                sku2 = 0
                sku1 = int(self._TEMP_SKU_DICT[state[i-1]])
            else:
                sku1 = int(self._TEMP_SKU_DICT[state[i-1]] )
                sku2 = int(self._TEMP_SKU_DICT[state[i]] )
            
            time += self.distance_calculator(sku1,sku2) / self._PICKER_SPEED

            # Add picking time
            time += self._PICKING_TIME

            # Check for weight adjustment
            if i < len(state) and i >  1:
                if (self.get_weight(sku2) > self.get_weight(sku1)):
                    time += self._STABILIZE_TIME

        # Operator Cost
        cost = time * self._PICKER_COST

        return cost

    def cellInfo(self, cell_id):
        cell_id = str(cell_id)
        info = {
            'Cell_ID' : cell_id,
            'SKU_ID' : self._LAYOUT.loc[self._LAYOUT['Cell_ID'] == cell_id].iloc[0]['SKU_ID'],
            'x'  : self._LAYOUT.loc[self._LAYOUT['Cell_ID'] == cell_id].iloc[0]['X'],
            'y'  : self._LAYOUT.loc[self._LAYOUT['Cell_ID'] == cell_id].iloc[0]['Y'],
            'direction'  : self._LAYOUT.loc[self._LAYOUT['Cell_ID'] == cell_id].iloc[0]['Direction']
        }
        return info

    # Calculate Picker Route Distance between two locations

    def distance_calculator(self, cell1, cell2):
        distance = 0
        try:
            pos1 = self.cellInfo(cell1)
            pos2 = self.cellInfo(cell2)
            # Start Point
            x1 = int(pos1['x'])
            y1 = int(pos1['y'])
            direction1 = int(pos1['direction'])

            # End Point
            x2 = int(pos2['x'])
            y2 = int(pos2['y'])
            direction2 = int(pos2['direction'])

            # Distance y-axis
            distance_y = abs(y2 - y1)

            # Distance x-axis
            distance_x = 0
            x_low = 1
            x_passage = int(self._X_MIDDLE)
            x_limit = int(self._X_LIMIT)

            # If locations are in same corridor:
            if y1 == y2:
                distance_x = abs(x2 - x1)
            else:
                if direction1 == 1:
                    if x1 <= x_passage:
                        if direction1 == direction2:
                            if x2 <= x_passage:
                                distance_x = x_passage - x1 + x_passage + x2
                            else:
                                distance_x = x2 - x1
                        else:
                            if x2 <= x_passage:
                                distance_x = x_passage - x1 + x_passage - x2
                            else:
                                distance_x = x_limit - x1 + x_limit - x2		
                    else:
                        if direction1 == direction2:
                            if x2 <= x_passage:
                                distance_x = x_limit - x1 + x_limit + x2
                            else:
                                distance_x = x_limit - x1 + x2
                        else:
                            distance_x = x_limit - x1 + x_limit - x2
                else:
                    if x1 <= x_passage:
                        if direction1 == direction2:
                            if x2 <= x_passage:
                                distance_x = x1 + x_passage + x_passage - x2

                            else:
                                distance_x = x1 + x_limit + x_limit - x2
                        else:
                                distance_x = x1 + x2
                    else:
                        if direction1 == direction2:
                            if x2 <= x_passage:
                                distance_x = x1 - x2
                            else:
                                distance_x = x1 + x_limit - x2
                        else:
                            if x2 <= x_passage:
                                distance_x = x1 + x2
                            else:
                                distance_x = x1 - x_passage + x2 - x_passage
                ############
        
            # Total distance
            distance = distance_x + distance_y
            
        except:
            distance = 0
        
        finally:
            return distance

    def get_weight(self, sku):
        sku = str(sku)
        resp = self._SKUS.loc[self._SKUS['SKU_ID'] == sku].iloc[0]['Weight']
        return resp

    def runOptimization(self, order_id):
        # Initialize custom fitness function object
        print("Creating Minimization Function... ")
        custom_fitness = mlrose.CustomFitness(self.route_min_cost)

        print("Defining Optimization Problem... ")
        n_states = int(self._ORDERS.loc[self._ORDERS['Order_ID'] == order_id].iloc[0]['NDif_Pos'])
        # Initialize optimization problem
        problem = mlrose.DiscreteOpt(length = n_states, fitness_fn = custom_fitness, maximize = False, max_val = n_states)
        print(f'Route Optimizationfor Order ID: {order_id}')

        # Turn positions into integers and Define initial state
        skus_in_order_df = self._ORDERS_SKUS.loc[self._ORDERS_SKUS['Order_ID'] == order_id]
        init_state = []
        self._TEMP_SKU_DICT = {}
        for i in range(0, n_states):
            init_state.append(i)
            self._TEMP_SKU_DICT[i] = skus_in_order_df.iloc[i]['SKU_ID']
        init_state = np.array(init_state)
        print(f'Initial State: {init_state}')


        # Define decay schedule
        schedule = mlrose.ExpDecay()
        print("Solving Optimization Problem...")
        # Solve problem using simulated annealing
        best_state, best_fitness = mlrose.simulated_annealing(problem, schedule = schedule,  max_attempts = 100, max_iters = 10000, init_state = init_state, random_state = 1)
        #best_state, best_fitness = mlrose.genetic_alg(problem, mutation_prob = 0.2,  max_attempts = 1, max_iters = 1, random_state = 1)

        # Get SKU order from State array
        best_state_skus = []
        for item in best_state:
            best_state_skus.append(self._TEMP_SKU_DICT[item])

        print('Problem Solved Successfully!')
        print(f'Best State: {best_state_skus}')
        print(f'Min Cost (€): {best_fitness}')
        return best_state_skus, best_fitness
    
    def total_cost(self):

        total_cost = 0

        # Repleneshing Cost
        repleneshing_cost = 0
        for index, sku in self._SKUS.iterrows():
            time_spent = 0
            if int(sku['N_Pallets_Needed']) > 1:
                # Froklift up, down and repleneshing
                time_spent += int(self._ASSUMPTIONS.loc[self._ASSUMPTIONS['Assumption'] == 'Forklift Time'].iloc[0]['Value']) * 2 # Forklift Up and Down
                time_spent += int(self._ASSUMPTIONS.loc[self._ASSUMPTIONS['Assumption'] == 'Pallet Replenish Time'].iloc[0]['Value'])
                time_spent = time_spent / 60 # Mins to hours
                # Forklift Operator moving to postion and back 
                cell1 = '0' #initial position
                cell2 =  str(self._LAYOUT.loc[self._LAYOUT['SKU_ID'] == sku['SKU_ID']].iloc[0]['Cell_ID']) #sku position
                distance = self.distance_calculator(cell1, cell2) * 2 / 1000 #back and forth and in km
                time_spent = distance * int(self._ASSUMPTIONS.loc[self._ASSUMPTIONS['Assumption'] == 'Picker Speed'].iloc[0]['Value'])
                repleneshing_cost += time_spent * int(self._ASSUMPTIONS.loc[self._ASSUMPTIONS['Assumption'] == 'Forklift Operator Cost'].iloc[0]['Value'])
        print(f'Repleneshing Cost: {repleneshing_cost}')
        
        # Picking Pallet Preparation
        picking_setup_cost = int(self._ASSUMPTIONS.loc[self._ASSUMPTIONS['Assumption'] == 'Picking Setup Cost'].iloc[0]['Value']) * self._ORDERS['Pallet_Qty'].sum()

        total_cost += repleneshing_cost
        return total_cost
        

optimizer = RouteOptimzer()
best_state_skus, best_fitness = optimizer.runOptimization('1056')
total_cost = optimizer.total_cost()
