#!/bin/bash

sudo apt install virtualenv

# Setup python venv if not exists
if [ ! -d "venv" ]; then
  virtualenv -p python3 venv
fi

./venv/bin/python -m pip install -r services/server/requirements.txt

# Setup npm packages
cd services/client || exit
npm install