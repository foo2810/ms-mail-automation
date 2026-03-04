#!/bin/bash

CONFIG_FILE=$HOME/.config/ms-mail-automation/config.sh
if [ ! -f $CONFIG_FILE ]; then
	echo "config.sh not found"
	exit 1
fi

. $CONFIG_FILE

SCRIPT_DIR=$(dirname "$0")
CONFIG_DIR=
PYENV=$SCRIPT_DIR/.venv

source $PYENV/bin/activate || exit 1

python $SCRIPT_DIR/main.py \
	$USERNAME \
	$MAIL_FOLDER_ID \
	$TENANT \
	$CLIENT_ID \
	$REDIRECT_URI \
	&> $SCRIPT_DIR/log.txt
