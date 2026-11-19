# KAS topology

Open [topo.drawio](topo.drawio) to edit the diagram, or [topo.png](topo.png) to view it.

| Component | Role |
| --- | --- |
| Site A | Headquarters: four floors with user, voice, engineering, guest, and management VLANs. |
| Site B | Robotics lab: separate user, robotics, and management VLANs. ACLs restrict traffic between robotics and users. |
| Site C | Data center and Internet edge: separate internal-server, public-server, and management VLANs. |
| RA / RB / RC | Route traffic between sites. RC also connects to both Internet providers. |
| DS-A / DS-B / DS-C | Layer-3 distribution switches. Their SVIs provide VLAN default gateways and route between VLANs. They also enforce ACLs and act as preferred STP roots. |
| Access switches | Connect devices on each floor or in each group to the local distribution switch. Boxes represent switch groups, not final equipment counts. |
| ISP-1 / ISP-2 | Preferred and backup Internet providers, respectively, using IPv4 and IPv6 eBGP with RC. KAS does not carry transit traffic between them. |

Solid lines are routed links; dashed lines are 802.1Q trunks carrying the required VLANs. WAN labels show capacity and one-way delay.

VLANs end at the local distribution switch and do not cross the WAN. Each access switch has one logical uplink, so no uplinks are normally blocked by STP. WAN routing uses OSPFv2 for IPv4 and OSPFv3 for IPv6, both in Area 0.
