#!/usr/bin/python3

import datasheet
import simulation


def analyze909090(country):
    print('{}'.format(country))

    parameters = datasheet.Parameters(country)

    qalys_909090, cost_909090 = simulation.solve_and_get_qalys_and_cost(
        '909090', parameters)

    qalys_base, cost_base = simulation.solve_and_get_qalys_and_cost(
        'base', parameters)

    incremental_qalys = qalys_909090 - qalys_base
    incremental_cost = cost_909090 - cost_base
    ICER = incremental_cost / incremental_qalys

    print('incremental effectiveness = {:g} QALYs gained'.format(
        incremental_qalys))
    print('incremental cost = {:g} USD'.format(incremental_cost))
    print('incremental cost = {:g} GDP per capita'.format(
        incremental_cost / parameters.GDP_per_capita))
    print('ICER = {:g} USD per QALY averted'.format(ICER))
    print('ICER = {:g} GDP per capita per QALY averted'.format(
        ICER / parameters.GDP_per_capita))

    return ICER / parameters.GDP_per_capita


if __name__ == '__main__':
    results = {}
    for country in datasheet.get_country_list():
        results[country] = analyze909090(country)
        print()
