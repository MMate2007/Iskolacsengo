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
ExecStart=python $dir/main.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
END
systemctl daemon-reload
systemctl enable iskolacsengo.service
systemctl start iskolacsengo.service