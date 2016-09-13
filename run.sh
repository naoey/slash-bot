# Temporary file to run bot till deploy mechanism is finalised

if [[ $1 == "--reset-db" ]]
then
    rm slash_bot.db
fi

cd slash_bot && python3 ./core.py

cd ..
