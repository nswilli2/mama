import unittest

import StringIO
import logging

from openmdao.util.testutil import assert_rel_error

from mama.maneuver import *


class SKB92TestCase(unittest.TestCase):

    def setUp(self):
        # initialize 'mission' logger
        self.logger = logging.getLogger('mission')
        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        print self.logstr.getvalue()
        pass

    def test_SKB92(self):
        # (check against Borowski hand calcs dated 10/9/92)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 10/9/92 2007 Cargo (1), TMI from 407km circular orbit with C3 = 13.41 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 407
        LEO.periapsis = 407

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 13.41
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 3.776, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 10/9/92 2007 Cargo (2), MOC into 250km x 33840km orbit with C3 = 6.35 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        MEO = Orbit()
        MEO.body = 'Mars'
        MEO.apoapsis = 250
        MEO.periapsis = 33840

        maneuver = Maneuver()
        maneuver.orbit = MEO
        maneuver.maneuver_type = 'Capture at Apoapsis'
        maneuver.C3 = 6.35
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -0.837, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 10/9/92 2009 Tanker (1) TMI from 407km circular orbit with C3 = 10.30 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 407
        LEO.periapsis = 407

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 10.30
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 3.640, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 10/9/92 2009 Tanker (2) MOC into 250km x 33840km orbit with C3 = 6.10 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        MEO = Orbit()
        MEO.body = 'Mars'
        MEO.apoapsis = 250
        MEO.periapsis = 33840

        maneuver = Maneuver()
        maneuver.orbit = MEO
        maneuver.maneuver_type = 'Capture at Apoapsis'
        maneuver.C3 = 6.10
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -0.814, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 10/9/92 2009 Crew (1) TMI from 407km circular orbit with C3 = 30.65 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 407
        LEO.periapsis = 407

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 30.65
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 4.506, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 10/9/92 2009 Crew (2) MOC into 250km x 33840km orbit with C3 = 6.10 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        MEO = Orbit()
        MEO.body = 'Mars'
        MEO.apoapsis = 250
        MEO.periapsis = 33840

        maneuver = Maneuver()
        maneuver.orbit = MEO
        maneuver.maneuver_type = 'Capture at Apoapsis'
        maneuver.C3 = 27.40
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -2.508, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 10/9/92 2009 Crew (3) TEI from 250km x 33840km orbit with C3 = 17.31 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        MEO = Orbit()
        MEO.body = 'Mars'
        MEO.apoapsis = 250
        MEO.periapsis = 33840

        maneuver = Maneuver()
        maneuver.orbit = MEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 17.31
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 1.762, 0.005)


if __name__ == '__main__':
    unittest.main()
