import setuptools


setuptools.setup(
    name='r',
    version='0.1',
    packages=['r'],
    entry_points=dict(
        console_scripts=['r = r:entry_point']),
    install_requires=['toml'])
