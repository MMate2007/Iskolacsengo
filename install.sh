#!/bin/sh

apt install python3 python3-bcrypt python3-flask python3-flask-login python3-pygame -y
dir=$PWD
python initdbs.py
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

[Install]
WantedBy=default.target
END
# cd /etc
# cat >> asound.conf << END
# defaults.pcm.card 2
# defaults.ctl.card 2
# END
systemctl daemon-reload
systemctl enable iskolacsengo.service
systemctl start iskolacsengo.service