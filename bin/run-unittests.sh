set -e
source env/bin/activate
python -m unittest discover
deactivate
