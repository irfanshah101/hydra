#!/bin/bash -e
dst_work_dir=$1

echo "**** $dst_work_dir"
# Pre Script
echo "Run pre script"
wget https://raw.githubusercontent.com/zeromq/cppzmq/master/zmq.hpp
mv zmq.hpp ${dst_work_dir}/hydra-master/src/main/c/zmq
sudo apt-get -y install python-dev python-pip

echo "Setup virtual environemnt"
# Setup virtual environment
sudo pip install virtualenv
venv_dir="/home/$USER/venv"
mkdir ${venv_dir}
virtualenv ${venv_dir}
source ${venv_dir}/bin/activate

echo "Install Hydra"
sudo apt-get -y install protobuf-c-compiler libzmq3-dev protobuf-compiler libprotobuf-dev
pip install pybuilder
pushd ${dst_work_dir}/hydra-master
pyb install_dependencies
pyb install

echo "Run script"
pyb publish -x run_unit_tests
pyb install -x run_unit_tests

popd
