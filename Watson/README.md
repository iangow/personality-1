# Description

`watson_pi.py` reads text files from a directory, submits the texts to
IBM Watson Personality Insights to obtain the psychological profiles
corresponding to the texts, and saves them to the files next to the
text files in the same directory.

`watson_pi_db.py` queries a PostgreSQL database for a list of subjects
with texts, and submits these texts to IBM Watson Personality Insights
to obtain the subjects' psychological profiles. It then uploads the
obtained profiles to the database to the specified table.

# Usage

The required Python 3 modules are listed in the import section.

Two files containing personal identification information for services
should be in the same directory as the program:

- `config.py` contains information identifying the user's account
  set up on IBM Watson website.

  Further details can be found in the
  file `config.example.py` which should be used as a template.

- `.pgpass` should be present in the same directory as the program
  (or a link should be used). This is a standard file containing
  PostgreSQL database connection parameters and credentials.

  This file is used only for `watson_pi_db.py`.

One additional file is used by `watson_pi_db.py`:

- `table_sql.ini` contains a number of groups of lines, where each
  group of lines specifies some parameters used in working with
  the database.

  Further details can be found in `table_sql.example.ini`, which
  can be used as an example.

### watson_pi.py

Usage:

```
watson_pi.py directory
```

The directory should contain a number of `.txt` files. The obtained
psychological profiles are stored in the corresponding `.json` files.

### watson_pi_db.py

Usage:

```
watson_pi_db.py
```

The program reads a series of parameters from `table_sql.ini` each
specifying one table to generate in the database. The parameters
used for one table are described in `table_sql.example.ini`.

The connection to the database is established using the parameters
from `.pgpass`.

The SQL statement is used to obtain a table where one column has name
`Text`. This column is used to submit texts to IBM Watson Personality
Insights. All other columns are copied to the output table that is
submitted back to the database. The output table consists of these
other columns, and columns containing all personality characteristics
returned by the service. Basically, the output table is different from
the input table returned by the SQL statement only in that the column
`Text` is substituted by a number of columns containing personality
characteristics instead. The name of the table, as well as a number of
its parameters, such as a comment, ownership and access rights, are
also specified for each table.

# Side effects

`watson_pi_db.py` uses the subfolder `table` of the directory of the
program to store the results returned by the service. It creates a
subfolder for each table, stores the SQL statement used to obtain the
input table, and all `.json` files returned by the service as well as
the final output table in the `.csv` format. This is done to prevent
calling IBM Watson Personality Insights API again for those texts for
which it was already called and results were returned. Not only does
it saves API calls of the paid per use service, but it also speeds up
the process enormously when it is rerun after an interruption or an
error. This does not use much of the disk space, as the results of
1,000 calls take approximately 14MB.

