from setuptools import setup

setup(
    name='mmquery',
    version='0.1',
    py_modules=['mmquery'],
    install_requires=[
        'Click',
        'mattermostdriver',
    ],
    entry_points='''
        [console_scripts]
        mmquery=mmquery:cli
    ''',
)