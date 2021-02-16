#!/bin/sh

if ! command -v L2A_Process &> /dev/null
then
  echo "Installing sen2cor for top-atmosphere correction of Sentinel-2"
  wget -nv http://step.esa.int/thirdparties/sen2cor/2.8.0/Sen2Cor-02.08.00-Linux64.run
  install_dir=~/sen2cor
  bash Sen2Cor-02.08.00-Linux64.run --target $install_dir
  full_path=$(cd "$(dirname $install_dir)"; pwd -P)/$(basename $install_dir)
  echo "export PATH=\"$full_path/bin:\$PATH\"" >> ~/.bashrc
  . ~/.bashrc
  rm Sen2Cor-02.08.00-Linux64.run
else
  echo "L2A_Process for Sentinel-2 correction is already installed"
fi