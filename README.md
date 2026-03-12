# ms-mail-automation

## Installation

Run `install.sh`. It installs the files into $HOME/.local/bin/ms-mail-automation,
$HOME/.config/ms-mail-automation, $HOME/.config/systemd/user.
```
$ ./install.sh
```

Modify $HOME/.config/ms-mail-automation/config.json to configure.
```
{
	"username": "john-doe@example.com",
	"mail_folder_id": "MAIL FOLDER ID TO MONITOR",
	"tenant": "Tenant ID or common or organizations or consumers",
	"client_id": "Client ID (Application ID) to use this tool",
	"redirect_uri": "Redirect URI used in the authentication process (e.g. http://localhost)"
}
```

Authenticate your account and create cache authorization infomation.
```
$ ms-auth.sh
```

Enable and start ms-mail-automation.service.
```
$ systemctl --user enable ms-mail-automation.service
$ systemctl --user start ms-mail-automation.service
```

## Log file

The log is stored at `$HOME/.local/bin/ms-mail-automation/log.txt`.
```
$ less $HOME/.local/bin/ms-mail-automation/log.txt
```
