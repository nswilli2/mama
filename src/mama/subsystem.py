"""
   subsystem.py
"""


import sys
import logging

from zope.interface import Interface

from openmdao.main.api import Assembly
from openmdao.lib.datatypes.api import Str, Float, Dict, List
from openmdao.main.mp_support import has_interface

import mga


class Subsystem(Assembly):
    """ A subsystem.

        A subsystem has a dry mass, a wet mass and power usage.

        If the subsystem is not composed of further subsystems, then its
        dry mass is the fixed mass times the dry weight contingency and the
        wet mass is the same as the dry mass.

        If the subsystem does have it's own subsystems, then its dry mass
        mass is the fixed mass plus the sum of its subsystem dry and wet
        masses, respectively.

        Power usage is not yet implemented.

        This class is intended to be extended to reflect the characteristics
        of specific subsystems.

        Mass properties (center of gravity and moments of inertia) are in the process of being added
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
        desc='dictionary of equipment masses')

    x = Float(0.0, iotype='in', units='m',
        desc='distance from end of stage of the center of gravity of the subsystem')

    y = Float(0.0, iotype='in', units='m',
        desc='distance from center line of the center of gravity of the subsystem')

    z = Float(0.0, iotype='in', units='m',
        desc='distance from center line of the center of gravity of the subsystem')

    #Length, radius and shape are needed to calculate Ioxx, Ioyy, Iozz for components (See Columns W-AA of Excel sheet)
    #L = Float(0.0, iotype='in', units='m',
    #    desc='effective length of subsystem'))

    #r = Float(0.0, iotype='in', units='m',
    #    desc='effective radius of subsystem')

    #shape = Enum('Solid_Cylinder', ('Solid_Cylinder','Hollow_Thin-Wall_Cylinder', 'Other'),
    #    iotype='in', desc='Shape of subsystem'

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

    Mx = FLoat(0.0,iotype='out', 
        desc='moment about x axis')

    My = Float(0.0,iotype='out', 
        desc='moment about y axis')

    Mz = Float(0.0,iotype='out', 
        desc='moment about z axis')

    Ixx = Float(0.0,iotype='out', 
        desc='moment of inertia around x axis')

    Iyy = Float(0.0,iotype='out',
        desc='moment of inertia around y axis')

    Izz = Float(0.0,iotype='out', 
        desc='moment of inertia around z axis')

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
                self.fixed_mass += self.equipment_list[name]

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
        self.get_mass_properties()

        # print '%10s %10s Dry Mass: %5.2f (%2d%% MGA), Wet Mass: %5.2f' \
        #     % (self.parent.name, self.name, self.dry_mass, self.dwc*100, self.wet_mass)
  
    def update_dry_mass(self):
        """ Update the dry mass of the subsystem.
            The default dry mass calculation is to multiply the fixed mass
            by the dry weight contigency and then add the dry mass of all
            subsystems (if any).  Override as necessary for specific subsystem.
        """
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).update_dry_mass()
            self.dry_mass = self.summation(subsystems, 'dry_mass')
            self.dry_mass += self.fixed_mass * (1 + self.dwc)
        else:
            self.dry_mass = self.fixed_mass * (1 + self.dwc)

    def update_wet_mass(self):
        """ Update the wet mass of the subsystem.
            The default wet mass is equal to the dry mass if there are no
            subsystems or the sum the wet mass of all subsystems if there are.
        """
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).update_wet_mass()
            self.wet_mass = self.summation(subsystems, 'wet_mass')
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
                val =  self.equipment_list[key]
                if not isinstance(val, dict):
                    print >>output, '%s%-30s%10.2f' \
                        % ('  '*(indent+1), key, val)

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).display(indent+1, output, show_equipment)

        #Need changes to include mass porperties

    def add_equipment(self, name, mass, Cgwrtstage):
        self.equipment_list[name] = mass
        self.equipment_list[name + '.x'] = Cgwrtstage[0]
        self.equipment_list[name + '.y'] = Cgwrtstage[1]
        self.equipment_list[name + '.z'] = Cgwrtstage[2]

    def get_equipment_list(self):
        el = self.equipment_list
        if len(el) == 0:
            if self.fixed_mass > 0:
                el['fixed_mass'] = self.fixed_mass

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                el[subsystem] = self.get(subsystem).get_equipment_list()
        return el

    def get_mass_properties(self):
        """ calculate mass properties """
        Cg = 0
        Mx = 0
        My = 0
        Mz = 0
        Ixx = 0
        Iyy = 0
        Izz = 0
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            """roll up properties from subsystems """
            xparent = self.x
            for subsystem in subsystems:
                self.get(subsystem).get_mass_properties()
                xorigin = subsystem.x + xparent
                self.Mx += (subsystem.dry_mass*xorigin)
                self.My += (subsystem.dry_mass*subsystem.y)
                self.Mz += (subsystem.dry_mass*subsystem.z)
            moments = [self.Mx,self.My,self.Mz]
            self.Cg = [moment/self.dry_mass for moment in moments]
            #Need to include (self.Cg[1] - Cgrocket[1]), etc...See Excel T-V
            self.Ixx = self.dry_mass*((self.Cg[1])**2 + (self.Cg[2])**2)
            self.Iyy = self.dry_mass*((self.Cg[0])**2 + (self.Cg[2])**2)
            self.Izz = self.dry_mass*((self.Cg[0])**2 + (self.Cg[1])**2)
        else:
            #Ioxx, Ioyy, Iozz depends on shape, length, radius
            #if shape == 'Solid_Cylinder':
            #    #calculations
            #elif shape == 'Hollow_Thin-Wall_Cylinder':
            #    #calculations
            #else:
            #    #Other: need Cg calculated elsewhere
            self.Cg = [self.x, self.y, self.z]
            self.Mx = self.x*self.dry_mass
            self.My = self.y*self.dry_mass
            self.Mz = self.z*self.dry_mass
            #Need to include (self.y - Cgrocket[1]), etc...See Excel T-V
            self.Ixx = self.dry_mass*((self.y)**2 + (self.z)**2)
            self.Iyy = self.dry_mass*((self.x)**2 + (self.z)**2)
            self.Izz = self.dry_mass*((self.x)**2 + (self.y)**2)    

        return (Cg, Mx, My, Mz, Ixx, Iyy, Izz)

    def log(self, *args):
        logger = logging.getLogger('mission')
        msg = ''
        for arg in args:
            msg += str(arg) + ' '
        logger.info(msg.rstrip(' '))

# end SubSystem
