import unittest

import StringIO
import logging

from mama.orbit import Orbit
from mama.maneuver import Maneuver


class GravLossTestCase(unittest.TestCase):

    def setUp(self):
        # initialize 'mission' logger
        self.logger = logging.getLogger('mission')
        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        print self.logstr.getvalue()
        pass

    def test_gravity_loss(self):
        # check against ...

        LEO = Orbit()
        LEO.body = 'Earth'
        LEO.apoapsis = 407
        LEO.periapsis = 407

        maneuver = Maneuver()
        maneuver.orbit = LEO
        maneuver.C3 = -1.671

        templ = 'Gravity Loss from %3dk LEO with C3 of %5.3f and T/W of %5.3f = %5.3f'

        TW = 0.11
        print templ % (maneuver.orbit.apoapsis, maneuver.C3, TW,
                       maneuver.gravity_loss(TW, burns=2))

        TW = 0.103
        print templ % (maneuver.orbit.apoapsis, maneuver.C3, TW,
                       maneuver.gravity_loss(TW, burns=2))

        TW = 0.165
        print templ % (maneuver.orbit.apoapsis, maneuver.C3, TW,
                       maneuver.gravity_loss(TW, burns=2))

        TW = 0.139
        print templ % (maneuver.orbit.apoapsis, maneuver.C3, TW,
                       maneuver.gravity_loss(TW, burns=2))


if __name__ == '__main__':
    unittest.main()
