#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sat Jun 13 14:42:07 2018

@author: vadim
"""

#%%

from collections import OrderedDict
from datetime import datetime as dt
import numpy as np
import pandas as pd
import sqlalchemy as sa

from personalityinsights import PersonalityInsights as PI

#%%

try:

#%%

    # parameters
    db_schema = 'personality'
    db_table = 'watson_output'
    db_schema_table = db_schema + '.' + db_table
    db_table_comment = 'IBM Watson Personality scores for speaker-call combinations. ' + \
              'Created using GitHub:vcherep/personality/Watson/watson.py on ' + \
              dt.today().strftime('%m/%d/%Y') + '.'
    db_table_owner = 'personality'
    db_table_access = 'personality_access'
    sql_input = \
        "SELECT company_id, executive_id, file_name, count(*) AS records, string_agg(speaker_qa, ' ') AS text " + \
        "FROM personality.watson_input " + \
        "GROUP BY company_id, executive_id, file_name"

#%%

    # obtaining texts
    print('Querying the database for texts...')
    print('Creating the database connection...')
    db_engine = sa.create_engine("postgresql://aaz.chicagobooth.edu:5432/postgres")
    print('Obtaining texts from the database...')
    texts = pd.read_sql(sql_input, db_engine)
    if not len(texts):
        Exception('Error: no records were returned by the SQL query.')
    if not 'text' in texts:
        Exception('Error: The resulting table has no column "text".')
    print('{0} records are returned.'.format(len(texts)))
    db_engine.dispose() # obtaining texts can be long enough for the connection to timeout
    db_engine = None

#%%

    # creating PersonalityInsights object
    pi = PI()

#%%

    # obtaining scores

    def get_scores(d):
        '''
        Extracts scores from a dictionary
        :param d: The dictionary or subdictionary returned by the IBM Watson Personality Insights service
        :return: A dictionary containing the extracted scores in a format suitable for writing to a database
        '''
        for key in [ 'trait_id', 'percentile', 'raw_score', 'significant' ]:
            if not key in d:
                Exception('Error: The provided dictionary has no key "' + key + '".')
        score_title = d['trait_id']
        return {
            score_title + '_pc': d['percentile'],
            score_title + '_raw': d['raw_score'],
            score_title + '_sig': d['significant']
        }

#%%

    print('Obtaining scores...')
    profiles = pd.DataFrame()
    for i in range(len(texts)):
        print('Obtaining scores for record #' + str(i + 1) + ' out of ' + str(len(texts)) + '...')
        profile = pi.get_profile(texts.iloc[i]['text'])
        scores = { 'word_count': 0 }
        if not 'error' in profile:
            if 'word_count' in profile:
                scores['word_count'] = profile['word_count']
            for category_name in [ 'personality', 'needs', 'values' ]:
                if not category_name in profile:
                    continue
                for category in profile[category_name]:
                    scores = { **scores, **get_scores(category) }
                    if 'children' in category:
                        for child in category['children']:
                            scores = { **scores, **get_scores(child) }
        # the following code is due to Python giving a warning in some cases
        # (claiming also that this warning will actually be an error in a future Python version)
        # I filed a bug against pandas regarding this and another related issue
        profiles = profiles.append([ OrderedDict( \
            { **scores, **{ key: np.NaN for key in profiles if not key in scores } } \
            ) ], ignore_index = True)
    profiles = pd.concat([
        texts[ [ column for column in texts if column != 'text' ] ],
        profiles
    ], axis = 1)

#%%

    # uploading the results
    print('Uploading the results to the database...')
    print('Creating the database connection...')
    db_engine = sa.create_engine("postgresql://aaz.chicagobooth.edu:5432/postgres")
    print('Uploading data...')
    profiles.to_sql(db_table, db_engine, db_schema, if_exists = 'replace')
    with db_engine.connect() as db_connection:
        sql = "COMMENT ON TABLE " + db_schema_table + " IS '" + db_table_comment + "';"
        db_connection.execute(sql)
        sql = 'ALTER TABLE ' + db_schema_table + ' OWNER TO ' + db_table_owner
        db_connection.execute(sql)
        sql = 'GRANT SELECT ON ' + db_schema_table + ' TO ' + db_table_access
        db_connection.execute(sql)
        db_connection_il = db_connection.connection.isolation_level
        db_connection.connection.set_isolation_level(0)
        sql = 'VACUUM ANALYZE ' + db_schema_table
        db_connection.execute(sql)
        db_connection.connection.set_isolation_level(db_connection_il)

# %%

except Exception as e:
    print("\n! An error has occured:")
    print('! ' + str(e))
    print("! Program terminated.")
finally:
    if db_engine:
        db_engine.dispose()
