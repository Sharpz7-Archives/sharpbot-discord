:: Application to boot up RethinkDB and Sharpbot asynchronously - created for non-Docker users and ease of use
:: Disable then clear message outputs for cleaner CLI

:: Check if environment variables are set - these are pre-defined and non-builtin
IF (%Sharpbot_Dir%=="") (
    ECHO "SharpBot_Dir" is not defined

    EXIT
)
IF (%Rethink_Dir%=="") (
    ECHO "Rethink_Dir" is not defined

    EXIT
)

:: Updates to the latest version of, then runs Sharpbot
cd "%Sharpbot_Dir%"

:: Database setup
start "" "%Rethink_Dir%\rethinkdb.exe"

git pull
CLS
cd project
pipenv run "py -3.7" run.py
