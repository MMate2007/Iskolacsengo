#!/bin/sh

apt install python3 python3-bcrypt python3-flask python3-flask-login python3-pygame python3-alsaaudio python3-gpiozero python3-pydub -y
dir=$PWD
python initdbs.py
chown -R $SUDO_USER: assets
chown $SUDO_USER users.db
chown $SUDO_USER programmes.db
chown $SUDO_USER settings.json
cd /etc/systemd/system
cat > iskolacsengo.service << END
[Unit]
Description=Iskolacsengo
Wants=sound.target
After=network.target sound.target

[Service]
WorkingDirectory=$dir
User=$SUDO_USER
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=python $dir/main.py
Restart=on-failure
RestartSec=30
KillSignal=SIGINT
CPUWeight=1000

[Install]
WantedBy=default.target
END
systemctl daemon-reload
systemctl enable iskolacsengo.service
systemctl start iskolacsengo.service
