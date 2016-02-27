import numpy
import functools

from . import proportions


def target_func(target_value, initial_proportion, time_to_full_implementation,
                t):
    '''
    From the initial value initial_proportion,
    target_func goes linearly from initial_proportion to target_value
    in time_to_full_implementation years, then stays constant at
    target_value after that.
    '''
    return (initial_proportion
            + ((target_value - initial_proportion)
               * numpy.clip(t, 0, time_to_full_implementation)
               / time_to_full_implementation))


def get_target_funcs(target_values, parameters,
                     time_to_full_implementation = 5):
    initial_proportions = proportions.get_proportions(
        parameters.initial_conditions)

    if isinstance(target_values, str):
        if target_values == '909090':
            # Max of 90% and current the current level.
            target_values = initial_proportions.clip(0.9, None)
        elif target_values == 'base':
            # Fixed at initial values.
            target_values = initial_proportions
        elif target_values == 'nothing':
            target_funcs = [lambda x: numpy.zeros_like(x)
                            for i in range(3)]
            return target_funcs

    target_funcs = [functools.partial(target_func, v, p,
                                      time_to_full_implementation)
                    for (v, p) in zip(target_values, initial_proportions)]

    return target_funcs
