# Projeto-de-rede-VXLAN-ovs-vms-mininet
Projeto de uma simples rede vxlan que conecta containers

O projeto envolve tres maquinas virtuais, uma com mininet que une as duas VMs por meio das duas redes NAT.

![ imagem 1 - Vista completa da rede. ](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/136ca614-c56b-4216-9691-4efceaa9f82b)


- Tabela de containers, para facilitar use estes parametros.

| Container   | IP          | VID         | MAC               |VM         |
|------------:|------------:|------------:|------------------:|:----------|
|Container1   |10.20.30.2/24|          100| 00:00:00:00:00:01 |VM1        |
|Container2   |10.20.30.2/24|          200| 00:00:00:00:00:02 |VM1        |
|Container3   |10.20.30.3/24|          100| 00:00:00:00:00:03 |VM2        |
|Container4   |10.20.30.3/24|          200| 00:00:00:00:00:04 |VM2        |

---
É necessario criar duas redes NATs para isolar a VM1 da VM2.

| REDE        | IP          | VM          | 
|------------:|------------:|------------:|
|NAT1         |10.1.0.0/24|VM1 VM-mininet|
|NAT2         |10.2.0.0/24|VM2 VM-mininet|

- Para criar as redes nat no VirtualBox pressione Ctrl H:
  ![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/e1f8f1a1-33f2-4556-bcb1-8d8db14c94d2)

---

Veja os pacotes de software utilizado e onde se aplica.

|Pacotes usado| VM               |
|------------:|------------------|
|Open vSwitch |VM1 VM2 VM-mininet|
|Docker       |VM1 VM2 VM-mininet|
|Mininet      |VM1 VM2           |

---
Utilize esta imagem ISO para todas as VMs envolvidas.

| VM          | Imagem      | RAM         | CPUs              |NICs        |Rede       | Interface Modo Promiscuo |
|------------:|------------:|------------:|------------------:|-----------:|:----------|:----------|
|VM1          |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |1           |NAT1       |sim|
|VM2          |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |1           |NAT2       |sim|
|VM-mininet   |[Ubuntu Server 22.04 LTS](https://ubuntu.com/download/server)|         2048| 2                 |2           |NAT1 & NAT2|sim|

# Estrutura do guia:

1. Instalação dos pacotes.
2. Configuração do OvS e Docker para VM1 e VM2.
3. Configurando o Mininet.
4. Configurando Tabela de rota VM1 e VM2.
5. Realizando teste.
6. Verificando pacotes com TCPDUMP.


## Instalacao de pacotes

1 - Crie as VMs usando as especificacoes da tabela acima:

2 - Instale os pacotes na VM1, VM2:


```sudo apt install -y openvswitch-switch docker.io```

3 - Instale os pacotes na VM-mininet:

``` sudo apt install -y openvswitch-switch docker.io mininet ```


## Configurando OvS e Docker -- Repita o procedimento para VM1 e VM2, 

1 - Criar Bridge no OvS


``` sudo ovs-vsctl add-br ovs-br1```

2 - Criar Containers


```
sudo docker run --name container1 -dit --net=none alpine

sudo docker run --name container2 -dit --net=none alpine
```

3 - Conectar containers a bridge

Ao adicionar um container ao OvS, verifique atraves de ``` sudo ovs-ofctl show ovs-br1 ``` qual foi a nova interface criada e anote.

```
sudo ovs-docker add-port ovs-br1 eth0 container1 --ipaddress=10.20.30.2/24 --gateway=10.20.30.1 --macaddress="00:00:00:00:00:01"

sudo ovs-docker add-port ovs-br1 eth0 container2 --ipaddress=10.20.30.2/24 --gateway=10.20.30.1 --macaddress="00:00:00:00:00:02"
```
Exemplo:
![Captura de tela 2023-12-26 160215](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/d65bd276-027a-4e61-9d62-488b2c6a9191)
A interface adicionada se chama 655f584cf11d4_l, esta na porta 1, e conectada ao container3. Essa informação é util para montar as regras de fluxo.

4 - Criar porta para vxlan0 e vxlan1

### Em remote_ip coloque o ip da outra VM
### exemplo: se estiver configurando na VM1 coloque o ip da VM2


```
     sudo ovs-vsctl add-port ovs-br1 vxlan0 -- set interface vxlan0 type=vxlan options:remote_ip=[IP_VM_EXTERNA] options:key=100
     sudo ovs-vsctl add-port ovs-br1 vxlan1 -- set interface vxlan1 type=vxlan options:remote_ip=[IP_VM_EXTERNA] options:key=200
```


5 - Criando regras de fluxo

As regras de fluxo como o nome já diz, ditam a forma que o tráfego dentro do switch tem que assumir, elas são parte do protocolo OpenFlow e podem ser encontradas neste [link](https://opennetworking.org/wp-content/uploads/2013/04/openflow-spec-v1.3.1.pdf) mais especificamente no capitulo 5.

Nesta etapa vamos criar regras de fluxo para direcionar o fluxo de dados dos containers para um túnel vxlan, encaminhar os pacotes tunelados para os devidos containers e redirecionar os pacotes ARP.

![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/fdb25fa0-e689-49fc-a4d9-d6703b3e2374)

Elas tem uma ordem de prioridade, sendo aquelas com tag "table=0" executadas primeiro, ate a n-ésima ordem de execucao.



A regra de fluxo pode ser armazenada em um arquivo de texto, portanto crie um com o nome que desejar
em seguida vamos escrever as regras:
Aqui utilizaremos as informaçoes sobre o numero da porta conectada ao container A e B.
1- Aplicando tunelamento ao trafego dos containers A e B.

```
     table=0,in_port=[OF PORT container 1],actions=set_field:100->tun_id,resubmit(,1)
     table=0,in_port=[OF PORT container 2],actions=set_field:200->tun_id,resubmit(,1) 
     table=0,actions=resubmit(,1)
```

- table=0 : ordem de execução, primeira a ser executada.
- in_port=ofport : indica onde sera aplicada a regra, neste caso em uma porta OpenFlow que esta associada a interface conectada ao conteiner A.
- actions= : define o conjuto de ações a serem tomadas
- set_field:200->tun_id : a ação set_field define o túnel de ID 200, neste caso VID da vxlan, como regra para o pacote que chega na porta in_port.
- resubmit : indica a proxima tabela de regras para os pacotes que nao se ajustam a primeira regra.

2- Direcionando o trafego que vem da vxlan e que tem um Mac de destino especifico para uma porta OF associada ao container.
```
table=1,tun_id=100,dl_dst=[mac do container 1],actions=output:[OF PORT container 1]
table=1,tun_id=200,dl_dst=[mac do container 2],actions=output:[OF PORT container 2]
```
- tabel=1 : a segunda regra a ser aplicada.
- tun_id=100 : indicamos que a regra se aplica ao tráfego do tunel 100 e 200. VID.
- dl_dst : indicamos que a regra se aplica ao tráfego que se destina ao MAC especificado, neste caso é o mac correspondente ao container.
- actions=output:[portas] : como ação, redirecionamos para uma porta de saida, neste caso ela corresponde a porta do container.

  
```
table=1,tun_id=100,dl_dst=[mac do container 3],actions=output:[OF PORT vxlan0]
table=1,tun_id=200,dl_dst=[mac do container 4],actions=output:[OF PORT vxlan1]

```
Aqui aplicamos a regra de redirecionamento de tráfego para pacotes vxlan que se destinam a macs externos, no caso os containers de outra vm.
Observe que a ação tomada é redirecionar para porta OF ligada a vxlan.


3- Tratando do tráfego ARP, aplicamos aos tuneis vxlan que se destinam aos IPs dos containers para que eles vao para a porta do container A ou B, ou que saiam pela porta vxlan.
```
table=1,tun_id=100,arp,nw_dst=10.20.30.3,actions=output:[OF PORT container 1]
table=1,tun_id=200,arp,nw_dst=10.20.30.3,actions=output:[OF PORT container 2]
table=1,tun_id=100,arp,nw_dst=10.20.30.2,actions=output:[OF PORT vxlan0]
table=1,tun_id=200,arp,nw_dst=10.20.30.2,actions=output:[OF PORT vxlan1]
table=1,priority=100,actions=drop
```
exemplo: 

```table=1,tun_id=100,arp,nw_dst=10.20.30.2,actions=output:[OF PORT vxlan0]```
- todo trafego da vxlan com VID 100 e que tem como destino o ip 10.20.30.2( outro container) sai pela porta OF da vxlan0



### Aqui as regras completas e separadas para vm1 e vm2.
#### Caso esteja na VM1

```
table=0,in_port=[OF PORT container 1],actions=set_field:100->tun_id,resubmit(,1)
table=0,in_port=[OF PORT container 2],actions=set_field:200->tun_id,resubmit(,1)
table=0,actions=resubmit(,1)

table=1,tun_id=100,dl_dst=[mac do container 1],actions=output:[OF PORT container 1]
table=1,tun_id=200,dl_dst=[mac do container 2],actions=output:[OF PORT container 2]
table=1,tun_id=100,dl_dst=[mac do container 3],actions=output:[OF PORT vxlan0]
table=1,tun_id=200,dl_dst=[mac do container 4],actions=output:[OF PORT vxlan1]
table=1,tun_id=100,arp,nw_dst=10.20.30.3,actions=output:[OF PORT container 1]
table=1,tun_id=200,arp,nw_dst=10.20.30.3,actions=output:[OF PORT container 2]
table=1,tun_id=100,arp,nw_dst=10.20.30.2,actions=output:[OF PORT vxlan0]
table=1,tun_id=200,arp,nw_dst=10.20.30.2,actions=output:[OF PORT vxlan1]
table=1,priority=100,actions=drop
```

#### Caso esteja na VM2

```
table=0,in_port=[OF PORT container 3],actions=set_field:100->tun_id,resubmit(,1)
table=0,in_port=[OF PORT container 4],actions=set_field:200->tun_id,resubmit(,1)
table=0,actions=resubmit(,1)

table=1,tun_id=100,dl_dst=[mac do container 3],actions=output:[OF PORT container 3]
table=1,tun_id=200,dl_dst=[mac do container 4],actions=output:[OF PORT container 4]
table=1,tun_id=100,dl_dst=[mac do container 1],actions=output:[OF PORT vxlan0]
table=1,tun_id=200,dl_dst=[mac do container 2],actions=output:[OF PORT vxlan1]
table=1,tun_id=100,arp,nw_dst=10.20.30.2,actions=output:[OF PORT container 3]
table=1,tun_id=200,arp,nw_dst=10.20.30.2,actions=output:[OF PORT container 4]
table=1,tun_id=100,arp,nw_dst=10.20.30.3,actions=output:[OF PORT vxlan0]
table=1,tun_id=200,arp,nw_dst=10.20.30.3,actions=output:[OF PORT vxlan1]
table=1,priority=100,actions=drop

```
## Configurando Mininet





