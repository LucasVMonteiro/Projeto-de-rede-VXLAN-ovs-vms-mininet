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

