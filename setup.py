from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in sg_slack_integration/__init__.py
from sg_slack_integration import __version__ as version

setup(
	name="sg_slack_integration",
	version=version,
	description="Slack Integration for SG",
	author="8848 Digital",
	author_email="rohitkumar8848@digital.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
