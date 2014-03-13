"""
   spacecraft.py
"""

import sys
import StringIO

from subsystem import Subsystem
from openmdao.lib.datatypes.api import Str, Float, Int, List, Slot

from subsystems import IPropulsion, IRCS, IFuelSystem
from openmdao.main.mp_support import has_interface

from math import exp


class Stage(Subsystem):

    # inputs
    crew_count = Int(0, iotype='in',
        desc='number of crew members for this stage')

    def drop_mass(self, mass):
        """ add to fixed mass of stage
            TODO: implement a payload or cargo mass
        """
        self.dry_mass = self.dry_mass - mass

    def pickup_mass(self, mass):
        """ remove from fixed mass of stage
            TODO: implement a payload or cargo mass
        """
        self.dry_mass = self.dry_mass + mass

    def get_fuel(self):
        """ get the mass of fuel on the specified stage
        """
        fuelsystem = self.get_children(IFuelSystem)
        if len(fuelsystem) < 1:
            return 0.0
        elif len(fuelsystem) > 1:
            raise Exception(self, 'has multiple fuel tanks')
        else:
            fuelsystem = self.get(fuelsystem[0])
            return fuelsystem.get_fuel()

    def add_fuel(self, fuel=None):
        """ add the specified mass of fuel to the specified stage
            if fuel mass is not specified, add the full capacity of fuel
        """
        fuelsystem = self.get_children(IFuelSystem)
        # self.log('  ', self.description, 'add fuel to fuelsystem:', fuelsystem)
        if len(fuelsystem) < 1:
            self.log('  ', self.name, 'has no fuel tank')
        elif len(fuelsystem) > 1:
            raise Exception(self, 'has multiple fuel tanks')
        else:
            fuelsystem = self.get(fuelsystem[0])
            fuelsystem.add_fuel()
            # fuelsystem.tank.display()
            self.update_wet_mass()

    def expend_fuel(self, fuel):
        """ remove the specified mass of fuel from the specified stage
        """
        fuelsystem = self.get_children(IFuelSystem)
        if len(fuelsystem) < 1:
            raise Exception(self, 'has no fuel tank')
        elif len(fuelsystem) > 1:
            raise Exception(self, 'has multiple fuel tanks')
        else:
            fuelsystem = self.get(fuelsystem[0])
            self.log('    expending', fuel, 'kg of fuel from', self.name, fuelsystem.name)
            fuelsystem.expend_fuel(fuel)
            self.update_wet_mass()

    def get_prop(self):
        """ get the mass of RCS propellant on the specified stage
        """
        propsystem = self.get_children(IRCS)
        if len(propsystem) < 1:
            return 0.0
        elif len(propsystem) > 1:
            raise Exception(self, 'has multiple RCS systems')
        else:
            propsystem = self.get(propsystem[0])
            return propsystem.get_prop()

    def add_prop(self, prop=None):
        """ add the specified mass of RCS prop to the specified stage
            if prop mass is not specified, add the full capacity of prop
        """
        propsystem = self.get_children(IRCS)
        self.log(self.description, 'add prop to propsystem:', propsystem)
        if len(propsystem) < 1:
            self.log(self.name, 'has no RCS')
        elif len(propsystem) > 1:
            self.log(self.name, 'has multiple RCS')
        else:
            propsystem = self.get(propsystem[0])
            propsystem.add_prop()
            # propsystem.display()
            self.update_wet_mass()

    def expend_prop(self, prop):
        """ remove the specified mass of RCS prop from the specified stage
        """
        propsystem = self.get_children(IRCS)
        if len(propsystem) < 1:
            raise Exception(self, 'has no RCS')
        elif len(propsystem) > 1:
            raise Exception(self, 'has multiple RCS')
        else:
            propsystem = self.get(propsystem[0])
            self.log('    expending', prop, 'kg of prop from', self.name, propsystem.name)
            propsystem.expend_prop(prop)
            self.update_wet_mass()

    def expend_consumables(self, duration):
        """ calculates and jettisons crew consumable mass
        """
        if self.crew_count > 0:
            consumption = self.crew_consumable_rate * duration * self.crew_count
            self.log('    expending consumables from', self.name, consumption)
            self.drop_mass(consumption)

    def boil_off(self, duration):
        """ calculates and expends fuel boil-off based on duration
        """
        fuel_systems = self.get_children(IFuelSystem)
        for fuel_system in fuel_systems:
            self.get(fuel_system).boil_off(duration)

    def burn(self, dV, stage=None, bulk_reserve=0., dV_reserve=0., Isp_reserve=0., other_reserve=0.):
        """ calculates the nominal propellant required for the specified delta-V (PMNOM).
            It also calculates reserve propellants and expends the total propellant burned (PROP).
            For burns where thrust (or T/W) was specified, this routine also calculates final T/W
            ratio of the burn and the burn duration (in minutes).
        """
        if dV > 0.1:
            # use main propulsion
            prop_systems = self.get_children(IPropulsion)
        else:
            # use RCS
            prop_systems = self.get_children(IRCS)

        prop_system = self.get(prop_systems[0])
        thrust = prop_system.thrust
        TW = prop_system.thrust / self.wet_mass
        Isp = prop_system.Isp

        self.log('    burning fuel from %s %s' % (self.name, prop_system.name),
                '(thrust = %1.1f, Isp = %1.1f) for delta-V of %1.3f' % (thrust, Isp, dV))

        res1 = bulk_reserve
        res2 = 1.0 + dV_reserve
        res3 = 1.0 - Isp_reserve
        res4 = other_reserve

        mass = self.wet_mass

        g = 9.8062E-3  # gravitational constant

        # use rocket equation to calculate nominal fuel burn
        fuel_nominal = mass * (1.-(1./exp(dV/(Isp*g))))

        res1 = fuel_nominal * res1
        res2 = mass*(1.0-(1.0/exp(dV*res2/(Isp*g))))-fuel_nominal
        res3 = mass*(1.0-(1.0/exp(dV/(Isp*res3*g))))-fuel_nominal
        res4 = fuel_nominal * res4

        fuel_nominal = fuel_nominal
        fuel_burn = fuel_nominal + res1 + res2 + res3 + res4

        self.log('    nominal fuel burn = %1.3f' % fuel_nominal)
        self.log('    fuel burn with reserve = %1.3f' % fuel_burn)

        if has_interface(prop_system, IPropulsion):
            # add any fuel burn required for engine cooldown
            if prop_system.cooldown_burn > 0:
                fuel_burn = fuel_burn * (1 + prop_system.cooldown_burn)
                self.log('    fuel burn with cooldown = %1.3f' % fuel_burn)
            self.expend_fuel(fuel_burn)
        else:
            # expend fuel from the RCS system that was used
            self.expend_prop(fuel_burn)

        # final thrust to weight & burn time
        TWfinal = thrust/(mass - fuel_nominal)
        burn_time = (fuel_nominal*Isp/TW)/60.0

        self.log('    thrust/weight, initial = %1.3f\n' % TW,
                '    thrust/weight, final = %1.3f\n' % TWfinal,
                '    burn time = %1.3f' % burn_time)

        return burn_time


class Spacecraft(Subsystem):
    """ A spacecraft with multiple stages. """

    description = Str(iotype='in',
        desc='description of the spacecraft')

    stages = List(Slot(Stage, required=True), iotype='in',
        desc='list of spacecraft stages')

    crew_consumable_rate = Float(0.0, iotype='in',
        desc='crew consumable rate in mt/person/day')

    def execute(self):
        """ instrumented execute function
        """
        self.log('\nExecuting spacecraft:', self.description)
        self.add_fuel()  # fill all fuel tanks to capacity
        super(Spacecraft, self).execute()
        self.log('')
        self.log(self)

    def __str__(self):
        output = StringIO.StringIO()
        self.display(output=output)
        return output.getvalue()

    def display(self, indent=0, output=sys.stdout):
        """ displays details about the spacecraft.
        """
        print >>output, '%s%-20.20s\tdry:%10.2f\twet:%10.2f' \
            % ('  '*indent, self.name, self.dry_mass, self.wet_mass)
        for stage in self.stages:
            stage.display(indent+1, output=output)
            print >>output, ''

        # extra: display total fuel boiloff
        # total_boiloff = 0
        # for stage in self.stages:
        #     fuel_systems = stage.get_children(IFuelSystem)
        #     for fuel_system in fuel_systems:
        #         ss = stage.get(fuel_system)
        #         print ' ', stage.name, ss.name, 'total boil_off =', ss.total_boiloff
        #         total_boiloff += ss.total_boiloff
        # print '  total boil_off =', total_boiloff

    def add_stage(self, name, stage):
        """ add a stage to the spacecraft
        """
        self.add(name, stage)
        self.stages.append(stage)
        self.driver.workflow.add(name)

    def get_stage(self, n):
        """ get the specified stage of the spacecraft
            if n is an integer get the nth stage, else assume n is the name of the stage
            (stages numbering starts at zero for core stage)
        """
        if type(n) is int:
            return self.stages[n]
        else:
            return self.get(n)

    def get_fuel(self, stage=None):
        """ get the mass of fuel currently on the spacecraft
        """
        if stage:
            return self.get_stage(stage).get_fuel()
        else:
            fuel = 0.0
            for stage in self.stages:
                fuel = fuel + stage.get_fuel()
            return fuel

    def add_fuel(self, stage=None, fuel=None):
        """ add the specified mass of fuel to the specified stage
            if stage is None, fuel all stages
            if fuel is None, fill to capacity
        """
        if stage:
            self.get_stage(stage).add_fuel(fuel)
        else:
            for stage in self.stages:
                stage.add_fuel(fuel)
        self.update_wet_mass()

    def expend_fuel(self, stage, fuel):
        """ remove the specified mass of fuel from the specified stage
        """
        self.get_stage(stage).expend_fuel(fuel)
        self.update_wet_mass()

    def get_prop(self, stage=None):
        """ get the mass of RCS propellant currently on the spacecraft
        """
        if stage:
            return self.get_stage(stage).get_prop()
        else:
            prop = []
            for stage in self.stages:
                prop.append(stage.get_prop())
            return prop

    def add_prop(self, stage, fuel):
        """ add the specified mass of RCS propellant to the specified stage
            if stage is None, fuel all stages
            if fuel is None, fill to capacity
        """
        self.get_stage(stage).add_prop(fuel)
        self.update_wet_mass()

    def expend_prop(self, stage, fuel):
        """ remove the specified mass of fuel from the specified stage
        """
        self.get_stage(stage).expend_prop(fuel)
        self.update_wet_mass()

    def drop(self, subsystem):
        """ drop the specified subsystem and update masses
        """
        self.get(subsystem).drop()
        self.update_dry_mass()
        self.update_wet_mass()

    # def drop_mass(self, stage, mass):
    #     """ subtract the specified mass from the stage
    #     """
    #     self.get_stage(stage).drop_mass(mass)
    #     self.update_dry_mass()
    #     self.update_wet_mass()

    def pickup_mass(self, stage, mass):
        """ add the specified mass to the stage
        """
        self.get_stage(stage).pickup_mass(mass)
        self.update_dry_mass()
        self.update_wet_mass()

    def expend_consumables(self, duration):
        """ calculates and jettisons crew consumable mass
        """
        for stage in self.stages:
            if stage.crew_count > 0:
                consumption = self.crew_consumable_rate * duration * stage.crew_count
                self.log('    expending consumables from', stage.name, consumption)
                stage.drop_mass(consumption)

    def boil_off(self, duration):
        """ calculates and expends fuel boil-off based on duration
        """
        for stage in self.stages:
            fuel_systems = stage.get_children(IFuelSystem)
            for fuel_system in fuel_systems:
                stage.get(fuel_system).boil_off(duration)

    def burn(self, dV, stage, bulk_reserve=0., dV_reserve=0., Isp_reserve=0., other_reserve=0.):
        """ calculates the nominal propellant required for the specified delta-V (PMNOM).
            It also calculates reserve propellants and expends the total propellant burned (PROP).
            For burns where thrust (or T/W) was specified, this routine also calculates final T/W
            ratio of the burn and the burn duration (in minutes).
        """

        if dV > 0.1:
            # use main propulsion
            prop_stage = self.get_stage(0)
            prop_systems = prop_stage.get_children(IPropulsion)
        else:
            # use RCS from the specified stage
            prop_stage = self.get_stage(stage)
            prop_systems = prop_stage.get_children(IRCS)

        prop_system = prop_stage.get(prop_systems[0])
        thrust = prop_system.thrust
        TW = prop_system.thrust / self.wet_mass
        Isp = prop_system.Isp

        self.log('    burning fuel from %s %s' % (prop_stage.name, prop_system.name),
                '(thrust = %1.1f, Isp = %1.1f) for delta-V of %1.3f' % (thrust, Isp, dV))

        res1 = bulk_reserve
        res2 = 1.0 + dV_reserve
        res3 = 1.0 - Isp_reserve
        res4 = other_reserve

        mass = self.wet_mass
        self.log('    initial mass =', mass)

        g = 9.8062E-3  # gravitational constant

        # use rocket equation to calculate nominal fuel burn
        fuel_nominal = mass * (1.-(1./exp(dV/(Isp*g))))

        res1 = fuel_nominal * res1
        res2 = mass*(1.0-(1.0/exp(dV*res2/(Isp*g))))-fuel_nominal
        res3 = mass*(1.0-(1.0/exp(dV/(Isp*res3*g))))-fuel_nominal
        res4 = fuel_nominal * res4

        fuel_nominal = fuel_nominal
        fuel_burn = fuel_nominal + res1 + res2 + res3 + res4

        self.log('    nominal fuel burn = %1.3f' % fuel_nominal)
        self.log('    fuel burn with reserve = %1.3f' % fuel_burn)

        if has_interface(prop_system, IPropulsion):
            # add any fuel burn required for engine cooldown
            if prop_system.cooldown_burn > 0:
                fuel_burn = fuel_burn * (1 + prop_system.cooldown_burn)
                self.log('    fuel burn with %2.0f%% cooldown = %1.3f'
                        % (prop_system.cooldown_burn*100, fuel_burn))

            # fuel will be burned from forward stages first
            stage_idx = len(self.stages) - 1
            while stage_idx > 0 and fuel_burn > 0:
                # self.log('checking fuel in stage', stage_idx, self.stages[stage_idx].name)
                fuel_systems = self.stages[stage_idx].get_children(IFuelSystem)
                if len(fuel_systems) > 0:
                    avail_fuel = self.stages[stage_idx].get(fuel_systems[0]).available_fuel()
                    if avail_fuel > 0:
                        stage_burn = min(fuel_burn, avail_fuel)
                        # self.log('burning', stage_burn, 'kg fuel from', self.stages[stage_idx].name)
                        self.stages[stage_idx].expend_fuel(stage_burn)
                        fuel_burn = fuel_burn - stage_burn
                    else:
                        self.log('    no fuel available from', self.stages[stage_idx].name)
                stage_idx = stage_idx - 1
            # take the rest from core stage
            if fuel_burn > 0:
                # self.log('burning remaining', fuel_burn, 'kg fuel from', self.stages[0].name)
                self.stages[0].expend_fuel(fuel_burn)
        else:
            # expend fuel from the RCS system that was used
            self.expend_prop(stage, fuel_burn)

        # final thrust to weight & burn time
        TWfinal = thrust/(mass - fuel_nominal)
        self.log('    final mass =', mass)
        self.log('    thrust/weight: initial = %1.3f' % TW, ', final = %1.3f\n' % TWfinal)

        burn_time = (fuel_nominal*Isp/TW)/60.0
        self.log('    burn time = %1.3f' % burn_time)

        return burn_time
