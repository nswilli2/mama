import unittest

import StringIO
import logging

from openmdao.util.testutil import assert_rel_error

from mama.orbit import Orbit
from mama.maneuver import Maneuver


class SKB12TestCase(unittest.TestCase):

    def setUp(self):
        # initialize 'mission' logger
        self.logger = logging.getLogger('mission')
        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        print self.logstr.getvalue()
        pass

    def test_SKB12(self):
        # check against Borowski hand calcs dated 9/17/12

        # define Orbits
        LEO_407 = Orbit()
        LEO_407.body = 'Earth'
        LEO_407.apoapsis = 407
        LEO_407.periapsis = 407

        LEO_500 = Orbit()
        LEO_500.body = 'Earth'
        LEO_500.apoapsis = 500
        LEO_500.periapsis = 500

        LEO_700 = Orbit()
        LEO_700.body = 'Earth'
        LEO_700.apoapsis = 700
        LEO_700.periapsis = 700

        MEO = Orbit()
        MEO.body = 'Mars'
        MEO.apoapsis = 250
        MEO.periapsis = 33840

        HEEO = Orbit()
        HEEO.body = 'Earth'
        HEEO.apoapsis = 71136
        HEEO.periapsis = 500

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12 (1), EOC into HEEO with Vinf = 0.855 km/s (from 2000SG344)')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = HEEO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.855**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -0.482, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12 (1), EOC into HEEO with Vinf = 5.882 km/s (from Apophis)')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = HEEO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 5.882**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -1.950, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12 (2), EOC into LEO_500 with Vinf = 0.855 km/s (from 2000SG344)')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = LEO_500
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.855**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -3.187, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12 (2), EOC into LEO_407 with Vinf = 0.855 km/s (from 2000SG344)')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = LEO_407
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.855**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -3.208, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12 (3), EOC into LEO_500 with Vinf = 5.882 km/s (from Apophis)')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = LEO_500
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 5.882**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -4.655, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12 (3), EOC into LEO_407 with Vinf = 5.882 km/s (from Apophis)')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = LEO_407
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 5.882**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -4.668, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12 (4), EOC into LEO_700 with Vinf = 0.855 km/s (from 2000SG344)')
        self.logger.info('--------------------------------------------------------------------------------')
        maneuver = Maneuver()
        maneuver.orbit = LEO_700
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.855**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -3.143, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12, EOC into 6 hour EEO with Vinf = 0.855 km/s (from 2000SG344)')
        self.logger.info('--------------------------------------------------------------------------------')

        EEO = Orbit()
        EEO.body = 'Earth'
        EEO.apoapsis = 20238
        EEO.periapsis = 500

        # check the derivation of the 6hr orbit
        self.logger.info(EEO.orbit_from_period(6*3600, 500))

        maneuver = Maneuver()
        maneuver.orbit = EEO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.855**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -1.203, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12, EOC into 9 hour EEO with Vinf = 0.855 km/s (from 2000SG344)')
        self.logger.info('--------------------------------------------------------------------------------')

        EEO = Orbit()
        EEO.body = 'Earth'
        EEO.apoapsis = 30633
        EEO.periapsis = 500

        # check the derivation of the 9hr orbit
        self.logger.info('(calculated periapsis=%1.1f, apoapsis=%1.1f)' % EEO.orbit_from_period(9*3600, 500))

        maneuver = Maneuver()
        maneuver.orbit = EEO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.855**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -0.914, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 9/17/12, EOC into 12 hour EEO with Vinf = 0.855 km/s (from 2000SG344)')
        self.logger.info('--------------------------------------------------------------------------------')

        EEO = Orbit()
        EEO.body = 'Earth'
        EEO.apoapsis = 39910
        EEO.periapsis = 500

        # check the derivation of the 9hr orbit
        self.logger.info('(calculated periapsis=%1.1f, apoapsis=%1.1f)' % EEO.orbit_from_period(12*3600, 500))

        maneuver = Maneuver()
        maneuver.orbit = EEO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.855**2
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -0.755, 0.005)


if __name__ == '__main__':
    unittest.main()
