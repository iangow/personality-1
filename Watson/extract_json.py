#!/usr/bin/env python3
import os, json
import pandas as pd

from sqlalchemy import create_engine
from datetime import datetime as dt

def get_text(cache_filename):
    try: 
        with open(cache_filename, 'r') as file:
            json_data = json.load(file)
            return json.dumps(json_data)
    except Exception as e:
        print('! Error: ' + str(e))
        pass
    
path = 'cache'
df = pd.DataFrame([ {'hash': file, 
                     'profile': get_text(os.path.join(path, file))} 
                   for file in os.listdir(path)])

# parameters
db_schema = 'personality'
db_table = 'watson_output_raw'
db_schema_table = db_schema + '.' + db_table
db_table_comment = 'IBM Watson profiles. ' + \
          'Created using GitHub:iangow/watson/watson.py on ' + \
          dt.today().strftime('%m/%d/%Y') + '.'
db_table_owner = db_schema
db_table_access = db_schema + '_access'

db_engine = create_engine("postgresql://aaz.chicagobooth.edu:5432/postgres")
print('Uploading data...')
df.to_sql(db_table, db_engine, db_schema, if_exists = 'replace', index=False)
with db_engine.connect() as db_connection:
    sql = "COMMENT ON TABLE " + db_schema_table + " IS '" + db_table_comment + "';"
    db_connection.execute(sql)
    sql = 'ALTER TABLE ' + db_schema_table + ' OWNER TO ' + db_table_owner
    db_connection.execute(sql)
    sql = 'ALTER TABLE ' + db_schema_table + ' ALTER COLUMN profile TYPE jsonb USING profile::jsonb'
    db_connection.execute(sql)
    sql = 'GRANT SELECT ON ' + db_schema_table + ' TO ' + db_table_access
    db_connection.execute(sql)
    db_connection_il = db_connection.connection.isolation_level
    db_connection.connection.set_isolation_level(0)
    sql = 'VACUUM ANALYZE ' + db_schema_table
    db_connection.execute(sql)
    db_connection.connection.set_isolation_level(db_connection_il)

db_engine.dispose()
