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

- Redes VM-Mininet
  
![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/d10b8b65-d32d-4630-93fd-3ce0dd96196d)

- Rede VM1

![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/8aa0fa85-faaf-44da-b19f-5835de41c7b1)

  
- Rede VM2
  
![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/dab6d74a-76f8-4381-a697-9838bd6db49a)


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

As regras de fluxo como o nome já diz, ditam a forma que o tráfego dentro do switch tem que assumir, elas são parte do protocolo OpenFlow e podem ser encontradas neste [link](https://opennetworking.org/wp-content/uploads/2013/04/openflow-spec-v1.3.1.pdf),capitulo 5.

Nesta etapa vamos criar regras de fluxo para direcionar o fluxo de dados dos containers para um túnel vxlan, encaminhar os pacotes tunelados para os devidos containers e redirecionar os pacotes ARP.

![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/fdb25fa0-e689-49fc-a4d9-d6703b3e2374)

Elas tem uma ordem de execução, sendo aquelas com tag "table=0" executadas primeiro, ate a n-ésima ordem de execucao.



A regra de fluxo pode ser armazenada em um arquivo de texto, portanto crie um com o nome que desejar
em seguida vamos escrever as regras:
Aqui utilizaremos as informaçoes sobre o numero da porta conectada ao container A e B.
1. Aplicando tunelamento ao trafego dos containers A e B.

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

2. Direcionando o trafego que vem da vxlan e que tem um Mac de destino especifico para uma porta OF associada ao container.
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


3. Tratando do tráfego ARP, aplicamos aos tuneis vxlan que se destinam aos IPs dos containers para que eles vao para a porta do container A ou B, ou que saiam pela porta vxlan.
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

Ao concluir a montagem da tabela precisamos carregá-la no OvS:

```
sudo ovs-ofctl add-flows ovs-br1 regras_fluxo.txt
```
Para apagar as regras>``` sudo ovs-ofctl del-flows ovs-br1```

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

No primeiro passo instalamos o Mininet, docker e OvS na maquina que possui o roteador virtual.

Agora vamos utilizar o script que criará uma rede no mininet em que sera possivel estabelecer a conexão entre a VM1 e VM2

Copie este codigo e salve no formato .py

neste caso ele se chama 1switch1router.py

```

#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import Intf

## Classe LinuxRouter é um roteador nativo do Linux.
class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    # pylint: disable=arguments-differ
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    # pylint: disable=arguments-differ
    def build( self, **_opts ):

        ## IPS DO ROTEADOR PAR NAT1 E NAT2
        defaultIPgws1 = '10.1.0.254/24'  # IP address for r0-eth1
        defaultIPgws2 = '10.3.0.254/24'

        
        ## ADICIONANDO ROTEADOR
        router = self.addNode( 'r0', cls=LinuxRouter, ip=defaultIPgws1 )

        ## ADICIONANDO SWITCH OvS , NOME DA BRIDGE = s1
        s1 = self.addSwitch('s1')


        ## CRIANDO DUAS INTERFACES NO SWITCH, CADA UMA CONECTADA AO MESMO ROTEADOR, REPRESENTANDO DUAS REDES.
        self.addLink( s1, router, intfName1='s1-r0-eth1', intfName2='r0-eth1',
                      params2={ 'ip' : defaultIPgws1 } )  # for clarity
        self.addLink( s1, router, intfName1='s1-r0-eth2', intfName2='r0-eth2',
                      params2={ 'ip' : defaultIPgws2 } )  # for clarity

        ## CRIANDO DOIS HOSTS, PARA FINS DE TESTES. NAO NECESSARIO
        h1 = self.addHost( 'h1', ip='10.1.0.220/24',
                           defaultRoute= 'via {}'.format(defaultIPgws1[0:-3]))
        h2 = self.addHost( 'h2', ip='10.3.0.220/24',
                           defaultRoute= 'via {}'.format(defaultIPgws2[0:-3]))

        ## LINK ENTRE SWITCH E HOST VIRTUAL
        self.addLink(s1,h1, intfName1='s1-h1-eth0')
        self.addLink(s1,h2, intfName1='s1-h2-eth0')


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo,
                   waitConnected=True )  # controller is used by s1-s3


    ## Aqui, substitua enp0s8 e enp0s9 pela interface conectada a NAT1 e NAT2.
    _intf1 = Intf('enp0s8',node=net['s1']) ## este comando substitui > sudo ovs-vsctl add-port ovs-br1 enp0s8 
    _intf2 = Intf('enp0s9',node=net['s1'])

    net.start()
    info( '*** Routing Table on Router:\n' )
    info( net[ 'r0' ].cmd( 'route' ) )
    CLI( net )
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    run()


```

Explicando a conexao entre interface e switch:
```
_intf1 = Intf('enp0s8',node=net['s1'])
_intf2 = Intf('enp0s9',node=net['s1'])
```
dentro da VM-mininet eu verifico as interfaces utilizando "ip l"

![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/ad3a1f52-4745-47d6-984f-88be4b13a0a2)

através do MAC eu sei que enp0s8 é a interface conectada ao NAT1 e enp0s9 conectada ao NAT2. Para se certificar abra as propriedades de rede da sua VM.

![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/45bfab85-bd72-4ba9-8efe-deca66903d68)

observe que o endereço MAC do adaptador2 é o mesmo da interface enp0s8

Após customizar o codigo python com base na sua rede, execute ``` sudo python3 1switch1router.py ```


## Configurando Tabela de rota VM1 e VM2.

Como estamos conectando duas VMs de redes diferentes por meio do mininet, precisamos alterar o ip gateway da VM1 e VM2.
O motivo é que por padrão a VM conectada a uma rede NAT tem como gateway o endereço 10.3.0.1 ou 10.2.0.1 
portanto iremos alterar para o gateway que definimos no mininet, 10.3.0.254 e 10.2.0.254


Se sua VM1 tem ip base 10.2.0.0/24
```
    sudo ip route del default via 10.2.0.1

    sudo ip route add default via 10.2.0.254
```

Se sua VM2 tem ip base 10.3.0.0/24
```
    sudo ip route del default via 10.3.0.1

    sudo ip route add default via 10.3.0.254
```
![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/15d2531d-50f1-4204-8ae5-3adccf5eae00)


Verifique as tabelas de rota
```
    sudo ip r
```




## Realizando teste.

Ao finalizar todas as configurações vamos testar a comunição entre as VMs e em seguida entre os containers

VM1
![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/ff6a8e1b-28cc-4e07-932c-70bd465f3ea2)

VM2
![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/3e6af34b-adfb-4d17-8324-7cafc6af5ead)

Teste o ping entre a VM1 e VM2
```
    ping 10.1.0.9
```
![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/7cedcb56-2a08-43c0-9150-8a66c177333b)



Lembre que container1 esta na mesma rede vxlan que container3
assim como o 2 esta na mesma rede que o 4
![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/45a5c3b1-3ad7-4b3e-b952-9704534f41de)

![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/dbd0ca3e-0d46-4d66-8543-020a6e76b3ec)


![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/2a4ed88d-70e1-4234-b9f4-391e21f4131f)


![image](https://github.com/LucasVMonteiro/Projeto-de-rede-VXLAN-ovs-vms-mininet/assets/59663614/01438482-86ef-4d0e-9c8f-a8699b427d61)




Teste o ping entre a Container1 e Container3
```
    sudo docker exec container1 ping 10.20.30.3
```

Teste o ping entre a Container2 e Container4
```
    sudo docker exec container2 ping 10.20.30.3
```


