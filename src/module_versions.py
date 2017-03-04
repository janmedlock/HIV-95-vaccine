#!/usr/bin/python3
'''
Record the versions of all external modules used.
'''

import importlib
import modulefinder
import os
import platform
import sys


root_path = '.'


def _is_executable(path):
    return os.access(path, os.X_OK)


def _get_scripts():
    mypath = os.path.relpath(__file__)
    scripts = []
    for (root, dirs, files) in os.walk(root_path):
        for f in files:
            path = os.path.relpath(os.path.join(root, f))
            if (path.endswith('.py')
                and _is_executable(path)
                and (path != mypath)):
                    scripts.append(path)
    return scripts


def _get_base(name):
    i = name.find('.')
    if i == -1:
        return name
    else:
        return name[ : i]


_builtin_path = os.path.join(sys.prefix,
                             'lib',
                             'python{ver[0]}.{ver[1]}'.format(
                                 ver = platform.python_version_tuple()))

def _is_builtin(name):
    if name in sys.builtin_module_names:
        return True
    else:
        mod = importlib.import_module(name)
        return (_builtin_path in mod.__file__)


def _is_local(name):
    mod = importlib.import_module(name)
    return (os.path.abspath(root_path) in mod.__file__)


def _get_version(name):
    mod = importlib.import_module(name)
    for attr in ('__version__', '__VERSION__', 'version', 'VERSION'):
        if hasattr(mod, attr):
            return getattr(mod, attr)
    else:
        return None


def _main():
    scripts = _get_scripts()

    finder = modulefinder.ModuleFinder()
    for script in scripts:
        print('Analyzing {}.'.format(script))
        try:
            finder.run_script(script)
        except ImportError:
            print("Script '{}' failed.".format(script))

    bases = set(_get_base(name) for name in finder.modules.keys())

    basename, _ = os.path.splitext(__file__)
    outputfile = '{}.txt'.format(basename)
    with open(outputfile, 'wt') as fd:
        fd.write('python, {}\n'.format(platform.python_version()))
        for name in sorted(bases):
            if (not name.startswith('_')
                 and not _is_builtin(name)
                 and not _is_local(name)):
                version = _get_version(name)
                fd.write('{}, {}\n'.format(name, version))


if __name__ == '__main__':
    _main()
