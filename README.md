# Projeto-de-rede-VXLAN-ovs-vms-mininet
Projeto de uma simples rede vxlan que conecta containers

![ imagem 1 - Vista completa da rede. ](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/136ca614-c56b-4216-9691-4efceaa9f82b)

VM1 --- Container1 00:00:00:00:00:01 10.20.30.2/24 VXLAN0
    \-- Container2 00:00:00:00:00:02 10.20.30.2/24 VXLAN1

VM2 --- Container3 00:00:00:00:00:03 10.20.30.3/24 VXLAN0
    \-- Container4 00:00:00:00:00:04 10.20.30.3/24 VXLAN1
