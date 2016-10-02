# Temporary file to run bot till deploy mechanism is finalised

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --reset-db)
        rm slash_bot.db
        shift
        ;;
        --clear-logs)
        rm -r logs
        shift
        ;;
    esac
done

if [[ ! -d "logs" ]]
then
    mkdir logs
fi

cd slash_bot && python3 ./core.py

cd ..
