#
# This file is autogenerated during plugin quickstart and overwritten during
# plugin makedist. DO NOT CHANGE IT if you plan to use plugin makedist to update 
# the distribution.
#

from setuptools import setup, find_packages

kwargs = {'author': '',
 'author_email': '',
 'classifiers': ['Intended Audience :: Science/Research',
                 'Topic :: Scientific/Engineering'],
 'description': '',
 'download_url': '',
 'entry_points': u'[openmdao.component]\nmama.subsystem.Summation=mama.subsystem:Summation\nmama.maneuver.Maneuver=mama.maneuver:Maneuver\nmama.spacecraft.Spacecraft=mama.spacecraft:Spacecraft\nmama.mission.Mission=mama.mission:Mission\nmama.maneuver.Orbit=mama.maneuver:Orbit\nmama.subsystem.Subsystem=mama.subsystem:Subsystem\nmama.mission.Phase=mama.mission:Phase\nmama.spacecraft.Stage=mama.spacecraft:Stage\nmama.subsystems.CargoSubsystem=mama.subsystems:CargoSubsystem\n\n[openmdao.container]\nmama.subsystem.Summation=mama.subsystem:Summation\nmama.maneuver.Maneuver=mama.maneuver:Maneuver\nmama.spacecraft.Spacecraft=mama.spacecraft:Spacecraft\nmama.mission.Mission=mama.mission:Mission\nmama.maneuver.Orbit=mama.maneuver:Orbit\nmama.subsystem.Subsystem=mama.subsystem:Subsystem\nmama.mission.Phase=mama.mission:Phase\nmama.spacecraft.Stage=mama.spacecraft:Stage\nmama.subsystems.CargoSubsystem=mama.subsystems:CargoSubsystem',
 'include_package_data': True,
 'install_requires': ['openmdao.main'],
 'keywords': ['openmdao'],
 'license': '',
 'maintainer': '',
 'maintainer_email': '',
 'name': 'mama',
 'package_data': {'mama': ['sphinx_build/html/genindex.html',
                           'sphinx_build/html/srcdocs.html',
                           'sphinx_build/html/pkgdocs.html',
                           'sphinx_build/html/index.html',
                           'sphinx_build/html/objects.inv',
                           'sphinx_build/html/.buildinfo',
                           'sphinx_build/html/py-modindex.html',
                           'sphinx_build/html/search.html',
                           'sphinx_build/html/searchindex.js',
                           'sphinx_build/html/usage.html',
                           'sphinx_build/html/_static/basic.css',
                           'sphinx_build/html/_static/pygments.css',
                           'sphinx_build/html/_static/comment-close.png',
                           'sphinx_build/html/_static/ajax-loader.gif',
                           'sphinx_build/html/_static/default.css',
                           'sphinx_build/html/_static/comment.png',
                           'sphinx_build/html/_static/jquery.js',
                           'sphinx_build/html/_static/doctools.js',
                           'sphinx_build/html/_static/down-pressed.png',
                           'sphinx_build/html/_static/down.png',
                           'sphinx_build/html/_static/up.png',
                           'sphinx_build/html/_static/websupport.js',
                           'sphinx_build/html/_static/comment-bright.png',
                           'sphinx_build/html/_static/searchtools.js',
                           'sphinx_build/html/_static/minus.png',
                           'sphinx_build/html/_static/underscore.js',
                           'sphinx_build/html/_static/up-pressed.png',
                           'sphinx_build/html/_static/sidebar.js',
                           'sphinx_build/html/_static/file.png',
                           'sphinx_build/html/_static/plus.png',
                           'sphinx_build/html/_sources/srcdocs.txt',
                           'sphinx_build/html/_sources/pkgdocs.txt',
                           'sphinx_build/html/_sources/usage.txt',
                           'sphinx_build/html/_sources/index.txt',
                           'sphinx_build/html/_modules/index.html',
                           'sphinx_build/html/_modules/mama/mission.html',
                           'sphinx_build/html/_modules/mama/mga.html',
                           'sphinx_build/html/_modules/mama/tank.html',
                           'sphinx_build/html/_modules/mama/maneuver.html',
                           'sphinx_build/html/_modules/mama/subsystems.html',
                           'sphinx_build/html/_modules/mama/spacecraft.html',
                           'sphinx_build/html/_modules/mama/subsystem.html',
                           'sphinx_build/html/_modules/mama/test/test_SKB00.html',
                           'sphinx_build/html/_modules/mama/test/test_SKB92.html',
                           'sphinx_build/html/_modules/mama/test/test_tank.html',
                           'sphinx_build/html/_modules/mama/test/test_SKB13.html',
                           'sphinx_build/html/_modules/mama/test/test_SKB12.html',
                           'sphinx_build/html/_modules/mama/test/test_SKB91.html',
                           'sphinx_build/html/_modules/mama/test/test_gravloss.html',
                           'test/test_SKB13.py',
                           'test/test_gravloss.py',
                           'test/test_SKB12.py',
                           'test/test_SKB91.py',
                           'test/__init__.py',
                           'test/test_SKB00.py',
                           'test/test_SKB92.py',
                           'test/test_tank.py']},
 'package_dir': {'': 'src'},
 'packages': ['mama', 'mama.test'],
 'url': '',
 'version': '0.1',
 'zip_safe': False}


setup(**kwargs)

