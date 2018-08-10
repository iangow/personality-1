#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module works with IBM Watson Personality Insights
The module supports caching of the results returned by the service

Created on Sat Jul 26 17:39:00 2018

@author: vadim
"""

# %%

import hashlib
import json
import os
import sys

# %%

class PersonalityInsights:
    '''
    :Description: A class for working with IBM Watson Personality Insights

                  The class supports caching of results in subdirectory cache/
    :Usage:
            pi = PersonalityInsights()

            json = pi.get_profile(text)
    :Note: Credentials to access the service are taken from config.py,
           which should be coppied from config.example.py
    '''

    def __init__(self):
        # storing the path to this module
        self.path = os.path.dirname(os.path.abspath(__file__))
        if self.path not in sys.path:
            sys.path.insert(0, self.path)
        path = os.path.join(self.path, "Insights")
        if path not in sys.path:
            sys.path.insert(0, path)

        # importing custom modules
        import config
        import Insights.watson_developer_cloud.personality_insights_v3 as PI

        # creating the PersonalityInsightsV3 object
        print('Creating the Personality Insights object.')
        self.pi = PI.PersonalityInsightsV3(
            username=config.bluemix_pi_username,
            password=config.bluemix_pi_password,
            version=config.bluemix_pi_version,
            url=config.bluemix_pi_url
        )
        self.pi.set_default_headers({"x-watson-learning-opt-out": "1"})

    def get_profile(self, text):
        '''
        :param text: The text passed to the IBM Watson Personality Insights service
        :return: A dictionary containing the scores returned by the service
        '''
        # first we check the cache
        cache_dirname = os.path.join(self.path, 'cache')
        if not os.path.isdir(cache_dirname):
            print('Creating the directory ' + cache_dirname)
            os.mkdir(cache_dirname, 0o755)
        cache_hex_string = hashlib.sha256(text.encode()).hexdigest()
        cache_filename = os.path.join(cache_dirname, cache_hex_string)
        if os.path.isfile(cache_filename):
            print('Obtaining Personality Insights scores from cache...')
            try:
                with open(cache_filename, 'r') as file:
                    json_data = json.load(file)
                return json_data
            except Exception as e:
                print('! Error: ' + str(e))
                pass
        # otherwise we call the Watson Personality Insights API
        # note that if the service cannot calculate scores for any reason
        # (such as too few words, for example), it raises an exception
        print('Obtaining Personality Insights scores from the service...')
        try:
            json_data = self.pi.profile(text,
                                        content_type = "text/plain;charset=utf-8",
                                        accept = "application/json",
                                        raw_scores = True,
                                        consumption_preferences = False
                                       )
        except Exception as e:
            print('! Error: ' + str(e))
            json_data = { 'error': str(e) }
            pass
        # caching and returning the result
        print('Caching Personality Insights scores...')
        try:
            with open(cache_filename, 'w') as file:
                file.write(json.dumps(json_data, indent=2))
        except Exception as e:
            print('! Error: ' + str(e))
            pass
        return json_data
