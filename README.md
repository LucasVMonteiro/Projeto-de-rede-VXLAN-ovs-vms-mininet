# Projeto-de-rede-VXLAN-ovs-vms-mininet
Projeto de uma simples rede vxlan que conecta containers

O projeto envolve tres maquinas virtuais, uma com mininet que une as duas VMs por meio das duas redes NAT,

![ imagem 1 - Vista completa da rede. ](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/136ca614-c56b-4216-9691-4efceaa9f82b)


| Container   | IP          | VID         | MAC               |VM         |
|------------:|------------:|------------:|------------------:|:----------|
|Container1   |10.20.30.2/24|          100| 00:00:00:00:00:01 |VM1        |
|Container2   |10.20.30.2/24|          200| 00:00:00:00:00:02 |VM1        |
|Container3   |10.20.30.3/24|          100| 00:00:00:00:00:03 |VM2        |
|Container4   |10.20.30.3/24|          200| 00:00:00:00:00:04 |VM2        |
---
| REDE        | IP          | VM          | 
|------------:|------------:|------------:|
|NAT1         |10.1.0.0/24|VM1 VM-mininet|
|NAT2         |10.2.0.0/24|VM2 VM-mininet|
---
|Pacotes usado| VM               |
|------------:|------------------|
|Open vSwitch |VM1 VM2 VM-mininet|
|Docker       |VM1 VM2 VM-mininet|
|Mininet      |VM1 VM2           |
---
| VM          | Imagem      | RAM         | CPUs              |NICs        |Rede       | Interface Modo Promiscuo |
|------------:|------------:|------------:|------------------:|-----------:|:----------|:----------|
|VM1          |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |1           |NAT1       |sim|
|VM2          |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |1           |NAT2       |sim|
|VM-mininet   |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |2           |NAT1 & NAT2|sim|

## Instalacao de pacotes

1 - Crie as VMs usando as especificacoes da tabela acima:

2 - Instale os pacotes na VM1, VM2:


sudo apt install -y openvswitch-switch docker.io

3 - Instale os pacotes na VM-mininet:

sudo apt install -y openvswitch-switch docker.io mininet


## Configurando OvS e Docker -- Repita o procedimento para VM1 e VM2, 

1 - Criar Bridge no OvS


sudo ovs-vsctl add-br ovs-br1

2 - Criar Containers


sudo docker run --name container1 -dit --net=none alpine

sudo docker run --name container2 -dit --net=none alpine

3 - Conectar containers a bridge


### Ao adicionar a porta de um container execute sudo ovs-vsctl show e veja qual foi adicionada
### exemplo: container1 interface ABCDEFG

sudo ovs-docker add-port ovs-br1 eth0 container1 --ipaddress=10.20.30.2/24 --gateway=10.20.30.1 --macaddress="00:00:00:00:00:01"

sudo ovs-docker add-port ovs-br1 eth0 container2 --ipaddress=10.20.30.2/24 --gateway=10.20.30.1 --macaddress="00:00:00:00:00:02"


4 - Criar porta para vxlan0 e vxlan1

### Em remote_ip coloque o ip da outra VM
### exemplo: se estiver configurando na VM1 coloque o ip da VM2


sudo ovs-vsctl add-port ovs-br1 vxlan0 -- set interface vxlan0 type=vxlan options:remote_ip=[IP_VM_EXTERNA] options:key=100

sudo ovs-vsctl add-port ovs-br1 vxlan1 -- set interface vxlan1 type=vxlan options:remote_ip=[IP_VM_EXTERNA] options:key=200


5 - Criando regras de fluxo

#### Caso esteja na VM1

```
table=0,in_port=[OF PORT],actions=set_field:100->tun_id,resubmit(,1)
table=0,in_port=[OF PORT],actions=set_field:200->tun_id,resubmit(,1)
table=0,actions=resubmit(,1)

table=1,tun_id=100,dl_dst=[mac do container 1],actions=output:[OF PORT]
table=1,tun_id=200,dl_dst=[mac do container 2],actions=output:[OF PORT]
table=1,tun_id=100,dl_dst=[mac do container 3],actions=output:[OF PORT]
table=1,tun_id=200,dl_dst=[mac do container 4],actions=output:[OF PORT]
table=1,tun_id=100,arp,nw_dst=10.20.30.2,actions=output:[OF PORT]
table=1,tun_id=200,arp,nw_dst=10.20.30.2,actions=output:[OF PORT]
table=1,tun_id=100,arp,nw_dst=10.20.30.3,actions=output:[OF PORT]
table=1,tun_id=200,arp,nw_dst=10.20.30.3,actions=output:[OF PORT]
table=1,priority=100,actions=drop
```

#### Caso esteja na VM2

```
table=0,in_port=[OF PORT],actions=set_field:100->tun_id,resubmit(,1)
table=0,in_port=[OF PORT],actions=set_field:200->tun_id,resubmit(,1)
table=0,actions=resubmit(,1)

table=1,tun_id=100,dl_dst=[mac do container 3],actions=output:[OF PORT]
table=1,tun_id=200,dl_dst=[mac do container 4],actions=output:[OF PORT]
table=1,tun_id=100,dl_dst=[mac do container 1],actions=output:[OF PORT]
table=1,tun_id=200,dl_dst=[mac do container 2],actions=output:[OF PORT]
table=1,tun_id=100,arp,nw_dst=10.20.30.3,actions=output:[OF PORT]
table=1,tun_id=200,arp,nw_dst=10.20.30.3,actions=output:[OF PORT]
table=1,tun_id=100,arp,nw_dst=10.20.30.2,actions=output:[OF PORT]
table=1,tun_id=200,arp,nw_dst=10.20.30.2,actions=output:[OF PORT]
table=1,priority=100,actions=drop

```

