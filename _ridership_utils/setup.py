from setuptools import find_packages, setup

# https://stackoverflow.com/questions/52630814/how-to-include-and-access-data-files-in-python-distribution
setup(
    name="ridership_utils",
    packages=find_packages(),
    version="0.1",
    description="Shared utility functions for transit-ridership-analytics repo",
    author="Cal-ITP",
    license="Apache",
    include_package_data=True,
    package_dir={"_ridership_utils": "ridership_utils"},
)