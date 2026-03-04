# ms-mail-automation

## Installation

Run `install.sh`. It installs the files into $HOME/.local/bin/ms-mail-automation,
$HOME/.config/ms-mail-automation, $HOME/.config/systemd/user.
```
$ ./install.sh
```

Modify $HOME/.config/ms-mail-automation to configure.
```
USERNAME=john-doe@example.com
MAIL_FOLDER_ID=...
TENANT=common
CLIENT_ID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
REDIRECT_URI=http://localhost
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
