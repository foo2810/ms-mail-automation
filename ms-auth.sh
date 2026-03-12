#!/bin/bash

CONFIG_FILE=$HOME/.config/ms-mail-automation/config.json
if [ ! -f $CONFIG_FILE ]; then
	echo "config.json not found"
	exit 1
fi

MAIN_SCRIPT_DIR=$HOME/.local/bin/ms-mail-automation

cd $MAIN_SCRIPT_DIR

source .venv/bin/activate || exit 1

python $MAIN_SCRIPT_DIR/ms-auth.py $CONFIG_FILE