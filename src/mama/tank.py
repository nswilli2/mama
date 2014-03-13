"""
   tank.py
"""

import logging

from openmdao.lib.datatypes.api import Str, Float, Enum

from math import pi
import numpy as np

try:
    import svgwrite as svg
    from svgwrite import mm
except ImportError:
    svg = None

import StringIO

from subsystem import Subsystem

# constants
m_to_f    = 3.2808
m2_to_f2  = 10.7639
m3_to_f3  = 35.3146667
lbs_to_kg = 0.453592

verbose = True


class Tank(Subsystem):

    # inputs

    capacity  = Float(0.0, units='kg', iotype='in',
        desc='fuel capacity')

    ullage  = Float(.025, units='kg', iotype='in',
        desc='ullage (default 2.5%)')

    diameter  = Float(0.0, units='m', iotype='in',
        desc='tank diameter (outer)')

    thickness = Float(0.1, units='m', iotype='in',
        desc='wall thickness')

    dome_ecc  = Float(0.707107, iotype='in',
        desc='dome eccentricity (1 = sphere)')

    fuel_density = Float(0.0, units='kg/m**3', iotype='in',
        desc='fuel density')

    material  =  Enum('metallic', ('metallic', 'composite'), iotype='in',
        desc='tank material')

    # per McCurdy 5/8/13:
    # We currently use 2% of actual propellant.  It's just been a standard
    # number I've been told to use.  I think it has Apollo heritage
    residual_fraction = Float(0.02, io_type='in',
        desc='fraction (percentage) of unusable fuel trapped in tank')

    # by default, tank mass is calculated from mass fraction and fuel load
    mass_fraction  = Float(0.0,  iotype='in',
        desc='mass fraction')

    # outputs

    inner_diameter = Float(0.0, units='m', iotype='out',
        desc='inner diameter of tank')

    length = Float(0.0, units='m', iotype='out',
        desc='length')

    area = Float(0.0, units='m**2', iotype='out',
        desc='Surface Area')

    volume = Float(0.0, units='m**3', iotype='out',
        desc='Volume')

    drawing = Str('', iotype='out',
        desc='Conceptual Drawing (SVG)')

    fuel = Float(0.0, iotype='out', units='kg',
         desc='current fuel load')

    residual_fuel = Float(0.0, io_type='out', units='kg',
        desc='unusable fuel trapped in tank')

    def execute(self):
        """ calculate volume, length, area and mass given diameter and capacity
        """
        self.log('')
        self.log('Executing tank, capacity =', self.capacity, 'kg')

        self.volume = (1 + self.ullage) * self.capacity/self.fuel_density  # m**3
        self.log('    volume = ', self.volume, 'm^3 (', self.volume*m3_to_f3, 'ft^3)')

        # assume wall thickness = 0.1m
        self.inner_diameter = self.diameter - (self.thickness * 2)

        ecc = self.dome_ecc

        r = self.inner_diameter / 2

        # volume of a cylinder = pi*r*r*h
        # volume of a sphere   = (4/3)*pi*r*r*r
        # length of tank       = (V - (4/3)*pi*r*r*r)/pi*r*r

        dome_volume = (4.0/3.0) * pi * ecc * r*r*r
        barrel_volume = self.volume - dome_volume

        self.log('    dome volume   =', dome_volume,   'm^3 (', dome_volume * m3_to_f3,   'ft^3)')
        self.log('    barrel volume =', barrel_volume, 'm^3 (', barrel_volume * m3_to_f3, 'ft^3)')

        barrel_length = barrel_volume/(pi*r*r)
        self.length = barrel_length + (self.inner_diameter * ecc)

        self.log('    barrel length =', barrel_length, 'm (', barrel_length * m_to_f, 'ft)')
        self.log('    dome length   =', (self.inner_diameter * ecc), 'm (', (self.inner_diameter * ecc) * m_to_f, 'ft)')
        self.log('    tank length   =', self.length,   'm (', self.length * m_to_f,   'ft)')

        barrel_area = pi*self.inner_diameter*barrel_length
        dome_area = 2*pi*(r*r+((r*ecc)**2/(2*ecc))*np.log((1+ecc)/(1-ecc)))
        self.area = barrel_area + dome_area

        self.log('    barrel area =', barrel_area, 'm^2 (', barrel_area * m2_to_f2, 'ft^2)')
        self.log('    dome area   =', dome_area,   'm^2 (', dome_area * m2_to_f2,   'ft^2)')
        self.log('    tank area   =', self.area,   'm^2 (', self.area * m2_to_f2,   'ft^2)')

        # tank weight relationships are in english units
        if self.material == 'metallic':
            length_ft = self.length * m_to_f
            areal_weight = (self.inner_diameter / 7.6) * (0.00087 * length_ft**2 - 0.111 * length_ft + 6.6)
        elif self.material == 'composite':
            areal_weight = (self.inner_diameter / 7.6) * (0.027777 * self.length + 2.022)
        else:
            print 'Invalid material specified for tank'

        self.log('    areal_weight =', areal_weight)

        # calulate mass in lbs
        barrel_weight = (1 + self.dwc) * areal_weight * barrel_area * m2_to_f2
        self.log('    barrel weight =', barrel_weight, 'lbs')

        dome_weight = (1 + self.dwc) * areal_weight * dome_area * m2_to_f2
        self.log('    dome weight   =', dome_weight, 'lbs')

        self.dry_mass = barrel_weight + dome_weight
        self.log('    dry mass =', self.dry_mass, 'lbs')

        # convert to kg
        barrel_weight = barrel_weight * lbs_to_kg
        dome_weight = dome_weight * lbs_to_kg
        self.dry_mass = barrel_weight + dome_weight
        self.log('    dry mass =', self.dry_mass, 'kg')

        # tank starts at full capacity
        self.fuel = self.capacity
        self.log('    fuel =', self.fuel, 'kg')

        self.residual_fuel = self.capacity * self.residual_fraction
        self.log('    residual fuel =', self.residual_fuel, 'kg')

        self.wet_mass = self.dry_mass + self.fuel
        self.log('    wet mass =', self.wet_mass, 'kg')
        self.log('')

        # self.display()

    def add_fuel(self, fuel):
        """ add the specified mass of fuel to the tank
            if fuel is not specified, fill to capacity
            (wet mass is recalculated)
        """

        if fuel is None:
            self.fuel = self.capacity
        else:
            self.fuel = self.fuel + fuel
        self.update_wet_mass()

    def expend_fuel(self, fuel):
        """ remove the specified mass of fuel from the tank
            (wet mass is recalculated)
        """
        self.fuel = self.fuel - fuel
        self.update_wet_mass()

    def update_dry_mass(self):
        """ update the dry mass of the subsystem
            Override: no need to update dry mass after execution
        """
        pass

    def update_wet_mass(self):
        """ update the wet mass of the subsystem """
        self.wet_mass = self.dry_mass + self.fuel

    def _repr_svg_(self):
        if svg:
            dwg = svg.Drawing(debug=True)
            shapes = dwg.add(dwg.g(id='shapes', fill='blue'))

            shapes.add(dwg.circle(center=(self.diameter*mm, self.diameter*mm),
                              r=self.diameter/2*mm,
                              stroke='red', stroke_width=3))

            shapes.add(dwg.circle(center=((self.length+self.diameter)*mm, self.diameter*mm),
                              r=self.diameter/2*mm,
                              stroke='red', stroke_width=3))

            shapes.add(dwg.rect(insert=(self.diameter*mm, self.diameter/2*mm),
                            size=(self.length*mm, self.diameter*mm),
                            stroke='red', stroke_width=3))

            dwg_str = StringIO.StringIO()
            dwg.write(dwg_str)
            return dwg_str.getvalue()
        else:
            return None

    def log(self, *args):
        if verbose:
            logger = logging.getLogger('mission')
            msg = ''
            for arg in args:
                msg += str(arg) + ' '
            logger.info(msg.rstrip())

    # def display(self):
    #     print '  tank volume:  ', self.volume, 'm^3 (', self.volume * m3_to_f3, 'ft^3)'
    #     print '  tank diameter:', self.diameter, 'm'
    #     print '  tank length:  ', self.length, 'm'
    #     print '  tank area:    ', self.area, 'm^2 (', self.area * m2_to_f2, 'ft^2)'
    #     print '  tank dry mass:', self.dry_mass, 'kg'


if __name__ == '__main__':
    core_tank = Tank()
    core_tank.diameter = 9.8
    core_tank.length = 19.46
    core_tank.execute()
    core_tank.display()
