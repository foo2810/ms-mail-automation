#!/bin/bash

USER_BIN_DIR=$HOME/.local/bin
USER_CONFIG_DIR=$HOME/.config

INSTALL_BIN_DIR=$USER_BIN_DIR/ms-mail-automation
INSTALL_USER_SYSTEMD_DIR=$USER_CONFIG_DIR/systemd/user
INSTALL_CONFIG_DIR=$USER_CONFIG_DIR/ms-mail-automation

# Create directories to install
mkdir -p $INSTALL_BIN_DIR
mkdir -p $INSTALL_USER_SYSTEMD_DIR
mkdir -p $INSTALL_CONFIG_DIR


# Generate ms-mail-automation.service
cat << EOF > systemd/ms-mail-automation.service
[Unit]
Description=ms-mail-automation

[Service]
Type=simple
ExecStart=$INSTALL_BIN_DIR/ms-mail-automation
Restart=no

[Install]
WantedBy=default.target
EOF


# Install scripts
install -m 644 pyproject.toml $INSTALL_BIN_DIR/pyproject.toml
install -m 644 uv.lock $INSTALL_BIN_DIR/uv.lock
install -m 644 .python-version $INSTALL_BIN_DIR/.python-version
install -m 644 main.py $INSTALL_BIN_DIR/main.py
install -m 644 ms-auth.py $INSTALL_BIN_DIR/ms-auth.py
mkdir -p $INSTALL_BIN_DIR/lib
install -m 644 -D -t $INSTALL_BIN_DIR/lib/ lib/*.py
install -m 744 systemd/ms-mail-automation $INSTALL_BIN_DIR/ms-mail-automation

install -m 744 ms-auth.sh $USER_BIN_DIR/ms-auth.sh

cp -r hook-scripts $INSTALL_BIN_DIR/

# Create virtual environment and install dependencies
[ -d $INSTALL_BIN_DIR/.venv ] && rm -rf $INSTALL_BIN_DIR/.venv
pushd .
cd $INSTALL_BIN_DIR
uv sync
popd


# Install config.sh
install -m 644 config.json $INSTALL_CONFIG_DIR/config.json


# Install systemd service file
install -m 644 systemd/ms-mail-automation.service $INSTALL_USER_SYSTEMD_DIR/ms-mail-automation.service
systemctl --user daemon-reload