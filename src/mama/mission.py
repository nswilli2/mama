"""
   mission.py
"""

import sys
import logging
import StringIO

from openmdao.main.api import Component, Assembly
from openmdao.lib.datatypes.api import Float, Int, Str, Slot, List, Array

from spacecraft import Spacecraft
from maneuver import Maneuver, Orbit


class Phase(Component):
    """ A phase of a mission. """

    spacecraft = Slot(Spacecraft,
        desc='the spacecraft that performs the mission phase')

    orbit = Slot(Orbit,
        desc='orbital parameters')

    maneuver = Slot(Maneuver,
        desc='a delta-V maneuver')

    # inputs
    description = Str(iotype='in',
        desc='description of the mission phase')

    duration = Float(0.0, iotype='in',
        desc='duration of phase, used for boiloff and crew consumable calculations')

    stage = Int(-1, iotype='in',
        desc='spacecraft stage involved in this phase (-1 indicates entire spacecraft)')

    crew = Int(0, iotype='in',
        desc='number of crew onboard for phase, used to calculate crew consumables')

    expend_fuel = Float(0.0, iotype='in',
        desc='mass of fuel jettisoned at end of phase (temporary standin for Cooldown logic)')

    fuel_stage = Int(0, iotype='in',
        desc='stage from which fuel is expended')

    expend_prop = Float(0.0, iotype='in',
        desc='mass of RCS propellant jettisoned at end of phase (temporary standin for spinup/spindown logic)')

    prop_stage = Int(0, iotype='in',
        desc='stage from which RCS propellant is expended')

    # drop_mass = Float(0.0, iotype='in',
    #     desc='fixed mass jettisoned at end of phase')

    # drop_stage = Int(0, iotype='in',
    #     desc='stage from which mass is dropped')

    drop_subsystem = Str('', iotype='in',
        desc='subsystem from which mass is dropped')

    pickup_mass = Float(0.0, iotype='in',
        desc='fixed mass picked up or added at end of phase')

    pickup_stage = Int(0, iotype='in',
        desc='stage to which mass is added')

    beg_mass = Float(0.0, iotype='in',
        desc='mass of spacecraft at beginning of phase')

    beg_MET = Float(0.0, iotype='in',
        desc='mission elapsed time at beginning of phase')

    # outputs
    end_mass = Float(0.0, iotype='out',
        desc='mass of spacecraft at end of phase')

    end_MET = Float(0.0, iotype='out',
        desc='mission elapsed time at end of phase')

    end_fuel = Float(0.0, iotype='out',
        desc='fuel remaining at end of phase')

    end_prop = Array(dtype=Float, iotype='out',
        desc='RCS propellant remaining at end of phase')

    def add_maneuver(self, maneuver):
        """ add a maneuver to the phase
        """
        self.add('maneuver', maneuver)

    def display(self, output=sys.stdout):
        """ display details about this mission phase.
        """

        print >> output, 'Mission phase:', self.description
        print >> output, '    has a duration of', self.duration, 'days'
        print >> output, '    with', self.crew, 'crew members'

        if self.orbit:
            print >> output, '    ', self.orbit

        if self.maneuver:
            self.maneuver.display(output)

        if self.drop_mass > 0:
            print >> output, '  drop ', self.drop_mass, 'mt of mass from stage', self.drop_stage

        if self.pickup_mass > 0:
            print >> output, '  pick up ', self.pickup_mass, 'mt of mass, add to stage', self.pickup_stage

        print >>output, ''

    def execute(self):
        """ Simulates the phase.
        """

        self.logger = logging.getLogger('mission')

        self.log('\f')  # form feed, new page for each mission phase
        self.log('MET:', self.beg_MET, 'days')
        self.log('Executing phase "' + self.description + '"',
                         'over duration of', self.duration, 'days',
                         'with', self.crew, 'crew')

        self.log('    start mass:', self.parent.spacecraft.wet_mass)

        # print self.name+'.beg_mass    = ', self.beg_mass
        # print self.name+'.beg_MET     = ', self.beg_MET

        mass_effect = False

        # if only one stage of the spacecraft is involved,
        # set working spacecraft to be only that one stage
        spacecraft = self.parent.spacecraft
        if self.stage >= 0:
            spacecraft = spacecraft.get_stage(self.stage)

        if self.duration > 0:
            spacecraft.expend_consumables(self.duration)
            spacecraft.boil_off(self.duration)
            mass_effect = True

        # TODO: handle BIGDV (C3 or AeroBraking)
        # TODO: handle orbit raising (diff apogee/perigee than previous phase)

        if self.maneuver:
            self.log('')
            self.maneuver.execute(spacecraft)
            mass_effect = True

        if self.expend_fuel > 0:
            self.log('    expend_fuel', self.expend_fuel, 'from stage', self.fuel_stage)
            spacecraft.expend_fuel(self.fuel_stage, self.expend_fuel)
            mass_effect = True

        if self.expend_prop > 0:
            self.log('    expend_prop', self.expend_prop, 'from stage', self.prop_stage)
            spacecraft.expend_prop(self.prop_stage, self.expend_prop)
            mass_effect = True

        if self.drop_subsystem:
            self.log('    drop subsystem', self.drop_subsystem)
            spacecraft.drop(self.drop_subsystem)
            mass_effect = True

        # if self.drop_mass > 0:
        #     self.log('    drop_mass', self.drop_mass)
        #     spacecraft.drop_mass(self.drop_stage, self.drop_mass)
        #     mass_effect = True

        if self.pickup_mass > 0:
            self.log('    pickup_mass', self.pickup_mass)
            spacecraft.pickup_mass(self.pickup_stage, self.pickup_mass)
            mass_effect = True

        # update mass for the spacecraft
        if mass_effect:
            self.parent.spacecraft.update_wet_mass()
            self.log('')
            self.log(str(self.parent.spacecraft))

        self.end_MET = self.beg_MET + self.duration
        self.log('    end MET:', self.end_MET, 'days')

        self.end_mass = self.parent.spacecraft.wet_mass
        self.log('    end mass:', self.end_mass)

        self.end_fuel = self.parent.spacecraft.get_fuel()
        self.log('    end fuel:', self.end_fuel)

        self.end_prop = self.parent.spacecraft.get_prop()
        self.log('    end prop:', self.end_prop)

        # print self.name+'.end_mass    = ', self.end_mass
        # print self.name+'.end_MET     = ', self.end_MET

        # print self.name+'.end_fuel    = ', self.end_fuel
        # for i in range(0, len(self.end_prop)-1):
        #     print self.name+'.end_prop['+str(i)+'] = ', self.end_prop[i]

    def log(self, *args):
        logger = logging.getLogger('mission')
        msg = ''
        for arg in args:
            msg += str(arg) + ' '
        logger.info(msg.rstrip(' '))


class Mission(Assembly):
    """ A mission with multiple phases. """

    description = Str(iotype='in',
        desc='description of the mission')

    spacecraft = Slot(Spacecraft, required=True,
        desc='the spacecraft')

    phases = List(Phase, iotype='in')

    beg_MET = Float(0.0, iotype='in',
        desc='mission elapsed time at beginning of mission')

    def configure(self):
        """ link up the spacecraft and mission phases in order
        """
        # print "Mission.configure()"

        if self.spacecraft is None:
            # put a temporary placeholder spacecraft in the Slot
            self.add('spacecraft', Spacecraft())

        self.driver.workflow.add(['spacecraft'])
        beg_MET  = 'beg_MET'
        beg_mass = 'spacecraft.wet_mass'

        # add mission phases to workflow and link them up
        for phase in self.phases:
            phase.force_execute = True
            self.driver.workflow.add(phase.name)

            self.connect(beg_MET, phase.name + '.beg_MET')
            beg_MET = phase.name + '.end_MET'

            self.connect(beg_mass, phase.name + '.beg_mass')
            beg_mass = phase.name + '.end_mass'

        self.create_passthrough(beg_mass, alias='end_mass')
        self.create_passthrough(beg_MET,  alias='end_MET')
        self.create_passthrough(phase.name + '.end_fuel')
        self.create_passthrough(phase.name + '.end_prop')
        self.force_execute = True

    def execute(self):
        """ instrumented execute function
        """

        # reset the log
        self.initialize_log()

        self.logger.info('=======================================================================================')
        self.logger.info('\nExecuting mission...\n')

        super(Mission, self).execute()

        self.logger.info('\nMission Complete...\n')

        self.logger.info(str(self.spacecraft))

        self.logger.info('=======================================================================================')
        self.logger.info('\f')  # form feed

    def display(self, output=sys.stdout):
        """ display the mission
        """
        print >>output, 'Mission:', self.description
        print >>output, ''
        if self.spacecraft is not None:
            self.spacecraft.display(output=output)
        else:
            print >>output, 'No spacecraft is assigned.'
        print >>output, ''
        print >>output, 'Phases:'
        for phase in self.phases:
            phase.display(output=output)

    def add_phase(self, name, phase):
        """ add phase to the mission
        """
        self.add(name, phase)
        self.phases.append(phase)

    def get_phase(self, n):
        """ get the nth phase of the mission
        """
        return self.phases[n]

    def initialize_log(self):
        """ initialize the mission log
        """
        self.logger = logging.getLogger('mission')
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)

        self.logstr = StringIO.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.logstr))
        self.logger.setLevel(logging.INFO)
