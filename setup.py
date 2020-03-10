from setuptools import setup, find_packages


requirements = [l.strip() for l in open('requirements.txt').readlines()]


setup(
    name="YNAB_Sync-Norge",
    version="1.1.0",
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,

    # metadata for upload to PyPI
    author="Filip Fog",
    description="Base function for YNAB_Sync-Norge",
    license="GPL-2.0",
    keywords="ynab sync norge base",
    url="https://github.com/hanfil/YNAB_Sync-Norge",
)