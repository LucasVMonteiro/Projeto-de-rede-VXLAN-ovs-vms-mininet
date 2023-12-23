# Projeto-de-rede-VXLAN-ovs-vms-mininet
Projeto de uma simples rede vxlan que conecta containers

![ imagem 1 - Vista completa da rede. ](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/136ca614-c56b-4216-9691-4efceaa9f82b)


| Container   | IP          | VID         | MAC               |VM         |
|------------:|------------:|------------:|------------------:|:----------|
|Container1   |10.20.30.2/24|          100| 00:00:00:00:00:01 |VM1        |
|Container2   |10.20.30.2/24|          200| 00:00:00:00:00:02 |VM1        |
|Container3   |10.20.30.3/24|          100| 00:00:00:00:00:03 |VM2        |
|Container4   |10.20.30.3/24|          200| 00:00:00:00:00:04 |VM2        |

| VM          | Imagem      | RAM         | CPUs              |NICs        |Rede       |
|------------:|------------:|------------:|------------------:|-----------:|:----------|
|VM1          |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |1           |NAT1       |
|VM2          |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |1           |NAT2       |
|VM-mininet   |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |2           |NAT1 & NAT2|
