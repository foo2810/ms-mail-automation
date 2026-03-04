#!/bin/bash

CONFIG_FILE=$HOME/.config/ms-mail-automation/config.sh
if [ ! -f $CONFIG_FILE ]; then
	echo "config.sh not found"
	exit 1
fi

. $CONFIG_FILE

MAIN_SCRIPT_DIR=$HOME/.local/bin/ms-mail-automation

cd $MAIN_SCRIPT_DIR

source .venv/bin/activate || exit 1

python $MAIN_SCRIPT_DIR/ms-auth.py \
	$USERNAME \
	$TENANT \
	$CLIENT_ID \
	$REDIRECT_URI