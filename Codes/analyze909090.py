#!/usr/bin/python3

'''
Analyze the 90-90-90 policies for all the countries.

See :func:`model.analyze909090.analyze909090`.
'''


if __name__ == '__main__':
    import pickle

    import model


    results = {}
    for country in model.get_country_list():
        results[country] = model.analyze909090(country)
        print()

    pickle.dump(results, open('analyze909090.pkl', 'wb'))
