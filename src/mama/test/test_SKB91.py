import unittest

import StringIO
import logging

from openmdao.util.testutil import assert_rel_error

from mama.orbit import Orbit
from mama.maneuver import Maneuver


class SKB91TestCase(unittest.TestCase):

    def setUp(self):
        # initialize 'mission' logger
        self.logger = logging.getLogger('mission')
        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        print self.logstr.getvalue()
        pass

    def test_SKB91(self):
        # (check against Borowski hand calcs dated 5/24/91)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/24/91 Ex #1, TLI from 407km circular orbit with C3 = -1 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 407
        LEO.periapsis = 407

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = -1
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 3.128, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/24/91 Ex #2, TLI from 481.5km circular orbit with C3 = 1.912 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 481.5
        LEO.periapsis = 481.5

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 1.912
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 3.247, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/24/91 Ex #2, TLI from 485km circular orbit with C3 = 1.912 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 485
        LEO.periapsis = 485

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 1.912
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 3.246, 0.005)

        #
        # McDDAC Lunar Shuttle Mission, "8-Burn Profile"
        # (check against Borowski hand calcs dated 5/27/91)
        #

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (1), LOI into 24hr lunar orbit')
        self.logger.info('    with apolune = 15.853 km, perilune = 111.12 km and C3 of 0.808 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        ELO = Orbit()
        ELO.body = 'Moon'
        ELO.apoapsis = 15853.12
        ELO.periapsis = 111.12

        maneuver = Maneuver()
        maneuver.orbit = ELO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.808
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -0.2815, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (1a), 30 deg plane change from 24hr lunar orbit')
        self.logger.info('    with apolune = 15.853 km, perilune = 111.12 km')
        self.logger.info('--------------------------------------------------------------------------------')
        ELO = Orbit()
        ELO.body = 'Moon'
        ELO.apoapsis = 15853.12
        ELO.periapsis = 111.12

        maneuver = Maneuver()
        maneuver.orbit = ELO
        maneuver.orbit.inclination = 30  # FIXME: quick&dirty hack, this is the maneuver not the orbit
        maneuver.maneuver_type = 'Plane Change'
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 0.119, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (2), circularize lunar orbit at periapsis starting at orbit')
        self.logger.info('    with apolune = 15.853 km, perilune = 111.12 km')
        self.logger.info('--------------------------------------------------------------------------------')
        ELO = Orbit()
        ELO.body = 'Moon'
        ELO.apoapsis = 15853.12
        ELO.periapsis = 111.12

        maneuver = Maneuver()
        maneuver.orbit = ELO
        maneuver.maneuver_type = 'Circularize at Periapsis'
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, .562, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (2), Trans Earth Injection with C3 of 1.486 km2/s2 from')
        self.logger.info('    24 hr lunar orbit with apolune = 15.853 km, perilune = 111.12 km ')
        self.logger.info('--------------------------------------------------------------------------------')
        LLO = Orbit()
        LLO.body = 'Moon'
        LLO.apoapsis = 15853.12
        LLO.periapsis = 111.12

        maneuver = Maneuver()
        maneuver.orbit = LLO
        maneuver.maneuver_type = 'Departure from Periapsis'
        maneuver.C3 = 1.486
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 0.415, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (3), EOC into 481.5 km circular Earth orbit with C3 of 1.378 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 481.5
        LEO.periapsis = 481.5

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 1.378
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -3.221, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (4), TLI from 481.5 km circular orbit with C3 = 1.912 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 481.5
        LEO.periapsis = 481.5

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.maneuver_type = 'Departure from Apoapsis'
        maneuver.C3 = 1.912
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 3.246, 0.005)

        #
        # "4-Burn" Lunar Shuttle Mission
        # (check against Borowski hand calcs dated 5/27/91)
        #

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (5), LOI into 111.12 km circular orbit with C3 = 0.808 km2/s2')
        self.logger.info('--------------------------------------------------------------------------------')
        LLO = Orbit()
        LLO.body = 'Moon'
        LLO.apoapsis = 111.12
        LLO.periapsis = 111.12

        maneuver = Maneuver()
        maneuver.orbit = LLO
        maneuver.maneuver_type = 'Capture at Periapsis'
        maneuver.C3 = 0.808
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, -0.844, 0.005)

        self.logger.info('--------------------------------------------------------------------------------')
        self.logger.info('SKB 5/27/91 (5), Trans Earth Injection with C3 of 1.486 km2/s2 from')
        self.logger.info('    24 hr lunar orbit with apolune = 15.853 km, perilune = 111.12 km ')
        self.logger.info('--------------------------------------------------------------------------------')
        LLO = Orbit()
        LLO.body = 'Moon'
        LLO.apoapsis = 111.12
        LLO.periapsis = 111.12

        maneuver = Maneuver()
        maneuver.orbit = LLO
        maneuver.maneuver_type = 'Departure from Periapsis'
        maneuver.C3 = 1.486
        dV = maneuver.calculate_dV()
        assert_rel_error(self, dV, 0.977, 0.005)


if __name__ == '__main__':
    unittest.main()
