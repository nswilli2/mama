import unittest

import StringIO
import logging

from openmdao.util.testutil import assert_rel_error

from mama.maneuver import *


class SKB00TestCase(unittest.TestCase):

    def setUp(self):
        # initialize 'mission' logger
        self.logger = logging.getLogger('mission')
        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        print self.logstr.getvalue()
        pass

    def test_SKB00(self):
        # "90 Day" Study LeRC Data *All Propulsive Optimized Trajectory
        # 2016 Opposition Mars Mission
        # (check against Borowski hand calcs dated 6/30/00)

        # define Orbits
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 407
        LEO.periapsis = 407

        MEO = Orbit()
        MEO.body = 'Mars'
        MEO.apoapsis = 250
        MEO.periapsis = 33840

        HEEO = Orbit()
        HEEO.body = 'Earth'
        HEEO.apoapsis = 71136
        HEEO.periapsis = 500

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 6/30/00 2016 Opposition (1), TMI from LEO with C3 = 14.06 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 14.06
        dV_TMI = maneuver.calculate_dV()
        assert_rel_error(self, dV_TMI, 3.805, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 6/30/00 2016 Opposition (2), MOC into MEO with Vinf = 5.31 km/s')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = MEO
        maneuver.maneuver_type = 'Capture at Apoapsis'
        maneuver.C3 = 5.31**2
        dV_MOC = maneuver.calculate_dV()
        assert_rel_error(self, dV_MOC, -2.563, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 6/30/00 2016 Opposition (3) TEI from MEO with C3 = 50.552 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = MEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 50.552
        dV_TEI = maneuver.calculate_dV()
        assert_rel_error(self, dV_TEI, 3.978, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 6/30/00 2016 Opposition (4), EOC into HEEO with Vinf = 5.56 km/s')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = HEEO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 5.56**2
        dV_EOC = maneuver.calculate_dV()
        assert_rel_error(self, dV_EOC, -1.799, 0.005)

        total_dV = abs(dV_TMI) + abs(dV_MOC) + abs(dV_TEI) + abs(dV_EOC)
        self.logger.info('Total Ideal Delta V = '+str(total_dV))
        assert_rel_error(self, total_dV, 12.145, 0.005)


if __name__ == '__main__':
    unittest.main()
