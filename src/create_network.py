

import time
import json
import argparse
from time import sleep
import os
import re
import sys
import argparse
from mininet.node import Node
from mininet.cli import CLI
from mininet.topolib import TreeTopo
from mininet.util import quietRun
from mininet.topo import Topo
from minisched import scheduler
from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info, debug,error
from mininet.net import Mininet
from mininet.node import OVSController, DefaultController, Host, OVSKernelSwitch
from mininet.link import TCLink, Intf, Link

class Min( Topo ):
    "Minimal topology with a single switch and two hosts"

    def build( self ):
        # Create a switch
        from mininet.topo import Topo

        s1=self.addSwitch('s1')
        root=self.addNode('root',ip='192.168.2.254/24',inetIntf='eth0',inNamespace=False)
        self.addLink(s1,root,bw=100)



class Minievents(Mininet):
    def __init__(self, topo=None, switch=OVSKernelSwitch, host=Host,
                 controller=DefaultController, link=Link, intf=Intf,
                 build=True, xterms=False, cleanup=False, ipBase='10.0.0.0/8',
                 inNamespace=False,
                 autoSetMacs=False, autoStaticArp=False, autoPinCpus=False,
                 listenPort=None, waitConnected=False, events_file=None):
        super(Minievents, self).__init__(topo=topo, switch=switch, host=host, controller=controller,
                                         link=link, intf=intf, build=build, xterms=xterms, cleanup=cleanup,
                                         ipBase=ipBase, inNamespace=inNamespace, autoSetMacs=autoSetMacs,
                                         autoStaticArp=autoStaticArp, autoPinCpus=autoPinCpus,
                                         listenPort=listenPort,
                                         waitConnected=waitConnected)

        self.scheduler = scheduler(time.time, time.sleep)
        if events_file:
            json_events = json.load(open(events_file))
            self.load_events(json_events)

    def load_events(self, json_events):

        event_type_to_f = {'editLink': self.editLink}
        for event in json_events:
            debug("processing event: time {time}, type {type}, params {params}\n".format(**event))
            event_type = event['type']
            self.scheduler.enter(event['time'], 1, event_type_to_f[event_type], kwargs=event['params'])

    # edit link event


    def editLink(self, **kwargs):
        """
        Command to edit the properties of a link between src and dst.
        :param kwargs: named arguments
            src: name of the source node.
            dst: name of the destination node.
            bw: bandwidth in Mbps.
            loss: packet loss ratio percentage.
            delay: delay in ms.
        """
        n1, n2 = self.get(kwargs['src'], kwargs['dst'])
        intf_pairs = n1.connectionsTo(n2)
        info('***editLink event at t={time}: {args}\n'.format(time=time.time(), args=kwargs))
        for intf_pair in intf_pairs:
            n1_intf, n2_intf = intf_pair
            n1_intf.config(**kwargs)
            n2_intf.config(**kwargs)




    def start(self):
        super(Minievents, self).start()
        CLI(self) if self.scheduler.empty() else self.scheduler.run()

if __name__ == '__main__':

    os.system("sudo ifconfig eth0 192.168.1.254 netmask 255.255.255.0 up")
    os.system("sudo ip route add 192.168.2.254 dev eth0")
    os.system("sudo sysctl net.ipv4.conf.all.forwarding=1")

    parser = argparse.ArgumentParser()
    parser.add_argument("--events",default="bw.json", help="json file with event descriptions")
    args = parser.parse_args()
    setLogLevel('info')
    net = Minievents( topo=Min( ),link=TCLink, events_file=args.events)
    intfName ='eth1'
    switch = net.switches[ 0 ]
    _intf = Intf( intfName, node=switch)

    net.start()
    CLI( net )

    net.stop()
    os.system("sudo mn -c")



