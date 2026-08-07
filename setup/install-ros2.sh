#!/bin/bash
# ROS2 Humble + Gazebo + Nav2 + TurtleBot3 + SLAM Toolbox — Ubuntu 22.04 (WSL2)
# Run as root:  wsl -d Ubuntu-22.04 -u root -- bash /mnt/c/Users/willi/ros2-setup/install-ros2.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

LOG=/var/log/ros2-install.log
exec > >(tee -a "$LOG") 2>&1
echo "=== ROS2 install started $(date) ==="

# --- 0. DNS sanity check (this is what failed on the laptop) ---
# NB: check plain-HTTP packages.ros.org (its TLS cert doesn't cover the bare host)
# plus an HTTPS endpoint, so a cert quirk doesn't false-positive as "no network".
if ! { curl -sSf -m 10 http://packages.ros.org >/dev/null 2>&1 && \
       curl -sSf -m 10 https://raw.githubusercontent.com/ros/rosdistro/master/ros.key >/dev/null 2>&1; }; then
    echo "DNS/network broken, applying static resolv.conf fix..."
    grep -q 'generateResolvConf' /etc/wsl.conf 2>/dev/null || cat >> /etc/wsl.conf <<'EOF'

[network]
generateResolvConf = false
EOF
    rm -f /etc/resolv.conf
    printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' > /etc/resolv.conf
    chattr +i /etc/resolv.conf 2>/dev/null || true
    curl -sSf -m 10 http://packages.ros.org >/dev/null || { echo "FATAL: still no network"; exit 1; }
fi
echo "Network OK"

# --- 1. ROS2 apt repo ---
apt-get update
apt-get install -y software-properties-common curl gnupg lsb-release
add-apt-repository -y universe
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list

# --- 2. Install the stack ---
apt-get update
apt-get upgrade -y
apt-get install -y \
    ros-humble-desktop \
    ros-dev-tools \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    'ros-humble-turtlebot3*' \
    gazebo \
    ros-humble-gazebo-ros-pkgs \
    python3-colcon-common-extensions \
    python3-rosdep

# --- 3. rosdep ---
[ -f /etc/ros/rosdep/sources.list.d/20-default.list ] || rosdep init
sudo -u "${SUDO_USER:-$(id -un 1000 2>/dev/null || echo root)}" rosdep update || rosdep update

# --- 4. Shell setup for the default user ---
USER_HOME=$(getent passwd 1000 | cut -d: -f6)
if [ -n "$USER_HOME" ] && ! grep -q 'ros/humble/setup.bash' "$USER_HOME/.bashrc" 2>/dev/null; then
    cat >> "$USER_HOME/.bashrc" <<'EOF'

# ROS2 Humble
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
export ROS_DOMAIN_ID=30
EOF
fi

echo "=== ROS2 install finished OK $(date) ==="
