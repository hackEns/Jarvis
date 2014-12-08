# Citizenwatt Python 3.4 install script
# Launch as root

# Upgrade Raspbian
apt-get update
apt-get --yes upgrade

# Install
apt-get --yes install python3 gcc python3-pip python3-dev

# Python modules
pip-3.2 install -r ../devel-req.txt

# Remove unused packets
apt-get --yes autoremove --purge
