# Description

# watson.py

`watson.py` queries a PostgreSQL database for a list of subjects
with texts, submits these texts to the IBM Watson Personality Insights
service to obtain the subjects' psychological profiles, and uploads
the results to the specified table in the database rewriting it if
it exists.

The table with texts obtained using the SQL statement (*sql_input*)
must have column `text`. The texts from this column are submitted
to the IBM Watson Personality Insights service. All the other columns
are copied to the output table, which is uploaded back to the database.
Accordingly, they define the non-score columns of the output table, and
should contain enough information to identify later the subjects in
the output table.

Besides these columns copied from the input data, the output table
also contains columns with the scores returned by the service.
Basically, the output table is different from the input table only
in that the column `text` is substituted by a number of columns
containing personality characteristics.

## personalityinsights.py

This file contains the main class to submit texts to the IBM Watson
Personality Insights service.

An example of usage:
``` Python
from personalityinsights import PersonalityInsights as PI
pi = PI()
profile = pi.get_profile(text)
```

The class supports caching of results returned by the service.
The results are cached in the subdirectory `cache/`.
This is done for two reasons:
- First, each Watson API call takes about 1 second to complete, so
  a large number of calls can take a long time to finish. Caching
  allows to skip those calls that were made previously.
- Second, the service charges per each API call.

## personalityinsights.example.py

This is an example of usage of `personalityinsights.py`.
The program takes as an input a directory (`examples` by default)
and loads all `*.txt` files from it. It then submits the texts
to the IBM Watson Personality Insights service using the module
`personalityinsights.py`, and saves the results in `*.json` files
next to the text files in the same directory.

# Authentication with the database and the IBM Watson Bluemix Cloud

Two files containing personal identification information for
the services being used by the program should be present:

- `config.py` contains information identifying the user's account
  previously set up on the IBM Watson website.

  Further details can be found in the file `config.example.py`,
  which should be used as a template.

- `.pgpass` should be present in the home directory of the user
  running the program on a *nix OS (including MacOS). Please
  consult appropriate documentation regarding the correct placement
  of this file on a Windows machine.

  Alternatively, the environment variables `PGUSER` and `PGPASSWORD`
  should be set.
