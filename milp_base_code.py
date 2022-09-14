
from pyomo.environ import *
import pyomo
import pyomo.opt
import pyomo.environ as pe
import logging 
import pickle
import pandas as pd
import datetime, calendar
import numpy as np

import pandas as pd 

print('\n---------------------------------------------')
print('DATA PREP STARTED')

data = pd.DataFrame({'cols': ['a','a', 'b','b','b', 'c', 'c', 'c', 'c']
                    , 'key_col' : [f'c_{i}'for i in range(9)]
                     , 'val': [2,1,3,4,5,6,1,8,9]
                    })

base_data = data.copy()
master_key = ['cols', 'key_col']
data.set_index(master_key , inplace=True)

print(data)

cols_list = base_data['cols'].unique().tolist()
key_cols_list = base_data['key_col'].unique().tolist()


tm_key_set = data.index.unique()

# =============================================================================
# 
# =============================================================================
print('\n---------------------------------------------')
print('OPTIMIZATION EQUATIONS START')

m = pe.ConcreteModel() 

m.input_df      = pe.Set(initialize = tm_key_set , dimen = len(master_key))

m.cols  = pe.Set(initialize = cols_list)
m.key_cols  = pe.Set(initialize = key_cols_list)
# =============================================================================
# 
# =============================================================================


m.Y     = pe.Var(m.input_df, domain=pe.NonNegativeIntegers,bounds=(0,2))

# def obj_rule(m):
#     return (sum([((m.Y[e]*(data.loc[e, 'val']))-10)**2  for e in tm_key_set]))
def obj_rule(m):
    return (sum([m.Y[e]*data.loc[e, 'val']  for e in tm_key_set]))

m.OBJ = pe.Objective(rule=obj_rule, sense=pe.minimize)



def impact_push_show_l(m,j):
    return sum([m.Y[e] for e in tm_key_set if j == e[master_key.index('cols')]])==1    
m.impact_push_show_cl = pe.Constraint(m.cols, rule = impact_push_show_l)

# =============================================================================
# 
# =============================================================================

print('\n---------------------------------------------')
print('OPTIMIZATION SOLVER START')

# opt = pyo.SolverFactory('baron')
# opt = pe.SolverFactory('glpk')
opt = pe.SolverFactory('gurobi')

opt.solve(m) 


dec_var = [str(v) for v in m.component_objects(Var,active=True)]
print(dec_var)

print('\n---------------------------------------------')
print('OPTIMIZATION RESULT COMPILATION START')


for v in dec_var:
    #if str(v) == 'Y':
    varobject = getattr(m, str(v))
    print(v)
    print(varobject)
        
    opt_out = {}    
    key_id = list(tm_key_set.names)
    
    for id_num in range(0,len(key_id)):
        globals()['key_list_{}'.format(id_num)] =[]
    value_list = []
    
    for index in varobject:
        for id_num in range(0,len(key_id)):
            globals()['key_list_{}'.format(id_num)].append(index[id_num])
            
        value_list.append(varobject[index].value)
    
    for id_num in range(0,len(key_id)):            
        opt_out[key_id[id_num]] = globals()['key_list_{}'.format(id_num)]

    opt_out['value'] = value_list
    
    globals()['opt_out_df_'+v] = pd.DataFrame(opt_out)
    globals()['opt_out_df_'+v].set_index(master_key, inplace=True)
    globals()['opt_out_df_'+v].sort_index(inplace=True)

#==============================================================================
#
#    OPTIMIZATION COMPLETE THE CORRESPONIND DECISION VARIABLE COMPUTATION
#    
#==============================================================================

print('\n---------------------------------------------')
print('OPTIMIZATION RESULT MERGE WITH BASE DATA')

p = pd.merge(  opt_out_df_Y
             , data
             , left_index= True
             , right_index = True
             , how = 'left')
p['value'] = p['value'].apply(lambda x : int(x))

print(p)
print('\n---------------------------------------------')
