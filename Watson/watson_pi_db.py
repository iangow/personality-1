#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sat Jun 13 14:42:07 2018

@author: vadim
"""

# %%

import config
import csv
import glob
import json
import os
import pandas
import re
import sqlalchemy
import sys

# %%

# This is to keep Insights files intact without creating additional files either
path_cwd = os.getcwd()
path = os.path.join(path_cwd, "Insights")
if path not in sys.path:
    sys.path.insert(0, path)

import Insights.watson_developer_cloud.personality_insights_v3 as PersonalityInsights

# %%

try:
    print("")

# %%

    # Create the PersonalityInsights object
    print('Creating the Personality Insights object.')
    bluemix_pi = PersonalityInsights.PersonalityInsightsV3(
            username = config.bluemix_pi_username,
            password = config.bluemix_pi_password,
            version = config.bluemix_pi_version,
            url = config.bluemix_pi_url
    )
    bluemix_pi.set_default_headers({ "x-watson-learning-opt-out": "1" })

# %%

    # Connect to the database, execute SQL statements to obtain text data, and run Watson on it

    tables = [ ]
    dirname_tables = os.path.join(path_cwd, 'tables')

    # Please note that the host address and credentials are taken from
    # the file .pgpass that must be present in the current directory
    print('Reading .pgpass for the PostgreSQL password and username.')
    filename = os.path.join(path_cwd, ".pgpass")
    with open(filename, 'r') as file:
        db_line = file.read().splitlines()[0]
    db_line = db_line.split(':')
    try:
        print('Creating the databaase engine...')
        db_engine = sqlalchemy.create_engine("postgresql://" + db_line[3] + ':' + db_line[4] + \
                                  '@' + db_line[0] + ':' + db_line[1] + '/postgres')
        db_line = ''

        # the file table_sql.ini contains a list of tables to create
        # with the corresponding parameters and SQL statements
        # the format is explained in table_sql.example.ini
        # in particular, if a line starts with '#' or ';' it is ignored
        # the table resulting from the execution of the SQL statement should have a column named 'text'
        # all the other returned columns are put into the resulting output table that is uploaded to the database
        print('Reading table_sql.ini for SQL statements...')
        filename = os.path.join(path_cwd, "table_sql.ini")
        with open(filename, 'r') as file:
            table_sql = [ line for line in [ s.strip() for s in file.read().splitlines() ] \
                          if len(line) > 0 and line[0] not in '#;' ]
        tables = [ ]
        tables_i = 0
        while tables_i + 4 < len(table_sql):
            tables.append({ 'name': table_sql[tables_i + 0], \
                            'comment': table_sql[tables_i + 1], \
                            'owner': table_sql[tables_i + 2], \
                            'access': table_sql[tables_i + 3], \
                            'sql': table_sql[tables_i + 4], \
                            })
            tables_i += 5
        for table in tables:
            print('Table: ' + table['name'])
            print('Comment: ' + table['comment'])
            print('Owner: ' + table['owner'])
            print('Access: ' + table['access'])
            print('SQL: ' + table['sql'])
            dirname_json = os.path.join(dirname_tables, table['name'])
            if not os.path.isdir(dirname_json):
                print('Creating the directory ' + dirname_json)
                os.mkdir(dirname_json, 0o755)
            else:
                try:
                    with open(os.path.join(dirname_json, 'sql.txt'), 'r') as file:
                        print('Checking if the SQL statement is the same in ' \
                              + os.path.join(dirname_json, 'sql.txt') + '.')
                        sql_old = file.read().splitlines()[0]
                except:
                    sql_old = ''
                if sql_old != table['sql']:
                    files = glob.glob(os.path.join(dirname_json, '*.json'))
                    if files:
                        print('Removing *.json files in ' + dirname_json + '.')
                        for file in files:
                            os.remove(os.path.join(dirname_json, file))
                    files = glob.glob(os.path.join(dirname_json, '*.csv'))
                    if files:
                        print('Removing *.csv files in ' + dirname_json + '.')
                        for file in files:
                            os.remove(os.path.join(dirname_json, file))
            filename = os.path.join(dirname_json, 'sql.txt')
            print('Writing the SQL statement into ' + filename + '...')
            with open(filename, 'w') as file:
                file.write(table['sql'])
            print('Executing the SQL statement...')
            texts = pandas.read_sql(table['sql'], db_engine)
            print('{0} records are returned.'.format(len(texts)))
            if not 'text' in texts:
                print('The SQL statement is ignored as the resulting table has no column "text".')
            else:
                titles = [ title for title in texts if title != 'text' ]
                for i in range(len(texts)):
                    text = texts.iloc[i]['text']
                    # Obtaining the profile
                    filename = os.path.join(dirname_json, str(i + 1) + '.json')
                    if os.path.isfile(filename) and os.path.getsize(filename) > 0:
                        print('The file ' + filename + ' already exists.')
                    else:
                        print("Obtaining the profile #{0}...".format(i + 1))
                        try:
                            profile = bluemix_pi.profile(text,
                                                         content_type = "text/plain;charset=utf-8",
                                                         accept = "application/json",
                                                         raw_scores = True,
                                                         consumption_preferences = False
                                                         )
                        except Exception as e:
                            profile = ''
                            print('Error: ' + str(e))
                            with open(os.path.join(dirname_json, str(i + 1) + '.log'), 'w') as file:
                                file.write(str(e))
                        print("Writing the output to " + filename + "...")
                        with open(filename, 'w') as file:
                            if profile:
                                file.write(json.dumps(profile, indent = 2))
                            else:
                                file.write('{}')
                        filename = os.path.join(dirname_json, str(i + 1) + '.csv')
                        print('Writing the fields to ' + filename + '...')
                        with open(filename, 'w') as file:
                            file.write('\t'.join(titles) + '\n')
                            file.write('\t'.join([ str(texts.iloc[i][title]) for title in titles ]))

        # Load all obtained json and csv files, build a table, and upload it to the database
        for table in tables:
            print('Table: ' + table['name'])
            dirname_json = os.path.join(dirname_tables, table['name'])
            files = glob.glob(os.path.join(dirname_json, '*.json'))
            print('Found {0} records.'.format(len(files)))
            if files:
                print('Reading the files and creating the output table.')
                csv_data = [ ]
                for filename in files:
                    filename_csv = filename.replace('.json', '.csv')
                    with open(os.path.join(dirname_json, filename_csv), 'r') as file:
                        lines = file.read().splitlines()
                    titles = lines[0].split('\t')
                    values = lines[1].split('\t')
                    json_data = ''
                    if os.path.getsize(filename) > 1000:
                        with open(os.path.join(dirname_json, filename), 'r') as file:
                            json_data = json.load(file)
                        titles.append('word_count')
                        values.append(json_data['word_count'])
                        for category_name in ['personality', 'needs', 'values']:
                            for category in json_data[category_name]:
                                titles.append(category['trait_id'] + '_pc')
                                values.append(category['percentile'])
                                titles.append(category['trait_id'] + '_raw')
                                values.append(category['raw_score'])
                                titles.append(category['trait_id'] + '_sig')
                                values.append(category['significant'])
                                if 'children' in category:
                                    for child in category['children']:
                                        titles.append(child['trait_id'] + '_pc')
                                        values.append(child['percentile'])
                                        titles.append(child['trait_id'] + '_raw')
                                        values.append(child['raw_score'])
                                        titles.append(child['trait_id'] + '_sig')
                                        values.append(child['significant'])
                    if not csv_data:
                        if not json_data:
                            raise Exception('The first file is needed for headers, but no JSON was returned.')
                        else:
                            csv_data = [ titles, values ]
                    else:
                        if not json_data:
                            while len(values) < len(csv_data[0]):
                                titles.append(csv_data[0][len(values)])
                                values.append('')
                        if titles != csv_data[0]:
                            raise Exception('The files ' + filename_csv + ' and ' + filename \
                                            + ' have different titles than the previous files.')
                        csv_data.append(values)
                print('Writing to the database...')
                filename_csv = os.path.join(dirname_json, 'data.csv')
                with open(filename_csv, 'w', newline = '') as file:
                    writer = csv.writer(file, delimiter='\t', quoting = csv.QUOTE_MINIMAL, quotechar='"')
                    writer.writerows(csv_data)
                df = pandas.read_csv(filename_csv, sep='\t')
                table_schema_name = table['name'].split('.', 2)
                if len(table_schema_name) == 1:
                    df.to_sql(table_schema_name[0], db_engine, \
                              if_exists = 'replace', index = False)
                else:
                    df.to_sql(table_schema_name[1], db_engine, schema = table_schema_name[0], \
                              if_exists = 'replace', index = False)
                # Permissions and a comment
                with db_engine.connect() as db_connection:
                    sql = "COMMENT ON TABLE " + table['name'] + " IS '" + table['comment'] + "';"
                    db_connection.execute(sql)
                    sql = 'ALTER TABLE ' + table['name'] + ' OWNER TO ' + table['owner']
                    db_connection.execute(sql)
                    sql = 'GRANT SELECT ON ' + table['name'] + ' TO ' + table['access']
                    db_connection.execute(sql)
                    db_connection_il = db_connection.connection.isolation_level
                    db_connection.connection.set_isolation_level(0)
                    sql = 'VACUUM FULL ANALYZE ' + table['name']
                    db_connection.execute(sql)
                    db_connection.connection.set_isolation_level(db_connection_il)
    finally:
        if db_engine:
            db_engine.dispose()

# %%

    print("\nDone.")

except Exception as e:
    print("\nAn error has occured:")
    print(e)
    print("\nProgram terminated.")

# %%
