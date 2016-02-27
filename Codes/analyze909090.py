#!/usr/bin/python3

import pickle

import model


results = {}
for country in model.get_country_list():
    results[country] = model.analyze909090(country)
    print()

pickle.dump(results, open('analyze909090.pkl', 'wb'))
