
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
                     , 'val': [20,10,30,40,50,60,10,80,90]
                    })

base_data = data.copy()
master_key = ['cols', 'key_col']
data.set_index(master_key , inplace=True)

print(data)
cols_list = ['cols']
cols_df = base_data[cols_list].drop_duplicates()
cols_df.set_index(cols_list, inplace=True)


key_cols_list = ['key_col']
key_cols_df = base_data[key_cols_list].drop_duplicates()
key_cols_df.set_index(key_cols_list, inplace=True)

tm_key_set = data.index.unique()


cols_list_df = pd.DataFrame({'':cols_list})

# =============================================================================
# 
# =============================================================================
print('\n---------------------------------------------')
print('OPTIMIZATION EQUATIONS START')

m = pe.ConcreteModel() 

m.input_df      = pe.Set(initialize = tm_key_set , dimen = len(master_key))

m.cols  = pe.Set(initialize = cols_df.index.unique())
m.key_cols  = pe.Set(initialize = key_cols_df.index.unique())
# =============================================================================
# 
# =============================================================================


m.Y      = pe.Var(m.input_df, domain=pe.NonNegativeIntegers,bounds=(0,2))
m.UB     = pe.Var(m.cols, domain=pe.NonNegativeIntegers,bounds=(1,100))
m.LB     = pe.Var(m.cols, domain=pe.NonNegativeIntegers,bounds=(1,100))

dict_dec_var = {'Y':tm_key_set
               , 'UB': cols_df.index.unique()
               , 'LB': cols_df.index.unique()}
key_dec_var = {'Y':master_key
               , 'UB': cols_list
               , 'LB': cols_df.index.unique()}



def obj_rule(m):
    return (sum([((m.Y[e]*(data.loc[e, 'val']))-10)**2  for e in tm_key_set]))
# def obj_rule(m):
#     return (sum([m.Y[e] for e in tm_key_set]))

m.OBJ = pe.Objective(rule=obj_rule, sense=pe.minimize)


def impact_push_show_l(m,j):
    return sum([m.Y[e] for e in tm_key_set if j == e[master_key.index('cols')]])==1    
m.impact_push_show_cl = pe.Constraint(m.cols, rule = impact_push_show_l)

def const_lb(m,j):
    return sum([m.Y[e]*(data.loc[e, 'val']) for e in tm_key_set if j == e[master_key.index('cols')]])*2== m.LB[j]    
m.const_lb = pe.Constraint(m.cols, rule = const_lb)

def const_ub(m,j):
    return sum([m.Y[e]*(data.loc[e, 'val']) for e in tm_key_set if j == e[master_key.index('cols')]])== m.UB[j]    
m.const_ub = pe.Constraint(m.cols, rule = const_ub)




# =============================================================================
# 
# =============================================================================

print('\n---------------------------------------------')
print('OPTIMIZATION SOLVER START')

# opt = pyo.SolverFactory('baron')
opt = pe.SolverFactory('gurobi')

opt.solve(m, keepfiles = True, tee=True) 


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
    
    ref_list = dict_dec_var[v]
    key_id = list(ref_list.names)
    print(key_id)
    
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
    globals()['opt_out_df_'+v].set_index(ref_list.names, inplace=True)
    globals()['opt_out_df_'+v].sort_index(inplace=True)

opt_out_df_Y
opt_out_df_LB
opt_out_df_UB
    
    
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
