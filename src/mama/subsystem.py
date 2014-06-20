"""
   subsystem.py
"""


import sys
import logging

from zope.interface import Interface

from openmdao.main.api import Assembly, Component
from openmdao.lib.datatypes.api import Str, Float, List, Bool
from openmdao.main.mp_support import has_interface


class MassItem(Component):
    """ an individual item within a subsystem that has mass properties
    """

    # inputs
    mass   = Float(0.0, iotype='in', units='kg', desc='mass')

    fluid  = Bool(False, iotype='in', desc='indicates if the item is a fluid')

    shape  = Str('Solid_Cylinder', iotype='in', desc='reference shape for item')

    radius = Float(0.0, iotype='in', units='m', desc='effective radius of item')
    length = Float(0.0, iotype='in', units='m', desc='effective length of item')

    x      = Float(0.0, iotype='in', desc='location of item within subsystem, X')
    y      = Float(0.0, iotype='in', desc='location of item within subsystem, Y')
    z      = Float(0.0, iotype='in', desc='location of item within subsystem, Z')

    # outputs
    Cg      = List([0.0, 0.0, 0.0], iotype='out', desc='center of gravity')

    Ioxx    = Float(0.0, iotype='out', desc='moment of inertia of item around X axis')
    Ioyy    = Float(0.0, iotype='out', desc='moment of inertia of item around Y axis')
    Iozz    = Float(0.0, iotype='out', desc='moment of inertia of item around Z axis')

    Mx      = Float(0.0, iotype='out', desc='mass moment of item within subsystem, X')
    My      = Float(0.0, iotype='out', desc='mass moment of item within subsystem, Y')
    Mz      = Float(0.0, iotype='out', desc='mass moment of item within subsystem, Z')

    def __init__(self, mass=0.0):
        self.mass = mass
        super(MassItem, self).__init__()

    def execute(self):
        # calculate moments of inertia with respect to item Cg
        if self.shape == 'Solid_Cylinder':
            r = self.radius
            L = self.length
            self.Cg   = [L/2.0, 0.0, 0.0]
            self.Ioyy = (self.mass/12)*((3*r)**2 + (L*2))
            self.Iozz = self.Ioyy
            self.Ioxx = self.mass*(r)**2
        elif self.shape == 'Hollow_Cylinder':
            r = self.radius
            L = self.length
            self.Cg   = [L/2.0, 0.0, 0.0]
            self.Ioyy = (self.mass/12)*((6*r)**2 + (L*2))
            self.Iozz = self.Ioyy
            self.Ioxx = self.mass*r**2
        else:
            # assume properties have already been set for item
            pass

        # calculate mass moments with respect to subsystem
        self.Mx = self.mass * self.x
        self.My = self.mass * self.y
        self.Mz = self.mass * self.z

class Subsystem(Assembly):
    """ A subsystem.

        A subsystem has a dry mass, a wet mass and power usage.

        A subsystem may be composed of further subsystems and/or a list of
        items, each of which has associated mass properties that
        contribute to the mass properties of the subsystem.

        Power usage is not yet implemented.

        This class is intended to be extended to reflect the characteristics
        of specific subsystems.

        Mass properties (center of gravity and moments of inertia) are in
        the process of being added
    """

    # inputs

    description = Str(iotype='in',
        desc='description of the subsystem')

    mass_category = Str('S', iotype='in',
        desc='mass category (per MGA table)')

    mass_maturity = Str('L', iotype='in',
        desc='mass maturity (per MGA table)')

    x = Float(0.0, iotype='in', units='m',
        desc='x location of subsystem within parent subsystem')

    y = Float(0.0, iotype='in', units='m',
        desc='y location of subsystem within parent subsystem')

    z = Float(0.0, iotype='in', units='m',
        desc='z location of subsystem within parent subsystem')

    # outputs

    dry_mass = Float(0., iotype='out', units='kg',
        desc='calculated dry mass of subsystem in kg')

    dwc = Float(0.0, iotype='out',
        desc='dry weight contingency (based on mass category and maturity)')

    wet_mass = Float(0., iotype='out', units='kg',
        desc='calculated wet mass of subsystem in kg')

    power_usage = Float(0., iotype='out', units='kW',
        desc='calculated electrical power used by subsystem')

    Cg = List([0.0, 0.0, 0.0], iotype='out',
        desc='center of gravity (x,y,z) of subsystem')

    Mx = Float(0.0, iotype='out',
        desc='moment about x axis')

    My = Float(0.0, iotype='out',
        desc='moment about y axis')

    Mz = Float(0.0, iotype='out',
        desc='moment about z axis')

    Ixx = Float(0.0, iotype='out',
        desc='moment of inertia around x axis wrt Vehicle')

    Iyy = Float(0.0, iotype='out',
        desc='moment of inertia around y axis wrt Vehicle')

    Izz = Float(0.0, iotype='out',
        desc='moment of inertia around z axis wrt Vehicle')

    Ioxx = Float(0.0, iotype='out',
        desc='moment of inertia around x axis wrt subsystem Cg')

    Ioyy = Float(0.0, iotype='out',
        desc='moment of inertia around y axis wrt subsystem Cg')

    Iozz = Float(0.0, iotype='out',
        desc='moment of inertia around z axis wrt subsystem Cg')

    # methods

    def configure(self):
        """ connect all mass items and subsystem masses to compute
            subsystem dry mass and wet mass
        """
        dry_masses = []
        wet_masses = []

        items = self.get_children(MassItem)
        for item in items:
            self.driver.workflow.add(item)
            dry_masses.append(item+'.mass')
            if self.get(item).fluid:
                wet_masses.append(item+'.mass')

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            self.add_to_workflow(subsystems)
            dry_masses.extend([subsystem + '.dry_mass' for subsystem in subsystems])
            wet_masses.extend([subsystem + '.wet_mass' for subsystem in subsystems])

        if len(dry_masses) > 0:
            self.connect('+'.join(dry_masses), 'dry_mass')
        if len(wet_masses) > 0:
            self.connect('+'.join(wet_masses), 'wet_mass')

        super(Subsystem, self).configure()

    def get_children(self, klass):
        """ get all children of the specified class """
        children = [child for child in self.list_containers()
            if (isinstance(self.get(child), klass) or
               (isinstance(klass, Interface.__class__) and has_interface(self.get(child), klass)))]
        return children

    def add_to_workflow(self, children):
        """ ensure that all the specified children are in the workflow """
        workflow = self.driver.workflow.get_names()
        for child in children:
            if child not in workflow:
                self.driver.workflow.add(child)

    def summation(self, children, prop):
        """ get the sum of the specified property for the listed children """
        total = 0
        for child in children:
            try:
                total = total + self.get(child).get(prop)
            except:
                print 'Child of ', self.name, ',', child, \
                      'does not have property', prop, 'for summation'
        return total

    def display(self, indent=0, output=sys.stdout):
        """ display details about the subsystem"""
        wetness = self.wet_mass - self.dry_mass
        if wetness == 0:
            print >>output, '%s%-15s\tdry:%10.2f\twet:%10.2f' \
                % ('  '*indent, self.name, self.dry_mass, self.wet_mass)
        else:
            print >>output, '%s%-15s\tdry:%10.2f\twet:%10.2f\t(%10.2f)' \
                % ('  '*indent, self.name, self.dry_mass, self.wet_mass, wetness)

        items = self.get_children(MassItem)
        if len(items) > 0:
            for item in items:
                print >>output, '%s%-15s\t    %10.2f' \
                    % ('  '*(indent+1), item, self.get(item).mass)

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).display(indent+1, output)

    def execute(self):
        """ Override to calculate subsystem dependent properties from input parameters.
            The default is just to calculate mass properties.
        """
        super(Subsystem, self).execute()
        if self.wet_mass == 0:
            self.wet_mass = self.dry_mass
        # self.update_mass_properties()

    def update_wet_mass(self):
        """ Update the wet mass of the subsystem to account for fuel burn, etc.
            (without re-executing everything)
        """
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).update_wet_mass()
            self.wet_mass = self.summation(subsystems, 'wet_mass')

        items = self.get_children(MassItem)
        # self.wet_mass += self.summation(items, 'mass')
        for item in items:
            self.wet_mass += self.get(item).mass

    def update_mass_properties(self):
        self.Mx = 0
        self.My = 0
        self.Mz = 0
        self.Ioxx = 0
        self.Ioyy = 0
        self.Iozz = 0
        # roll up properties from subsystems
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for name in subsystems:
                subsystem = self.get(name)
                self.Mx += subsystem.wet_mass*(subsystem.Cg[0] + self.x)
                self.My += subsystem.wet_mass*(subsystem.Cg[1] + self.y)
                self.Mz += subsystem.wet_mass*(subsystem.Cg[2] + self.z)
                self.Ioxx += subsystem.Ioxx
                self.Ioyy += subsystem.Ioyy
                self.Iozz += subsystem.Iozz

        # roll up properties from items
        items = self.get_children(MassItem)
        if len(items) > 0:
            for name in items:
                item = self.get(name)
                self.Mx += item.Mx
                self.My += item.My
                self.Mz += item.Mz
                self.Ioyy += item.Ioyy
                self.Iozz += item.Iozz
                self.Ioxx += item.Ioxx

        # calculate subsystem Cg
        if self.dry_mass > 0:
            moments = [self.Mx, self.My, self.Mz]
            self.Cg = [moment/self.dry_mass for moment in moments]
        else:
            self.Cg = [0.0, 0.0, 0.0]

    Cgrocket = List([0.0, 0.0, 0.0], iotype='in',
        desc='center of gravity for entire system')

    def get_inertia(self):
        """ calculate moments of inertia
            get_mass_properties must be executed first in order to determine Cgrocket
        """
        self.Ixx = 0
        self.Iyy = 0
        self.Izz = 0

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            # roll up properties from subsystems
            for subsystem in subsystems:
                self.get(subsystem).get_inertia()
                x = subsystem.Cg[0] + self.x
                y = subsystem.Cg[1] + self.y
                z = subsystem.Cg[2] + self.z
                self.Ixx += subsystem.dry_mass*((y - self.Cgrocket[1])**2 + (z - self.Cgrocket[2])**2)
                self.Iyy += subsystem.dry_mass*((x - self.Cgrocket[0])**2 + (z - self.Cgrocket[2])**2)
                self.Izz += subsystem.dry_mass*((x - self.Cgrocket[0])**2 + (y - self.Cgrocket[1])**2)

        el = self.items
        if len(el) > 0:
            # roll up properties from items
            for name in el:
                x = el[name]['x']
                y = el[name]['y']
                z = el[name]['z']
                self.Ixx += subsystem.dry_mass*((y - self.Cgrocket[1])**2 + (z - self.Cgrocket[2])**2)
                self.Iyy += subsystem.dry_mass*((x - self.Cgrocket[0])**2 + (z - self.Cgrocket[2])**2)
                self.Izz += subsystem.dry_mass*((x - self.Cgrocket[0])**2 + (y - self.Cgrocket[1])**2)

    def log(self, *args):
        logger = logging.getLogger('mission')
        msg = ''
        for arg in args:
            msg += str(arg) + ' '
        logger.info(msg.rstrip(' '))

# end SubSystem
