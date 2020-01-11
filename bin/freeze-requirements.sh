set -e
source env/bin/activate
pip freeze >requirements.txt
deactivate
