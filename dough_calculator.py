#!/usr/bin/env python3

from argparse import ArgumentParser
from json import load as json_load
import sys

try:
    # pip3 install pyyaml
    from yaml import safe_load as yaml_load
    __yaml__ = True
except ImportError:
    __yaml__ = False

try:
    # pip3 install argcomplete
    # eval "$(register-python-argcomplete ./dough_calculator.py)"
    import argcomplete
    __argcomplete__ = True
except ImportError:
    __argcomplete__ = False


parser = ArgumentParser(description="Fab & Claire's Baker Calculator")
parser.add_argument(
    '--people',
    default=1,
    type=int,
    help="The number of people, used to multiply all other ingredients"
)
parser.add_argument(
    '--portions',
    default=1,
    type=int,
    help="The number of portion to divide the dough in. Default value: 1 portion"
)

parser.add_argument(
    '--flour',
    default=100,
    type=int,
    help="The quantity of flour, in grams, for one person. Default value: 100g"
)
water_group = parser.add_mutually_exclusive_group()
water_group.add_argument(
    '--hydration',
    default=0.55,
    type=float,
    help=("The hydration in baker's percentage, for one person. This option cannot be used together"
          " with --hydration. Default value: 0.55")
)
water_group.add_argument(
    '--water',
    default=None,
    type=int,
    help=("The amount of water to use in the recipe, for one person. This option cannot be used "
          "together with --hydration. Default value: 55")
)
parser.add_argument(
    '--fats',
    default=0.0,
    type=float,
    help="The amount of fats, in baker's percentage, for one person. Default value: 0.0"
)
parser.add_argument(
    '--salt',
    default=0.015,
    type=float,
    help="The amount of salt, in baker's percentage, for one person. Default value: 0.015"
)
parser.add_argument(
    '--sourdough',
    default=0.25,
    type=float,
    help="The amount of sourdough, in baker's percentage, for one person. Default value: 0.25"
)
parser.add_argument(
    '--sourdough-hydration',
    default=0.5,
    type=float,
    help="The hydration of the sourdough itself. Default value: 0.50"
)

parser.add_argument(
    '--profile',
    default=None,
    help=("The file, in {0} format containing, a baking profile to use. The settings in the profile "
          "will override the command line arguments").format("YAML" if __yaml__ else "JSON")
)
parser.add_argument(
    '--no-sourdough-correction',
    action='store_true',
    help=("When specified the calculations will not take into account the sourdough contribution to "
          "flour and water")
)


if __argcomplete__:
    argcomplete.autocomplete(parser)
args = parser.parse_args()

# Load profile from file
if args.profile is not None:
    with open(args.profile, mode='r') as profile_file:
        if __yaml__:
            profile_data = yaml_load(profile_file)
        else:
            profile_data = json_load(profile_file)

    cmdline_options = args.__dict__
    args.__dict__.update(profile_data)
    args.__dict__.update(cmdline_options)

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

# Estimate the rising time of the dough compared to the sourdough
rising_multiplier = 0.5 / args.sourdough if args.sourdough > 0.0 else 0.0

data = {
    "conf_people": args.people,
    "conf_portions": args.portions,

    "single_flour": args.flour,
    "single_hydration": hydration * 100,
    "single_sourdough": args.sourdough * 100,
    "single_sourdough_hydration": args.sourdough_hydration * 100,
    "single_salt": args.salt * 100,
    "single_fats": args.fats * 100,

    "total_flour": round(flour),
    "total_water": round(water),
    "total_sourdough": round(sourdough),
    "total_fats": round(fats),
    "total_salt": round(salt, 1),
    "total_weight": total_weight,

    "portion_weight": round(portion_weight),
    "rising_multiplier": round(rising_multiplier, 2),
}

# Display result
print("""
  ~  Fab & Claire's Baker Calculator  ~

Number of people..............: {conf_people}
Number of portions............: {conf_portions}

Selected quantities for one person:

  Flour.......................: {single_flour:.0f}g
  Hydration...................: {single_hydration:.0f}%
  Sourdough...................: {single_sourdough:.0f}%
  SD hydration................: {single_hydration:.0f}%
  Salt........................: {single_salt:.1f}%
  Fats........................: {single_fats:.0f}%

Total amounts for {conf_people} person(s):

  Flour.......................: {total_flour:.0f}g
  Water.......................: {total_water:.0f}g
  Sourdough...................: {total_sourdough:.0f}g
  Fats........................: {total_fats:.0f}g
  Salt........................: {total_salt:.1f}g

Other information:

  Total weight................: {total_weight:.0f}g
  Portion weight..............: {portion_weight:.0f}g
  Rising multiplier...........: {rising_multiplier:.1f}x""".format(**data))

print("\nENJOY YOUR DOUGH!")
