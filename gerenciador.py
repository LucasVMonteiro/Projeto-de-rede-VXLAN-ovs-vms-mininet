import subprocess
import re


CONTAINER_A_NAME = "container1"
CONTAINER_B_NAME = "container2"

MACADDRESS_A = "00:00:00:00:00:01"
MACADDRESS_B = "00:00:00:00:00:02"
MACADDRESS_EXTA = "00:00:00:00:00:03"
MACADDRESS_EXTB = "00:00:00:00:00:04"

IP_CONTAINER = "10.20.30.2/24"

IP_VM_EXTERNA = "10.1.0.9"

NAME_BRIDGE = "ovs-br1"

PORT_NAME = ""

VXLAN0_NAME = "vxlan0"
VXLAN1_NAME = "vxlan1"

NOME_ARQUIVO_FLOWS = "flows23"

primeira_vez = False

## comandos

COMANDO_CRIAR_BRIDGE = f'sudo ovs-vsctl add-br {NAME_BRIDGE}'

COMANDO_CRIAR_CONTAINER_A = f"sudo docker run --name {CONTAINER_A_NAME} -dit --net=none alpine"
COMANDO_CRIAR_CONTAINER_B = f"sudo docker run --name {CONTAINER_B_NAME} -dit --net=none alpine"

COMANDO_ADD_CONTAINER_A_OVS = f'sudo ovs-docker add-port {NAME_BRIDGE} eth0 {CONTAINER_A_NAME} --ipaddress={IP_CONTAINER} --gateway=10.20.30.1 --macaddress="{MACADDRESS_A}"'

COMANDO_ADD_CONTAINER_B_OVS = f'sudo ovs-docker add-port {NAME_BRIDGE} eth0 {CONTAINER_B_NAME} --ipaddress={IP_CONTAINER} --gateway=10.20.30.1 --macaddress="{MACADDRESS_B}"'

COMANDO_LISTAR_PORTAS_OF = f"sudo ovs-ofctl show {NAME_BRIDGE}"

COMANDO_DELETAR_PORTA = f"sudo ovs-vsctl del-port {NAME_BRIDGE} {PORT_NAME}"

COMANDO_LISTAR_PORTAS_BR = "sudo ovs-vsctl show"

COMANDO_CRIAR_VXLAN0 = f"sudo ovs-vsctl add-port {NAME_BRIDGE} {VXLAN0_NAME} -- set interface {VXLAN0_NAME} type=vxlan options:remote_ip={IP_VM_EXTERNA} options:key=100"

COMANDO_CRIAR_VXLAN1 = f"sudo ovs-vsctl add-port {NAME_BRIDGE} {VXLAN1_NAME} -- set interface {VXLAN1_NAME} type=vxlan options:remote_ip={IP_VM_EXTERNA} options:key=100"

COMANDO_DELETAR_FLOWS = f'sudo ovs-ofctl del-flows {NAME_BRIDGE}'

COMANDO_ADICIONAR_FLOWS = f'sudo ovs-ofctl add-flows {NAME_BRIDGE} {NOME_ARQUIVO_FLOWS}'

COMANDO_LISTAR_REGRAS_FLOWS = f'sudo ovs-ofctl dump-flows {NAME_BRIDGE}'

def extrair_ofports(stdout_comando_listar_portas_of):

    #busca do padrao
    resultado= re.findall("[0-9]\(.*\)\:",stdout_comando_listar_portas_of)
    print("\n")
    print(resultado)
    #processamento
    interfaces_of = []
    for res in resultado:

        interfaces_of.append((res[0],res[2:-2]))


    resultado= re.findall("[0-9][0-9]\(.*\)\:",stdout_comando_listar_portas_of)
    if len(resultado) > 0:
        for res in resultado:
            interfaces_of.append((int(f"{res[0]}{res[1]}"),res[3:-2]))

    return interfaces_of

if primeira_vez:
    
    subprocess.run(COMANDO_CRIAR_BRIDGE,shell=True)

    subprocess.run(COMANDO_CRIAR_CONTAINER_A,shell=True)
    subprocess.run(COMANDO_CRIAR_CONTAINER_B,shell=True)

    subprocess.run(COMANDO_CRIAR_VXLAN0,shell=True)
    subprocess.run(COMANDO_CRIAR_VXLAN1,shell=True)




blacklist = [VXLAN0_NAME,VXLAN1_NAME,'veth0']
info_containers = []



## execute apos iniciar os containers sudo docker start container1 container2
#---------------------------------------------------------------------------
subprocess.run(COMANDO_ADD_CONTAINER_A_OVS,shell=True)

## CAPTURANDO INTERFACESS DA LISTA DE INTERFACES OPENFLOW
teste = subprocess.run(COMANDO_LISTAR_PORTAS_OF,capture_output=True, text=True, shell=True)
print(teste.stdout)

#extrai os numeros das portas e seu nome
portas_extraidas = extrair_ofports(teste.stdout) ## eh recalculada a cada etapa de listagem de of ports


#classificando porta conectada ao  container
for intf in portas_extraidas:
    if intf[1] in blacklist:
        pass
    else:
        info_containers.append((CONTAINER_A_NAME,intf[1],intf[0]))#nome do container, nome da interface of, numero da interface of
        blacklist.append(intf[1])

#---------------------------------------------------------------------------
subprocess.run(COMANDO_ADD_CONTAINER_B_OVS,shell=True)

## CAPTURANDO INTERFACESS DA LISTA DE INTERFACES OPENFLOW
teste = subprocess.run(COMANDO_LISTAR_PORTAS_OF,capture_output=True, text=True, shell=True)
print(teste.stdout)

#extrai os numeros das portas e seu nome
portas_extraidas = extrair_ofports(teste.stdout)


#classificando porta conectada ao  container
for intf in portas_extraidas:
    if intf[1] in blacklist:
        pass
    else:
        info_containers.append((CONTAINER_B_NAME,intf[1],intf[0]))#nome do container, nome da interface of, numero da interface of
        blacklist.append(intf[1])

#---------------------------------------------------------------------------

# funciona se as vxlans jah estejam criadas

teste = subprocess.run(COMANDO_LISTAR_PORTAS_OF,capture_output=True, text=True, shell=True)
print(teste.stdout)
portas_extraidas = extrair_ofports(teste.stdout)

print(portas_extraidas)
print("\n\n\n")
print(info_containers)


for intf in portas_extraidas:
    if intf[1] == VXLAN0_NAME:
        ofports_vxlan0 = intf
    elif intf[1] == VXLAN1_NAME:     
        ofports_vxlan1 = intf

REGRA1  = f'table=0,in_port={info_containers[0][2]},actions=set_field:100->tun_id,resubmit(,1)'
REGRA2  = f'table=0,in_port={info_containers[1][2]},actions=set_field:200->tun_id,resubmit(,1)'
REGRA3  = f'table=0,actions=resubmit(,1)'
REGRA4  = f'table=1,tun_id=100,dl_dst={MACADDRESS_A},actions=output:{info_containers[0][2]}'
REGRA5  = f'table=1,tun_id=200,dl_dst={MACADDRESS_B},actions=output:{info_containers[1][2]}'
REGRA6  = f'table=1,tun_id=100,dl_dst={MACADDRESS_EXTA},actions=output:{ofports_vxlan0[0]}'
REGRA7  = f'table=1,tun_id=200,dl_dst={MACADDRESS_EXTB},actions=output:{ofports_vxlan1[0]}'
REGRA8  = f'table=1,tun_id=100,arp,nw_dst=10.20.30.2,actions=output:{info_containers[0][2]}'
REGRA9  = f'table=1,tun_id=200,arp,nw_dst=10.20.30.2,actions=output:{info_containers[1][2]}'
REGRA10 = f'table=1,tun_id=100,arp,nw_dst=10.20.30.3,actions=output:{ofports_vxlan0[0]}'
REGRA11 = f'table=1,tun_id=200,arp,nw_dst=10.20.30.3,actions=output:{ofports_vxlan1[0]}'
REGRA12 = f'table=1,priority=100,actions=drop'

REGRAS = [REGRA1,REGRA2,REGRA3,REGRA4,
          REGRA5,REGRA6,REGRA7,REGRA8,
          REGRA9,REGRA10,REGRA11,REGRA12]
          
with open(NOME_ARQUIVO_FLOWS,'w') as f:
    for regra in REGRAS:
        f.write(regra+'\n')
    f.close()


subprocess.run(COMANDO_ADICIONAR_FLOWS,shell=True)
output_regrasfluxo = subprocess.run(COMANDO_LISTAR_REGRAS_FLOWS,shell=True,capture_output=True,text=True)
print(output_regrasfluxo.stdout)
