#!/bin/bash
set -euo pipefail
useradd -m -s /bin/bash william
usermod -aG sudo william
echo 'william ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/william
chmod 440 /etc/sudoers.d/william
printf '[user]\ndefault=william\n' > /etc/wsl.conf
echo "user setup done"
