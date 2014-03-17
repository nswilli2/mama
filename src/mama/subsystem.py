"""
   subsystem.py
"""

import sys
import logging

from zope.interface import Interface

from openmdao.main.api import Component, Assembly
from openmdao.lib.datatypes.api import Str, Float, Array
from openmdao.main.mp_support import has_interface

from mga import get_MGA


class Summation(Component):
    """ A component that sums it's input values
    """

    inputs = Array(dtype=Float, iotype='in',
        desc='list of input values to be summed')

    output = Float(0.0, iotype='out',
        desc='sum of input values')

    def __init__(self):
        super(Summation, self).__init__()
        self.force_execute = True

    def execute(self):
        self.output = sum(self.inputs)


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

    # outputs

    dry_mass = Float(0., iotype='out', units='kg',
         desc='calculated dry mass of subsystem in kg')

    dwc = Float(0.0, iotype='out',
        desc='dry weight contingency (based on mass category and maturity)')

    wet_mass = Float(0., iotype='out', units='kg',
         desc='calculated wet mass of subsystem in kg')

    power_usage = Float(0., iotype='out', units='kW',
         desc='calculated electrical power used by subsystem')

    # methods

    def add_summation(self, subsystems, name):
        """ add a summation component to calculate the named output
            as a summation of that output from the subsystems
        """
        summation = Summation()
        summation.inputs.resize(len(subsystems))
        sum_name = '%s_%s' % ('sum', name)
        self.add(sum_name, summation)
        self.add_to_workflow([sum_name])

        i = 0
        for subsystem in subsystems:
            inputs_i = '%s.inputs[%d]' % (sum_name, i)
            self.connect('%s.%s' % (subsystem, name), inputs_i)
            i = i + 1
        self.connect(sum_name + '.output', name)

    def configure(self):
        """ if subsystem has child subsystems, add a Summation component.
        """
        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            self.add_to_workflow(subsystems)
            # self.add_summation(subsystems, 'dry_mass')
            # self.add_summation(subsystems, 'wet_mass')

            # this SHOULD work the same:
            dry_masses = [subsystem + '.dry_mass' for subsystem in subsystems]
            wet_masses = [subsystem + '.wet_mass' for subsystem in subsystems]
            # print self.name+'.connect('+'+'.join(dry_masses)+", 'dry_mass')"
            # print self.name+'.connect('+'+'.join(wet_masses)+", 'wet_mass')"
            self.connect('+'.join(dry_masses), 'dry_mass')
            self.connect('+'.join(wet_masses), 'wet_mass')

        super(Subsystem, self).configure()

    def execute(self):
        """ Calculates subsystem dependent properties from input parameters.
            The default is just to update the dry and wet masses.
        """
        if len(self.driver.workflow) > 0:
            super(Subsystem, self).execute()

        self.dwc = get_MGA(self.mass_category, self.mass_maturity)
        self.update_dry_mass()
        self.update_wet_mass()
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

    def display(self, indent=0, output=sys.stdout):
        """ display details about the subsystem
        """
        wetness = self.wet_mass - self.dry_mass
        if wetness == 0:
            print >>output, '%s%-15s\tfixed:%10.2f\tdry:%10.2f\twet:%10.2f' \
                % ('  '*indent, self.name, self.fixed_mass*(1+self.dwc), self.dry_mass, self.wet_mass)
        else:
            print >>output, '%s%-15s\tfixed:%10.2f\tdry:%10.2f\twet:%10.2f\t(%10.2f)' \
                % ('  '*indent, self.name, self.fixed_mass*(1+self.dwc), self.dry_mass, self.wet_mass, wetness)

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for subsystem in subsystems:
                self.get(subsystem).display(indent+1, output)

    def log(self, *args):
        logger = logging.getLogger('mission')
        msg = ''
        for arg in args:
            msg += str(arg) + ' '
        logger.info(msg.rstrip(' '))

# end SubSystem
