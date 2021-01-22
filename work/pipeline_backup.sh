#!/bin/bash

set -ex

python3 create_tables.py 
python3 load_data_backup.py 
python3 backup.py 
python3 etl.py 
python3 visualization.py




