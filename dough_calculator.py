#!/usr/bin/env python3

from argparse import ArgumentParser
import json
import sys

try:
    import yaml
except ImportError:
    print("You need to install pyyaml using \"pip3 install -y pyyaml\"")
    sys.exit(1)

parser = ArgumentParser()
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
    default=150,
    type=int,
    help="The quantity of flour, in grams, for one person. Default value: 150g"
)
parser.add_argument(
    '--hydration',
    default=0.55,
    type=float,
    help="The hydration in baker's percentage, for one person. Default value: 0.55"
)
parser.add_argument(
    '--fats',
    default=0.0,
    type=float,
    help="The amount of fats, in baker's percentage, for one person. Default value: 0.0"
)
parser.add_argument(
    '--salt',
    default=0.02,
    type=float,
    help="The amount of salt, in baker's percentage, for one person: Default value: 0.2"
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
    help="The hydration of the sourdough. Default value: 0.50"
)
parser.add_argument(
    '--profile',
    default=None,
    help="The file, in JSON format containing, a baking profile to use"
)
args = parser.parse_args()

# Load profile from file
if args.profile is not None:
    with open(args.profile, mode='r') as profile_file:
        profile_data = yaml.safe_load(profile_file)

    cmdline_options = args.__dict__
    args.__dict__.update(profile_data)
    args.__dict__.update(cmdline_options)

# Calculates the quantity for each ingredient
flour_total = args.flour * args.people
sourdough = flour_total * args.sourdough
flour = flour_total / (1 + args.sourdough * (1.0 - args.sourdough_hydration))
water = flour_total * args.hydration - sourdough * args.sourdough_hydration
salt = flour_total * args.salt
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
    "single_hydration": args.hydration * 100,
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
