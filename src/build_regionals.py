#!/usr/bin/python3
'''
Update the global and regional results.
'''

import model


def _main():
    for region in model.regions.all_:
        for target in model.target.all_:
            if not model.results.exists(region, target):
                print('{}: {}'.format(region, target))
                data = {country: model.results.load(country, target)
                        for country in model.regions.regions[region]}
                if region == 'Global':
                    results = model.multicountry.Global(target, data)
                else:
                    results = model.multicountry.MultiCountry(region,
                                                              target,
                                                              data)
                model.results.dump(results)


if __name__ == '__main__':
    _main()
