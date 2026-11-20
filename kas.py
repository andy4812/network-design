#!/usr/bin/env python3
from ipmininet.iptopo import IPTopo
from ipmininet.ipnet import IPNet
from ipmininet.cli import IPCLI


class KASTopology(IPTopo):
    def build(self, *args, **kwargs):
        aRouter = self.addRouter('aRouter')
        bRouter = self.addRouter('bRouter')
        cRouter = self.addRouter('cRouter')
        aHost = self.addHost('aHost')
        bRobot = self.addHost('bRobot')
        cServer = self.addHost('cServer')

        # WAN links: matching Section 3 and Section 4.
        ac = self.addLink(aRouter, cRouter, igp_metric=10)
        ac[aRouter].addParams(ip=('10.80.240.1/30', '2001:db8:6500:f001::2/127'))
        ac[cRouter].addParams(ip=('10.80.240.2/30', '2001:db8:6500:f001::3/127'))

        ab = self.addLink(aRouter, bRouter, igp_metric=50)
        ab[aRouter].addParams(ip=('10.80.240.5/30', '2001:db8:6500:f002::2/127'))
        ab[bRouter].addParams(ip=('10.80.240.6/30', '2001:db8:6500:f002::3/127'))

        bc = self.addLink(bRouter, cRouter, igp_metric=50)
        bc[bRouter].addParams(ip=('10.80.240.9/30', '2001:db8:6500:f003::2/127'))
        bc[cRouter].addParams(ip=('10.80.240.10/30', '2001:db8:6500:f003::3/127'))

        # Representative LANs: distribution switches are collapsed into routers.
        a = self.addLink(aRouter, aHost)
        a[aRouter].addParams(ip=('10.80.2.65/26', '2001:db8:6500:1006::1/64'))
        a[aHost].addParams(ip=('10.80.2.74/26', '2001:db8:6500:1006::10/64'))

        b = self.addLink(bRouter, bRobot)
        b[bRouter].addParams(ip=('10.80.16.1/24', '2001:db8:6500:2002::1/64'))
        b[bRobot].addParams(ip=('10.80.16.10/24', '2001:db8:6500:2002::10/64'))

        c = self.addLink(cRouter, cServer)
        c[cRouter].addParams(ip=('10.80.32.1/26', '2001:db8:6500:3001::1/64'))
        c[cServer].addParams(ip=('10.80.32.10/26', '2001:db8:6500:3001::10/64'))
        super().build(*args, **kwargs)


if __name__ == '__main__':
    net = IPNet(topo=KASTopology(), allocate_IPs=False)
    try:
        net.start()
        for host, gateway4, gateway6 in [
            ('aHost', '10.80.2.65', '2001:db8:6500:1006::1'),
            ('bRobot', '10.80.16.1', '2001:db8:6500:2002::1'),
            ('cServer', '10.80.32.1', '2001:db8:6500:3001::1'),
        ]:
            net[host].cmd('ip route replace default via ' + gateway4)
            net[host].cmd('ip -6 route replace default via ' + gateway6)
        IPCLI(net)
    finally:
        net.stop()
