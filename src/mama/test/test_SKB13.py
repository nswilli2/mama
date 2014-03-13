import unittest

import StringIO
import logging

from openmdao.util.testutil import assert_rel_error

from mama.maneuver import *


class SKB13TestCase(unittest.TestCase):

    def setUp(self):
        # initialize 'mission' logger
        self.logger = logging.getLogger('mission')
        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        print self.logstr.getvalue()
        pass

    def test_SKB13(self):
        # Borowski notes dated 3/17/13
        # check against Laura Burke results in e-mail dated 9/20/12

        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.periapsis = 407
        LEO.apoapsis = 407
        LEO.inclination = 28.5

        HEEO_24hr = Orbit()
        HEEO_24hr.body = 'Earth'
        HEEO_24hr.periapsis = 500
        HEEO_24hr.apoapsis = 71136

        HEEO_48hr = Orbit()
        HEEO_48hr.body = 'Earth'
        HEEO_48hr.periapsis = 500
        HEEO_48hr.apoapsis = 120702

        LLO_110 = Orbit()
        LLO_110.body = 'Moon'
        LLO_110.periapsis = 110
        LLO_110.apoapsis = 110

        LLO_300 = Orbit()
        LLO_300.body = 'Moon'
        LLO_300.periapsis = 300
        LLO_300.apoapsis = 300

        # data to be provided by laura burke


if __name__ == '__main__':
    unittest.main()
