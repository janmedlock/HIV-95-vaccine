#!/usr/bin/python3

import sys
sys.path.append('..')

import model


country = 'Nigeria'

# 0 is just cost.
# inf is just QALYs.
# Other values are multiples of per-capita GDP.
CE_threshold = 1

(target_values,
 incremental_effectiveness,
 incremental_cost,
 incremental_net_benefit) = model.maximize_incremental_net_benefit(
     country,
     CE_threshold,
     method = 'cobyla',
     debug = True)

print('target values = {}'.format(target_values))

print('incremental effectiveness = {:g} QALYs gained'.format(
    incremental_effectiveness))
print('incremental cost = {:g} USD'.format(incremental_cost))
print('incremental net benefit = {:g} QALYs'.format(
    incremental_net_benefit))
