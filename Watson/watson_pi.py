#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sat Jan 13 14:42:07 2018

@author: vadim
"""

# %%

import config
import glob
import json
import os
import re
import sys

# %%

# This is to keep Insights files intact without creating additional files either
path = os.path.join(os.getcwd(), "Insights")
if path not in sys.path:
    sys.path.insert(0, path)

import Insights.watson_developer_cloud.personality_insights_v3 as PersonalityInsights

# %%

try:
    print("")

# %%

    # The first argument should be the directory to look for files
    if len(sys.argv) == 1:
        print("Usage: watson_pi.py directory")
        sys.exit(1)
    directory = os.path.join(os.getcwd(), sys.argv[1])
    print("Looking for *.txt files in " + directory + "...")
    directory = os.path.join(directory, '*.txt')

# %%

    # Create the PersonalityInsights object
    bluemix_pi = PersonalityInsights.PersonalityInsightsV3(
            username = config.bluemix_pi_username,
            password = config.bluemix_pi_password,
            version = config.bluemix_pi_version,
            url = config.bluemix_pi_url
    )
    bluemix_pi.set_default_headers({ "x-watson-learning-opt-out": "1" })

# %%

    # Looping over files
    for filename in glob.glob(directory):

# %%

        # Reading the content of the file
        print("\nFile " + os.path.basename(filename) + ".")
        file = open(filename, 'r')
        content = file.read()
        file.close()

# %%

        # Obtaining the profile
        print("Obtaining the profile...")
        profile = bluemix_pi.profile(content,
                                     content_type = "text/plain;charset=utf-8",
                                     accept = "application/json",
                                     raw_scores = True,
                                     consumption_preferences = False
                                     )

# %%

        # Writing the output
        filename = re.sub(r"\.txt$", ".json", filename)
        print("Writing the output to " + os.path.basename(filename) + "...")
        file = open(filename, 'w')
        file.write(json.dumps(profile, indent = 2))
        file.close()

# %%

    print("\nDone.")

except Exception as e:
    print("\nAn error has occured:")
    print(e)
    print("\nProgram terminated.")

# %%
