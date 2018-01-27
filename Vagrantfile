# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/xenial64"

  # config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
  #   vb.memory = "1024"
  # end
  config.vm.provision "shell", inline: <<-SHELL
     apt-get update
     apt-get upgrade -y
     apt-get install -y libssl-dev
     apt-get install -y python3-pip
     cd /vagrant && make test
     steempy info
  SHELL
end
