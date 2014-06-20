"""
   orbit.py
"""

from math import sqrt, pi, acos

from openmdao.main.api import Component
from openmdao.lib.datatypes.api import Float, Enum


class Orbit(Component):
    """ Orbit parameters. """

    # inputs
    body = Enum('Earth', ('Sun', 'Mercury', 'Venus', 'Earth', 'Mars',
                'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Moon'),
        iotype='in',
        desc='celestial body about which the vehicle is currently in orbit,'
             'not required unless you want to calculate orbit change'
             '(change in periapsis/apoapsis) delta-V or arrival/departure delta-V (from C3)')

    apoapsis  = Float(0, iotype='in',
        desc='apoapsis altitude')

    periapsis = Float(0, iotype='in',
        desc='periapsis altitude')

    inclination = Float(0, iotype='in',
        desc='inclination')

    # constant
    G = Float(6.67384e-11, iotype='out',
        desc='gravitational constant (m^3/kg-s^2)')

    def __init__(self, body='Earth'):
        # default to Earth orbit
        self.body = body
        super(Orbit, self).__init__()

    def __str__(self):
        return 'Orbiting %s at %1.1f X %1.1f km with inclination %1.1f, period %1.1fhr' \
            %  (self.body, self.periapsis, self.apoapsis, self.inclination, self.period()/3600)

    def body_index(self):
        index = {
            'Sun':      1,
            'Mercury':  2,
            'Venus':    3,
            'Earth':    4,
            'Mars':     5,
            'Jupiter':  6,
            'Saturn':   7,
            'Uranus':   8,
            'Neptune':  9,
            'Pluto':    10,
            'Moon':     11
        }
        return index[self.body]

    def body_mass(self):
        mass = {
            'Sun':      0.9891e30,
            'Mercury':  3.30104e23,
            'Venus':    4.86732e24,
            'Earth':    5.976e24,   # 5.97219e24,
            'Mars':     6.41693e23,
            'Jupiter':  1.89813e27,
            'Saturn':   5.68319e26,
            'Uranus':   8.68103e25,
            'Neptune':  1.0241e26,
            'Pluto':    1.30900e22,
            'Moon':     7.35e22     # 7.34767309e22
        }
        return mass[self.body]  # kg

    def body_radius(self):
        radius = {
            'Sun':        6.955e8,
            'Mercury':    2.440e3,
            'Venus':      6.051e3,
            'Earth':      6.378e3,
            'Mars':       3.397e3,
            'Jupiter':   7.1492e4,
            'Saturn':    6.0268e4,
            'Uranus':    2.5559e4,
            'Neptune':   2.4764e4,
            'Pluto':      1.160e3,
            'Moon':       1.738e3
        }
        return radius[self.body]  # km

    def insolation(self):
        """ http://pveducation.org/pvcdrom/properties-of-sunlight/solar-radiation-in-space
        """
        insolation = {
            'Mercury':    9116.4,
            'Venus':      2611.0,
            'Earth':      1366.1,
            'Mars':        588.6,
            'Jupiter':      50.5,
            'Saturn':       15.04,
            'Uranus':        3.72,
            'Neptune':       1.51,
            'Pluto':         0.878,
            'Moon':       1366.1
        }
        return insolation[self.body]  # W/m**2

    def body_gravity(self):
        return self.G * self.body_mass() / 1e9

    def velocity(self, altitude):
        """ orbital velocity at specified altitude
            v = sqrt(Mu * (2/r - 1/a))
            http://en.wikipedia.org/wiki/Orbital_mechanics#Velocity
        """
        Mu = self.body_gravity()
        r = self.body_radius() + altitude
        a = (2*self.body_radius() + self.apoapsis + self.periapsis) / 2  # semi_major_axis
        v = sqrt(Mu * (2/r - 1/a))
        return v

    def circular_velocity(self, altitude):
        """ circular velocity at specified altitude
            Vc = sqrt(Mu / r)
            http://en.wikipedia.org/wiki/Orbital_mechanics#Circular_orbits
        """
        Mu = self.body_gravity()
        r = self.body_radius() + altitude
        Ve = sqrt(Mu/r)
        return Ve

    def escape_velocity(self, altitude):
        """ escape velocity at specified altitude
            Ve = sqrt(2 * Mu / r)
            http://en.wikipedia.org/wiki/Escape_velocity
        """
        Mu = self.body_gravity()
        r = self.body_radius() + altitude
        Ve = sqrt(2*Mu/r)
        return Ve

    def period(self):
        """ orbital period of an elliptic orbit
            T = 2 * pi * sqrt(a**3 / Mu)
            http://en.wikipedia.org/wiki/Orbital_mechanics#Orbital_period
        """
        a = (2*self.body_radius() + self.apoapsis + self.periapsis) / 2  # semi_major_axis
        Mu = self.body_gravity()
        T = 2 * pi * sqrt(a**3 / Mu)
        return T

    def eclipse(self):
        """ amount of time spent in eclipse during a single orbit
            TODO: derive this
        """
        # note: assumes circular orbit
        r = self.body_radius() + self.periapsis

        # equation taken from 'Solar Array Sizer - CRC3a.xls'
        eclipse = (0.01745*(2*acos(1-(r-0.5*sqrt(4*r**2-(2*self.body_radius())**2))/r)*180/pi)*r) \
                / (2*pi*r)*self.period()
        return eclipse

    def orbit_from_period(self, T, apsis):
        """ calculate the apoapsis and periapsis for an orbit with the given
            period (in seconds)
            T = 2 * pi * sqrt(a**3 / Mu)
            a = ((T/(2*pi))**2 * Mu)**(1/3)
            http://en.wikipedia.org/wiki/Orbital_mechanics#Orbital_period

        """
        Mu = self.body_gravity()
        Mu = 3.986e5
        lhs = T / (2*pi)
        lhs = lhs**2
        lhs = lhs * Mu
        a = lhs**(1./3.)  # semi_major_axis
        body_radius = self.body_radius()
        r_apsis = body_radius + apsis
        r_other = 2*a - r_apsis
        if r_other < r_other:
            return (r_other - body_radius, apsis)
        else:
            return (apsis, r_other - body_radius)
