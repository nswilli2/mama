"""
   subsystems.py
"""

from openmdao.lib.datatypes.api import *

from subsystem import Subsystem
from tank import Tank

from zope.interface import Interface, Attribute, implements


class IPropulsion(Interface):
    """Interface for a subsystem that provides propulsion."""

    thrust = Attribute("Thrust")

    Isp = Attribute("Specific Impulse")


class IRCS(Interface):
    """Interface for a subsystem that provides reaction control."""

    thrust = Attribute("Thrust")

    Isp = Attribute("Specific Impulse")

    def get_prop():
        """Get mass of propellant in the RCS system.
        """

    def add_prop(prop):
        """Add propellant to the RCS system.
        """

    def expend_prop(prop):
        """ Expend propellant from the RCS system.
        """


class IFuelSystem(Interface):
    """Interface for a subsystem that provides fuel."""

    def get_fuel():
        """Get mass of fuel in the fuel system.
        """

    def add_fuel(fuel):
        """Add fuel to the fuel system.
        """

    def expend_fuel(fuel):
        """ Expend fuel from the fuel system.
        """


class IExpendable(Interface):
    """ Interface for a subsystem than can be jettisoned. """

    dropped = Attribute("flag indicating if the subsystem has been dropped")

    def drop():
        """ drop expendable mass
        """


class CargoSubsystem(Subsystem):
    """ a Fuel Subsystem. """

    implements(IExpendable)

    # outputs
    mass_cargo = Float(0.0, iotype='in',
        desc='mass of cargo')

    @property
    def dropped(self):
        """flag indicating if the subsystem has been dropped."""
        return self._dropped

    def configure(self):
        """ configure the fuel tank subsystem
        """
        self.force_execute = True  # force execution to 'undrop' expendable subsystem
        self._dropped = False

    def execute(self):
        """ reset dropped flag before executing
        """
        self._dropped = False
        super(CargoSubsystem, self).execute()

    def drop(self):
        """ drop expendable hardware
        """
        # print "DROPPING", self.get_pathname(), self
        self._dropped = True

        self.dry_mass = self.fixed_mass
        self.wet_mass = self.fixed_mass

    def update_dry_mass(self):
        """ Update the dry mass of the subsystem.
            Overridden: if dropped, then dry mass is just the fixed mass
        """
        self.dry_mass = self.fixed_mass * (1 + self.dwc)
        if not self._dropped:
            self.dry_mass += self.mass_cargo

    def update_wet_mass(self):
        """ Update the wet mass of the subsystem.
        """
        # wet_mass is always same as dry mass
        self.wet_mass = self.dry_mass


class MMOD(Subsystem):
    # inputs
    area = Float(0.0, iotype='in', units='m**2',
        desc='area to be protected')

    def update_dry_mass(self):
        self.dry_mass = self.area * 3.0


class TPS(Subsystem):
    """ thermal protection system (insulation) """
    # inputs
    area = Float(0.0, iotype='in', units='m**2',
        desc='area of tank')

    def configure(self):
        self.force_execute = True  # why do I have to do this?

    def update_dry_mass(self):
        # from "Space2013_LNTR_SKB.doc":
        # 1" of SOFI (~0.78 kg/m^2) + 60 layers of MLI (~0.90 kg/m^2)
        self.dry_mass = self.area * (0.78 + 0.90)


class FuelSubsystem(Subsystem):
    """ a Fuel Subsystem. """

    implements(IFuelSystem, IExpendable)

    # inputs

    fuel_density = Float(70.85, iotype='in',  # kg/m**3
        desc='fuel density, default is LH2 (wikipedia.org/wiki/Liquid_hydrogen)')

    # outputs

    boil_off_rate = Float(0.003, iotype='out',
        desc='fuel boil off rate, fraction (percentage) per month')

    @property
    def dropped(self):
        """flag indicating if the subsystem has been dropped."""
        return self._dropped

    def configure(self):
        """ configure the fuel tank subsystem
        """
        self.add('tank', Tank())
        self.connect('fuel_density', 'tank.fuel_density')

        self.add('mmod', MMOD())
        self.connect('tank.area', 'mmod.area')

        self.add('tps', TPS())
        self.connect('tank.area', 'tps.area')

        self.create_passthrough('tank.capacity')
        self.create_passthrough('tank.diameter')
        self.create_passthrough('tank.volume')
        self.create_passthrough('tank.inner_diameter')
        self.create_passthrough('tank.dry_mass', alias='mass_tank')

        self._dropped = False

        # force execution to 'undrop' expendable subsystems from any previous runs
        self.force_execute = True
        self.tank.force_execute = True
        self.mmod.force_execute = True
        self.tps.force_execute = True

        super(FuelSubsystem, self).configure()

    def execute(self):
        """ reset dropped flag before executing
        """
        self._dropped = False
        self.total_boiloff = 0
        self.log('  ', self.parent.name, self.name,
                'capacity:', self.capacity)
        super(FuelSubsystem, self).execute()

    def get_fuel(self):
        """ get the amount of fuel in the tank
        """
        if not self._dropped:
            return self.tank.fuel
        else:
            return 0

    def available_fuel(self):
        """ get the amount of fuel in the tank that is available
            (excludes trapped residuals)
        """
        if not self._dropped and self.tank.fuel > self.tank.residual_fuel:
            return self.tank.fuel - self.tank.residual_fuel
        else:
            return 0

    def add_fuel(self, fuel=None):
        """ add the specified mass of fuel to the tank
            if fuel is not specified, fill to capacity
            (wet mass is recalculated)
        """
        if not self._dropped:
            self.tank.add_fuel(fuel)
            self.update_wet_mass()

    def expend_fuel(self, fuel):
        """ remove the specified mass of fuel from the tank
            (wet mass is recalculated)
        """
        if not self._dropped:
            self.tank.expend_fuel(fuel)
            self.update_wet_mass()

    def boil_off(self, duration):
        """ expend fuel boil-off based on duration and boil-off rate
            rate is per month (30.5 days) i.e. 0.003 is 0.3% per month.
            calculated from initial propellant load (not remaining)
            because it is a function of tank size
        """
        # TODO: calculate based on TLI & tank surface area, etc
        #       see McCurdy e-mail 3/1/2013, "Boil_Off_Calculation1.xls"
        if not self._dropped and self.tank.fuel > 0:
            boil_off = self.tank.capacity * self.boil_off_rate/30.5 * duration
            self.log('    ', self.parent.name, self.name, self.tank.fuel,
                    'boil_off @ %2.2f%% per day:' % (100*self.boil_off_rate/30.5),
                     boil_off)
            boil_off = min(boil_off, self.tank.fuel)
            self.expend_fuel(boil_off)
            self.total_boiloff += boil_off
            self.log('    ', self.parent.name, self.name,
                    'total boil_off:', self.total_boiloff)
            return boil_off
        else:
            self.log('    ', self.parent.name, self.name, self.tank.fuel,
                    'no boil off')
            return 0

    def drop(self):
        """ drop expendable hardware
        """
        # print "DROPPING", self.get_pathname(), self
        self._dropped = True

        self.tank.fuel = 0

        subsystems = self.get_children(Subsystem)
        if len(subsystems) > 0:
            for name in subsystems:
                subsystem = self.get(name)
                # print "DROPPING Subsystem", name, subsystem
                subsystem.dry_mass = 0
                subsystem.wet_mass = 0

        self.dry_mass = self.fixed_mass
        self.wet_mass = self.fixed_mass

    def update_dry_mass(self):
        """ Update the dry mass of the subsystem.
            Overridden: if dropped, then dry mass is just the fixed mass
        """
        if self._dropped:
            self.dry_mass = self.fixed_mass * (1 + self.dwc)
        else:
            super(FuelSubsystem, self).update_dry_mass()

    def update_wet_mass(self):
        """ Update the wet mass of the subsystem.
            Overridden: if dropped, then wet mass is just the fixed (dry) mass
        """
        if self._dropped:
            self.wet_mass = self.dry_mass
        else:
            super(FuelSubsystem, self).update_wet_mass()
