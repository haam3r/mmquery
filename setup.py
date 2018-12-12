from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='mmquery',
    version='0.2',
    author="haam3r",
    description="CLI utility to query MatterMost API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/haam3r/mmquery",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'Click',
        'mattermostdriver',
        'tabulate',
    ],
    entry_points='''
        [console_scripts]
        mmquery=mmquery.mmquery:cli
    ''',
)
