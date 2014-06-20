"""
   subsystems.py
"""

from openmdao.lib.datatypes.api import *

from subsystem import Subsystem

from zope.interface import Interface, Attribute, implements


class IPropulsion(Interface):
    """Interface for a component/subsystem that provides propulsion."""

    thrust = Attribute("Thrust")

    Isp = Attribute("Specific Impulse")


class IRCS(Interface):
    """Interface for a component/subsystem that provides reaction control."""

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
    """Interface for a component/subsystem that provides fuel."""

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
    """ Interface for a component/subsystem than can be jettisoned. """

    dropped = Attribute("flag indicating if the subsystem has been dropped")

    def drop():
        """ drop expendable mass
        """


class CargoSubsystem(Subsystem):
    """ a Cargo Subsystem. """

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

        self.add('cargo', Equipment())

    def execute(self):
        """ reset dropped flag before executing
        """
        self._dropped = False

        self.cargo.mass = self.mass_cargo

        super(CargoSubsystem, self).execute()

    def drop(self):
        """ drop expendable hardware
        """
        # print "DROPPING", self.get_pathname(), self
        self._dropped = True

        self.cargo.mass = 0
