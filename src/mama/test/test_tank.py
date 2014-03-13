
import unittest

from math import sqrt

import StringIO
import logging

from openmdao.main.api import Assembly, set_as_top
from openmdao.util.testutil import assert_rel_error

from mama.tank import Tank, m2_to_f2, m3_to_f3


class TankTestCase(unittest.TestCase):

    def setUp(self):
        # initialize 'mission' logger
        self.logger = logging.getLogger('mission')
        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)

        # create a top level assembly and add a tank to it
        self.top = set_as_top(Assembly())
        self.top.add('tank', Tank())
        self.top.driver.workflow.add('tank')

    def tearDown(self):
        print self.logstr.getvalue()
        pass

    def test_tank_calcs(self):
        # check against "Tank calcs.xlsx" spreadsheet from McCurdy
        self.top.tank.diameter  = 8.4
        self.top.tank.thickness = 0.1
        self.top.tank.dome_ecc  = sqrt(2)/2
        self.top.tank.material  = 'metallic'
        self.top.tank.density   = 70.85  # kg/m**3, density of LH2 (wikipedia.org/wiki/Liquid_hydrogen)
        self.top.tank.capacity  = (28509.26 / m3_to_f3) * self.top.tank.density
        self.top.tank.ullage    = 0.0

        self.top.run()

        assert_rel_error(self, self.top.tank.inner_diameter,    8.2,      0.0001)
        assert_rel_error(self, self.top.tank.length,            17.22,    0.0005)
        assert_rel_error(self, self.top.tank.area * m2_to_f2,   5012.43,  0.0005)
        assert_rel_error(self, self.top.tank.volume * m3_to_f3, 28509.26, 0.0005)


if __name__ == '__main__':
    unittest.main()
