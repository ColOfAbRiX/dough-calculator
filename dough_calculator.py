#!/usr/bin/env python3

from argparse import ArgumentParser
from json import load as json_load
from types import SimpleNamespace
import sys

# pip3 install jinja
from jinja2 import Template, Environment, FileSystemLoader

try:
    # pip3 install pyyaml
    from yaml import safe_load as yaml_load
    __yaml__ = True
except ImportError:
    __yaml__ = False

try:
    # pip3 install argcomplete
    import argcomplete
    __argcomplete__ = True
except ImportError:
    __argcomplete__ = False

try:
    # pip3 install colored
    from colored import fg, attr
    __colored__ = True
except ImportError:
    __colored__ = False
    def fg(dummy):
        return ""
    def bg(dummy):
        return ""
    def attr(dummy):
        return ""

parser = ArgumentParser(description="Fab & Claire's Baker Calculator")
parser.add_argument(
    '--people',
    type=int,
    help="The number of people, used to multiply all other ingredients"
)
parser.add_argument(
    '--portions',
    type=int,
    help="The number of portion to divide the dough in. Default value: 1 portion"
)

parser.add_argument(
    '--flour',
    type=int,
    help="The quantity of flour, in grams, for one person. Default value: 100g"
)
water_group = parser.add_mutually_exclusive_group()
water_group.add_argument(
    '--hydration',
    type=float,
    help=("The hydration in baker's percentage, for one person. This option cannot be used together"
          " with --hydration. Default value: 0.55")
)
water_group.add_argument(
    '--water',
    type=int,
    help=("The amount of water to use in the recipe, for one person. This option cannot be used "
          "together with --hydration. Default value: 55")
)
parser.add_argument(
    '--fats',
    type=float,
    help="The amount of fats, in baker's percentage, for one person. Default value: 0.0"
)
parser.add_argument(
    '--salt',
    type=float,
    help="The amount of salt, in baker's percentage, for one person. Default value: 0.015"
)
parser.add_argument(
    '--sourdough',
    type=float,
    help="The amount of sourdough, in baker's percentage, for one person. Default value: 0.25"
)
parser.add_argument(
    '--sourdough-hydration',
    type=float,
    help="The hydration of the sourdough itself. Default value: 0.50"
)

parser.add_argument(
    '--profile',
    help=("The file, in {0} format containing, a baking profile to use. The settings in the profile "
          "will override the command line arguments").format("YAML" if __yaml__ else "JSON")
)
parser.add_argument(
    '--templates',
    help=("Directory that contains the templates used to build the output.")
)
parser.add_argument(
    '--no-sourdough-correction',
    action='store_true',
    help=("When specified the calculations will not take into account the sourdough contribution to "
          "flour and water")
)
parser.add_argument(
    '--portion-weight',
    type=float,
    help=("Define the weight of a portion for for one person and adjust all other quantities")
)

if __argcomplete__:
    argcomplete.autocomplete(parser)
args = parser.parse_args()

# Default configuration values
default_settings = {
    'args': {},
    'fats': 0.0,
    'flour': 100,
    'hydration': 0.55,
    'no_sourdough_correction': False,
    'notes': "",
    'people': 1,
    'portion_weight': None,
    'portions': 1,
    'profile': None,
    'salt': 0.015,
    'sourdough_hydration': 0.5,
    'sourdough': 0.25,
    'templates': "templates",
    'title': "",
    'water': None,
}

# Holds the final configuration
final_settings = default_settings.copy()

# Load profile from file
if args.profile is not None:
    with open(args.profile, mode='r') as profile_file:
        if __yaml__:
            profile_settings = yaml_load(profile_file)
        else:
            profile_settings = json_load(profile_file)

    # Update final settings using profile settings
    final_settings.update(profile_settings)

# Settings from the command line (cleaned of None values)
cmdline_settings = {
    key: value
    for key, value in vars(args).items() if value is not None
}

# Update final settings using command line settings
final_settings.update(cmdline_settings)

# Convert back final settings in a more comfy object
args = SimpleNamespace(**final_settings)

# Calculates the quantity for each ingredient
flour_total = args.flour * args.people
sourdough = flour_total * args.sourdough
salt = flour_total * args.salt
flour = flour_total
hydration = args.hydration if args.water is None else args.water / flour_total
water = flour * hydration

if hydration < 0.3:
    print("Hydration is too low for any sensible baking. Hydration must always be greater than 30%")
    sys.exit(1)

# Take into account the flour and water contribution from the sourdough
if not args.no_sourdough_correction:
    flour /= (1 + args.sourdough * (1.0 - args.sourdough_hydration))
    water -= sourdough * args.sourdough_hydration

# On effects of fats on hydration:
#   http://www.thefreshloaf.com/node/30743/where-does-oilhoney-and-sugar-fit-hydration-formulas
fats = flour_total * args.fats

# Total weight
total_weight = sourdough + water + flour + salt + fats

# Portioning
portion_weight = total_weight / float(args.portions)

# If a portion weight has been set, adjust the correction factor
k = 1.0
if args.portion_weight is not None:
    k = args.portion_weight / portion_weight

# Estimate the rising time of the dough compared to the sourdough
rising_multiplier = 0.5 / args.sourdough if args.sourdough > 0.0 else 0.0

data = {
    "title": args.title,
    "notes": args.notes,

    "conf_people": args.people,
    "conf_portions": args.portions,

    "single_flour": args.flour * k,
    "single_hydration": hydration * 100,
    "single_sourdough": args.sourdough * 100,
    "single_sourdough_hydration": args.sourdough_hydration * 100,
    "single_salt": args.salt * 100,
    "single_fats": args.fats * 100,

    "total_flour": round(flour * k),
    "total_water": round(water * k),
    "total_sourdough": round(sourdough * k),
    "total_fats": round(fats * k),
    "total_salt": round(salt * k, 1),
    "total_weight": total_weight * k,

    "portion_weight": round(portion_weight * k),
    "rising_multiplier": round(rising_multiplier, 2),

    "extra": vars(args)
}

environment = Environment(loader=FileSystemLoader(args.templates), trim_blocks=True)
template = environment.get_template("main.j2")
output = template.render(**data)
print(output)
