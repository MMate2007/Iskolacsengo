#!/bin/sh

apt install python3-bcrypt python3-flask python3-flask-login python3-pygame
dir=$PWD
cd /etc/systemd/system
cat > iskolacsengo.service << END
[Unit]
Description=Start the main Python script of Iskolacsengo
After=network.target

[Service]
WorkingDirectory=$dir
ExecStart=python $dir/main.py
Restart=on-abnormal

[Install]
WantedBy=default.target
END

systemctl daemon-reload
systemctl enable iskolacsengo.service
systemctl start iskolacsengo.service