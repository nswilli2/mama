"""
   mga.py
"""

MGA_enabled = False

# maturity = {
#     'E': 'Estimated (sketch)',
#     'L': 'Layout Drawings (major mod)',
#     'P': 'Pre-Released Drawings (minor mods)',
#     'C': 'Released Drawings (calc)',
#     'X': 'Existing Hardware',
#     'A': 'Actual Mass',
#     'CFE': 'Customer Furnished Equipment'
# }

maturity = {
    'E':   0,
    'L':   1,
    'P':   2,
    'C':   3,
    'X':   4,
    'A':   5,
    'CFE': 6
}

category = {
    'S':  'Structures and Mechanisms',
    'P':  'Propulsion',
    'T':  'Thermal',
    'B':  'Batteries',
    'W':  'Wiring and Instrumentation',
    'E1': 'Electrical Boxes and Components (  <10 lbs)',
    'E2': 'Electrical Boxes and Components (10-30 lbs)',
    'E3': 'Electrical Boxes and Components (  >30 lbs)',
    'L':  'ECLSS',
    'H':  'Crew Systems',
    'C':  'Composites'
}

# mass growth allowance
#    cat: [  E,   L,   P,   C,   X,   A, CFE]
MGA = {
    'S':  [.18, .15, .08, .04, .02, 0.0, 0.0],
    'P':  [.18, .15, .08, .04, .02, 0.0, 0.0],
    'T':  [.18, .15, .08, .04, .02, 0.0, 0.0],
    'B':  [.20, .15, .10, .05, .03, 0.0, 0.0],
    'W':  [.50, .30, .25, .05, .03, 0.0, 0.0],
    'E1': [.30, .25, .20, .10, .03, 0.0, 0.0],
    'E2': [.20, .20, .15, .05, .03, 0.0, 0.0],
    'E3': [.15, .15, .10, .05, .03, 0.0, 0.0],
    'L':  [.23, .18, .12, .09, .04, 0.0, 0.0],
    'H':  [.23, .18, .19, .09, .04, 0.0, 0.0],
    'C':  [.24, .19, .13, .06, .03, 0.0, 0.0]
}


def get_MGA(cat, mat):
    """ return the mass growth allowance fraction for the given
        mass category and maturity
    """
    if MGA_enabled:
        return MGA[cat][maturity[mat]]
    else:
        return 0
