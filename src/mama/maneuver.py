"""
   maneuver.py
"""

import logging

from math import sqrt, pi, cos

from openmdao.main.api import Component
from openmdao.lib.datatypes.api import Float, Int, Slot, Enum

from orbit import Orbit


class Maneuver(Component):

    orbit = Slot(Orbit,
        desc='initial orbit and final orbit (if applicable)')

    # inputs

    maneuver_type = Enum('Delta-V',
        ('Departure from Apoapsis', 'Departure from Periapsis',
         'Capture at Apoapsis',     'Capture at Periapsis',
         'Circularize at Apoapsis', 'Circularize at Periapsis',
         'Delta-V', 'Plane Change'), iotype='in',
        desc='maneuver type')

    stage = Int(0, iotype='in',
        desc='stage number from which the propellant for this maneuver is deducted')

    mass = Float(0.0, iotype='in',
        desc='mass of the vehicle at the start of the maneuver')

    dV = Float(0.0, iotype='in', units='km/s',
        desc='fixed delta-V for phase (RCS, MCC, etc.)')

    bulk_reserve = Float(0.0, iotype='in',
        desc='multiplying factor to calculate bulk reserve propelllant, '
             'it is multiplied by the nominla propellant required')

    dV_reserve = Float(0.0, iotype='in',
        desc='multiplying factor to calculate reserve propellant for uncertainties in delta-V, '
             'taken as percentage of nominal delta-V. e.g. 1.5%  is expressed as 0.015')

    Isp_reserve = Float(0.0, iotype='in',
        desc='multiplying factor to calculate reserve propellant for uncertainties in ISP, '
             'taken as percentage of nominal ISP. e.g. 1.5%  is expressed as 0.015')

    other_reserve = Float(0.0, iotype='in',
        desc='multiplying factor to calculate OTHER reserve propelllant, '
             'it is multiplied by the nominla propellant required')

    gravloss_data = Int(iotype='in',
        desc='gravity loss data set to use (1-16) for burn')

    g = Float(9.8062E-3, iotype='in', units='km/s',
        desc='acceleration due to gravity')

    C3 = Float(0.0, iotype='in',  # units='km^2/s^2',
        desc='C3 incoming/outgoing for maneuver, requires apoapsis and periapsis'
             'to calculate required periapsis velocity change')

    # outputs

    burn_time = Float(0.0, iotype='out',
        desc='burn duration (in minutes)')

    def gravity_loss(self, TW, burns=1):
        """ calculate gravity loss for maneuver
            TODO: currently only have equations for one or two burn TLI from
                  a circular earth orbit with Isp of 900s
        """
        orbit = self.orbit
        if orbit.body != 'Earth' or orbit.apoapsis != orbit.periapsis:
            self.log('Can only compute gravity loss leaving from circular LEO')
            self.log(str(orbit))
            return

        # TW    = 0.11
        # r     = 6785.14
        # C3    = -1.671
        # burns = 2

        if burns == 1:
            m1 = (- 0.001780493 * TW**5
                  - 0.022793191 * TW**4
                  + 0.077236216 * TW**3
                  - 0.088317529 * TW**2
                  + 0.044187306 * TW**1
                  - 0.008675645)

            b1 = (- 373.5457107 * TW**5
                  + 1416.037449 * TW**4
                  - 2123.882421 * TW**3
                  + 1586.194924 * TW**2
                  - 600.5083743 * TW**1
                  + 96.9251525)

            m2 = (+ 5.236463124 * TW**5
                  - 17.13945421 * TW**4
                  + 21.76682131 * TW**3
                  - 13.46112409 * TW**2
                  + 4.118567455 * TW**1
                  - 0.524766446)

            b2 = (- 46715.84466 * TW**5
                  + 152665.0942 * TW**4
                  - 193425.3839 * TW**3
                  + 119181.2715 * TW**2
                  - 36249.91164 * TW**1
                  + 4573.564918)
        elif burns == 2:
            m1 = (+ 0.065289684 * TW**5
                  - 0.212965428 * TW**4
                  + 0.268721507 * TW**3
                  - 0.164266201 * TW**2
                  + 0.049233822 * TW**1
                  - 0.0060403)

            b1 = (- 609.7173222 * TW**5
                  + 1985.167045 * TW**4
                  - 2499.028265 * TW**3
                  + 1522.748139 * TW**2
                  - 454.2432999 * TW**1
                  + 55.31565955)

            m2 = (+ 2.310083708 * TW**5
                  - 7.485235246 * TW**4
                  + 9.36476806  * TW**3
                  - 5.658397    * TW**2
                  + 1.666878713 * TW**1
                  - 0.198921842)

            b2 = (- 19557.5509  * TW**5
                  + 63349.30543 * TW**4
                  - 79217.25722 * TW**3
                  + 47829.47535 * TW**2
                  - 14073.25171 * TW**1
                  + 1676.106499)
        else:
            self.log('Can only compute gravity loss for one or two burns but',
                burns, 'burns were specified')
            return

        r = orbit.body_radius() + orbit.apoapsis
        C3 = self.C3

        m = m1 * r + b1
        b = m2 * r + b2
        g_loss = m * C3 + b

        return g_loss

    def calculate_dV(self):
        """ determine the delta-V required for orbit change
        """
        if self.maneuver_type == 'Departure from Apoapsis':
            # given an orbit and C3, calculate the dV required to leave orbit with that C3
            orbit = self.orbit
            self.log('   ', orbit)

            Va = orbit.velocity(orbit.apoapsis)
            Ve = orbit.escape_velocity(orbit.apoapsis)
            Vfinal = sqrt(self.C3 + Ve**2)
            self.log('    velocity @ %4.1f km = %4.3f km/s' % (orbit.apoapsis, Va))
            self.log('    escape velocity @ %4.2f km = %4.3f km/s' % (orbit.apoapsis, Ve))
            self.log('    Vfinal = %6.3f km/s' % Vfinal)

            dV = Vfinal - Va
            self.log('    dV needed to leave orbit with C3 of %4.3f km2/s2 = %1.3f km/s' %
                (self.C3, dV))
            return dV

        if self.maneuver_type == 'Departure from Periapsis':
            # given an orbit and C3, calculate the dV required to leave orbit with that C3
            orbit = self.orbit
            self.log(orbit)

            Vp = orbit.velocity(orbit.periapsis)
            Vfinal = sqrt(self.C3 + orbit.escape_velocity(orbit.periapsis)**2)
            self.log('    Vfinal = %6.3f km/s' % Vfinal)

            dV = Vfinal - Vp
            self.log('    dV needed to leave orbit with C3 of %4.3f km2/s2 = %1.3f km/s' %
                (self.C3, dV))
            return dV

        if self.maneuver_type == 'Capture at Apoapsis':
            # given a C3 and an orbit, calculate the dV required to capture into that orbit
            orbit = self.orbit
            self.log(orbit)

            self.log('    Vfinal (apoapsis):')
            Vfinal = orbit.velocity(orbit.apoapsis)

            Vapproach = sqrt(self.C3 + orbit.escape_velocity(orbit.apoapsis)**2)
            self.log('    Vapproach = %6.3f km/s' % Vapproach)

            dV = Vfinal - Vapproach
            self.log('    dV needed to enter orbit with C3 of %4.3f km2/s2 = %1.3f km/s' %
                (self.C3, dV))
            return dV

        if self.maneuver_type == 'Capture at Periapsis':
            # given a C3 and an orbit, calculate the dV required to capture into that orbit
            orbit = self.orbit
            self.log(orbit)

            self.log('    Vfinal (periapsis):')
            Vfinal = orbit.velocity(orbit.periapsis)

            Vapproach = sqrt(self.C3 + orbit.escape_velocity(orbit.periapsis)**2)
            self.log('    Vapproach = %6.3f km/s' % Vapproach)

            dV = Vfinal - Vapproach
            self.log('    dV needed to enter orbit with C3 of %4.3f km2/s2 = %1.3f km/s' %
                (self.C3, dV))
            return dV

        if self.maneuver_type == 'Plane Change':
            # given an orbit and a delta inclination, calculate the dV required
            # to make that plane change at the apoapsis
            orbit = self.orbit
            self.log(orbit)

            Va = orbit.velocity(orbit.apoapsis)
            self.log('    Va:', Va)

            # dVp^2 = Va^2 + Va^2 - 2Va^2 cos(theta)
            # FIXME: using inclination here as inclination CHANGE vs actual inclination
            dV = sqrt(2 * Va**2 * (1 - cos(orbit.inclination*pi/180)))
            self.log('    dV needed to make a plane change of %4.3f deg at apoapsis = %1.3f km/s' %
                (orbit.inclination, dV))
            return dV

        if self.maneuver_type == 'Circularize at Apoapsis':
            # TODO: UNTESTED
            orbit = self.orbit
            self.log(orbit)

            Vc = orbit.circular_velocity(orbit.apoapsis)

            Vp = orbit.velocity(orbit.apoapsis)
            self.log('    Vp:', Vp)

            dV = Vp - Vc
            self.log('    dV needed to circularize orbit at apoapsis = %1.3f km/s' % dV)
            return dV

        if self.maneuver_type == 'Circularize at Periapsis':
            orbit = self.orbit
            self.log(orbit)

            Vc = orbit.circular_velocity(orbit.periapsis)

            Vp = orbit.velocity(orbit.periapsis)
            self.log('    Vp:', Vp)

            dV = Vp - Vc
            self.log('    dV needed to circularize orbit at periapsis = %1.3f km/s' % dV)
            return dV

        self.log('TODO: calculate delta-V for orbit change maneuver', self.maneuver_type)

    def execute(self, spacecraft):
        """ calls the spacecraft to do a burn to achieve the delta-V
            required for this maneuver.  If the delta-V is not explicitly
            provided, it is calculated based on the current orbit and
            the maneuver type.
        """
        if self.dV <= 0.0:
            self.dV = self.calculate_dV()
            self.log('')

        self.burn_time = spacecraft.burn(self.dV, self.stage,
            self.bulk_reserve, self.dV_reserve, self.Isp_reserve, self.other_reserve)

    def log(self, *args):
        logger = logging.getLogger('mission')
        msg = ''
        for arg in args:
            msg += str(arg) + ' '
        logger.info(msg.rstrip(' '))
