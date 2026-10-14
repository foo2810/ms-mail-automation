# ms-mail-automation

## Build and Installation

Build the package:
```
$ uv build
```

Install the package as uv tool:
```
# For example:
$ uv tool install dist/ms_mail_automation-0.1.0-py3-none-any.whl
```

Modify $HOME/.config/ms-mail-automation/config.json to configure:
```
{
	"username": "john-doe@example.com",
	"mail_folder_id": "MAIL FOLDER ID TO MONITOR",
	"tenant": "Tenant ID or common or organizations or consumers",
	"client_id": "Client ID (Application ID) to use this tool",
	"redirect_uri": "Redirect URI used in the authentication process (e.g. http://localhost)"
}
```

Authenticate your account and create cache authorization infomation:
```
$ ms-auth
```

Write systemd service:
```
[Unit]
Description=ms-mail-watch

[Service]
Type=simple
ExecStart=/home/<user name>/.local/bin/ms-mail-watch
Restart=no

[Install]
WantedBy=default.target
```

Enable and start ms-mail-automation.service:
```
$ systemctl --user enable ms-mail-automation.service
$ systemctl --user start ms-mail-automation.service
```
