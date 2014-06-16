"""
   subsystem.py
"""


import sys
import logging

from zope.interface import Interface

from openmdao.main.api import Assembly, Component
from openmdao.lib.datatypes.api import Str, Float, Dict, List
from openmdao.main.mp_support import has_interface

import mga


class Equipment(Component):
    """ a component representing an item on the equipment list
        (currently not executable, just provides mass properties)
    """

    mass   = Float(0.0, iotype='in', units='kg', desc='mass')
    x      = Float(0.0, iotype='in', desc='x location of component in its subsystem')
    y      = Float(0.0, iotype='in', desc='y location of component in its subsystem')
    z      = Float(0.0, iotype='in', desc='z location of component in its subsystem')
    radius = Float(0.0, iotype='in', desc='effective radius of component')
    length = Float(0.0, iotype='in', desc='effective length of component')
    shape  = Str('Solid_Cylinder', iotype='in', desc='reference shape for component')

    def __init__(self, mass=0.0):
        # constructor with optional mass
        self.mass = mass

    def mass_properties(self):
        properties = {}

        properties['Mx'] = self.mass * self.x
        properties['My'] = self.mass * self.y
        properties['Mz'] = self.mass * self.z

        if self.shape == 'Solid_Cylinder':
            r = self.radius
            L = self.length
            properties['Ioyy'] = (self.mass/12)*((3*r)**2 + (L*2))
            properties['Iozz'] = properties['Ioyy']
            properties['Ioxx'] = self.mass*(r)**2
        elif self.shape == 'Hollow_Cylinder':
            r = self.radius
            L = self.length
            properties['Ioyy'] = (self.mass/12)*((6*r)**2 + (L*2))
            properties['Iozz'] = properties['Ioyy']
            properties['Ioxx'] = self.mass*r**2
        else:
            properties['Ioyy'] = 0
            properties['Iozz'] = 0
            properties['Ioxx'] = 0

        return properties


class Subsystem(Assembly):
    """ A subsystem.

        A subsystem has a dry mass, a wet mass and power usage.

        A subsystem may be composed of further subsystems and/or a list of
        equipment, each of which has associated mass properties that
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

    fixed_mass = Float(0.0, iotype='in', units='kg',
        desc='fixed hardware mass ("overhead") of subsystem')

    mass_category = Str('S', iotype='in',
        desc='mass category (per MGA table)')

    mass_maturity = Str('L', iotype='in',
        desc='mass maturity (per MGA table)')

    equipment_list = Dict(iotype='in',
        desc='dictionary of equipment')

    xbase = Float(0.0, iotype='in', units='m',
        desc='base reference of distance along center axis')

    ybase = Float(0.0, iotype='in', units='m',
        desc='base reference of distance perpendicular to x')

    zbase = Float(0.0, iotype='in', units='m',
        desc='base reference of distance perpindicular to x and y')

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
        """ if subsystem has child subsystems, add a Summation component."""
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            self.add_to_workflow(subsystems)

            dry_masses = [subsystem + '.dry_mass' for subsystem in subsystems]
            wet_masses = [subsystem + '.wet_mass' for subsystem in subsystems]

            self.connect('+'.join(dry_masses), 'dry_mass')
            self.connect('+'.join(wet_masses), 'wet_mass')

        # if fixed mass is not specified, roll it up from equipment list
        if self.fixed_mass == 0:
            for name in self.equipment_list:
                self.fixed_mass += self.equipment_list[name].mass

        super(Subsystem, self).configure()

    def execute(self):
        """ Calculates subsystem dependent properties from input parameters.
            The default is just to update the dry and wet masses.
        """
        if len(self.driver.workflow) > 0:
            super(Subsystem, self).execute()

        self.dwc = mga.get_MGA(self.mass_category, self.mass_maturity)
        self.update_dry_mass()
        self.update_wet_mass()
        # self.get_mass_properties()

        # print '%10s %10s Dry Mass: %5.2f (%2d%% MGA), Wet Mass: %5.2f' \
        #     % (self.parent.name, self.name, self.dry_mass, self.dwc*100, self.wet_mass)

    def update_dry_mass(self):
        """ Update the dry mass of the subsystem.
            The default dry mass calculation is tp sum the dry mass of all the
            subsystems, the masses of all the equipment on the equipment list
            and the fixed mass and then add the dry weight contigency.
        """
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).update_dry_mass()
            self.dry_mass = self.summation(subsystems, 'dry_mass')

        for name in self.equipment_list:
            self.dry_mass += self.equipment_list[name].mass

        self.dry_mass = self.fixed_mass * (1 + self.dwc)

    def update_wet_mass(self):
        """ Update the wet mass of the subsystem.
            The default wet mass is equal to the dry mass if there are no
            subsystems or the sum the wet mass of all subsystems plus the mass
            of all the equipment on the equipment list if there are.
        """
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).update_wet_mass()
            self.wet_mass = self.summation(subsystems, 'wet_mass')
            for equipment in self.equipment_list:
                self.wet_mass += equipment.mass
            self.wet_mass += self.fixed_mass * (1 + self.dwc)
        else:
            self.wet_mass = self.dry_mass

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

    def display(self, indent=0, output=sys.stdout, show_equipment=False):
        """ display details about the subsystem"""
        wetness = self.wet_mass - self.dry_mass
        if wetness == 0:
            if (mga.MGA_enabled):
                print >>output, '%s%-15sfixed (%2.f%% dwc):%10.2f\tdry:%10.2f\twet:%10.2f' \
                    % ('  '*indent, self.name, self.dwc*100, self.fixed_mass*(1+self.dwc), self.dry_mass, self.wet_mass)
            else:
                print >>output, '%s%-15sfixed:%10.2f\tdry:%10.2f\twet:%10.2f' \
                    % ('  '*indent, self.name, self.fixed_mass*(1+self.dwc), self.dry_mass, self.wet_mass)
        else:
            if (mga.MGA_enabled):
                print >>output, '%s%-15sfixed (%2.f%% dwc):%10.2f\tdry:%10.2f\twet:%10.2f\t(%10.2f)' \
                    % ('  '*indent, self.name, self.dwc*100, self.fixed_mass*(1+self.dwc), self.dry_mass, self.wet_mass, wetness)
            else:
                print >>output, '%s%-15sfixed:%10.2f\tdry:%10.2f\twet:%10.2f\t(%10.2f)' \
                    % ('  '*indent, self.name, self.fixed_mass*(1+self.dwc), self.dry_mass, self.wet_mass, wetness)

        if show_equipment:
            for key in self.equipment_list:
                val =  self.equipment_list[key].mass
                if not isinstance(val, dict):
                    print >>output, '%s%-30s%10.2f' \
                        % ('  '*(indent+1), key, val)

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).display(indent+1, output, show_equipment)

        #Need changes to include mass porperties

    def add_equipment(self, name, equipment):
        self.equipment_list[name] = equipment

    def get_equipment_list(self):
        el = self.equipment_list
        # if len(el) == 0:
        #     if self.fixed_mass > 0:
        #         el['fixed_mass'] = self.fixed_mass

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                el[subsystem] = self.get(subsystem).get_equipment_list()
        return el

    def get_mass_properties(self):
        """ calculate mass properties """
        self.Mx = 0
        self.My = 0
        self.Mz = 0
        self.Ioxx = 0
        self.Ioyy = 0
        self.Iozz = 0

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            # roll up properties from subsystems
            for subsystem in subsystems:
                sub = self.get(subsystem)
                sub.get_mass_properties()
                self.Mx += sub.dry_mass*(sub.Cg[0] + self.xbase)
                self.My += sub.dry_mass*(sub.Cg[1] + self.ybase)
                self.Mz += sub.dry_mass*(sub.Cg[2] + self.zbase)
                self.Ioxx += sub.Ioxx
                self.Ioyy += sub.Ioyy
                self.Iozz += sub.Iozz

        el = self.equipment_list
        if len(el) > 0:
            # roll up properties from equipment_list
            for name in el:
                mp = el['name'].mass_properties()
                self.Mx += mp['Mx']
                self.My += mp['My']
                self.Mz += mp['Mz']
                self.Ioyy += mp['Ioyy']
                self.Iozz += mp['Iozz']
                self.Ioxx += mp['Ioxx']

        moments = [self.Mx, self.My, self.Mz]
        self.Cg = [moment/self.dry_mass for moment in moments]

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
                x = subsystem.Cg[0] + self.xbase
                y = subsystem.Cg[1] + self.ybase
                z = subsystem.Cg[2] + self.zbase
                self.Ixx += subsystem.dry_mass*((y - self.Cgrocket[1])**2 + (z - self.Cgrocket[2])**2)
                self.Iyy += subsystem.dry_mass*((x - self.Cgrocket[0])**2 + (z - self.Cgrocket[2])**2)
                self.Izz += subsystem.dry_mass*((x - self.Cgrocket[0])**2 + (y - self.Cgrocket[1])**2)

        el = self.equipment_list
        if len(el) > 0:
            # roll up properties from equipment_list
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
