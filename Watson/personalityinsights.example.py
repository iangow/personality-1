#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sat Jan 13 14:42:07 2018

@author: vadim
"""

# %%

import glob
import json
import os
import re
import sys

from personalityinsights import PersonalityInsights as PI

# %%

try:

# %%

    # The first argument should be the directory to look for files
    if len(sys.argv) == 1:
        directory = 'examples'
    else:
        directory = sys.argv[1]
    directory = os.path.join(os.getcwd(), directory)
    if not os.path.isdir(directory):
        print("Error: Directory " + directory + " does not exist\n" + \
              "Usage: personalityinsights.example.py directory")
        sys.exit(1)
    print("Looking for *.txt files in " + directory + "...")
    directory = os.path.join(directory, '*.txt')

# %%

    # Create the PersonalityInsights object
    pi = PI()

# %%

    # Looping over files
    for filename in glob.glob(directory):
        # Obtaining the profile
        print("Reading " + os.path.basename(filename) + "...")
        with open(filename, 'r') as file:
            profile = pi.get_profile(file.read())
        # Writing the output
        filename = re.sub(r"\.txt$", ".json", filename)
        print("Writing to " + os.path.basename(filename) + "...")
        with open(filename, 'w') as file:
            file.write(json.dumps(profile, indent = 2))

# %%

except Exception as e:
    print("\n! An error has occured:")
    print('! ' + str(e))
    print("! Program terminated.")
