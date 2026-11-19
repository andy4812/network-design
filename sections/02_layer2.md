## 2. Physical, Layer-2, and Segmentation Design

### 2.1 Physical and logical topology

The [topology diagram](../diagrams/topo.drawio) ([preview](../diagrams/topo.png)) shows the three sites, site routers, distribution and access switches, WAN circuits, Internet circuits, and Layer-2 boundaries.

At each site, access switches connect to one Layer-3 distribution switch: DS-A, DS-B, or DS-C. The distribution switch connects to its site router through a routed link. RA, RB, and RC form the WAN triangle. RC also provides the Internet edge.

| Circuit | Capacity | One-way delay / role |
| --- | --- | --- |
| A-C | 10 Gb/s | 5 ms; primary high-capacity path |
| A-B | 2 Gb/s | 12 ms |
| B-C | 2 Gb/s | 10 ms |
| RC to ISP-1, AS64501 | 10 Gb/s | Preferred Internet provider |
| RC to ISP-2, AS64502 | 5 Gb/s | Backup Internet provider |

The diagram's access switches represent groups, not final equipment counts. Site A has an access group on each of its four floors. Sites B and C group access by device role. Each physical access switch has one logical uplink to its local distribution switch. No access switch connects directly to another site.

### 2.2 VLAN plan and default gateways

Every production VLAN has its own IPv4 subnet and IPv6 /64. Its default gateways reside on the corresponding switched virtual interface (SVI) at the local distribution switch. Subnets and gateway addresses are listed in [Section 3](03_addressing.md).

| Site | VLAN | Purpose | Gateway location | Normal traffic path |
| --- | --- | --- | --- | --- |
| A | 110 | Floor 1 ordinary users | DS-A, SVI 110 | Same-VLAN traffic stays local; applications and Internet traffic cross the WAN to C. |
| A | 120 | Floor 2 ordinary users | DS-A, SVI 120 | Same as VLAN 110. |
| A | 130 | Floor 3 ordinary users | DS-A, SVI 130 | Same as VLAN 110. |
| A | 140 | Floor 4 ordinary users | DS-A, SVI 140 | Same as VLAN 110. |
| A | 150 | IP phones | DS-A, SVI 150 | Phone-to-phone media stays local when both endpoints are in this VLAN; call control crosses the WAN to C. |
| A | 160 | Engineering lab devices | DS-A, SVI 160 | Local lab traffic; repository access to C and approved robot-control traffic to B cross the WAN. |
| A | 170 | Guest wireless clients | DS-A, SVI 170 | Internet traffic crosses the WAN to the edge at C; no access to KAS application networks. |
| A | 180 | Infrastructure and management | DS-A, SVI 180 | Local device administration; central monitoring and approved remote administration cross the WAN. |
| B | 210 | Ordinary users | DS-B, SVI 210 | Same-VLAN traffic stays local; applications and Internet traffic cross the WAN to C. |
| B | 220 | Robots and embedded test systems | DS-B, SVI 220 | Robot/test exchanges stay local where possible; telemetry and repository access cross the WAN to C. |
| B | 230 | Infrastructure and management | DS-B, SVI 230 | Local device administration; central monitoring and approved remote administration cross the WAN. |
| C | 310 | Internal production services: shared DNS, software repository, applications, call control | DS-C, SVI 310 | Server-to-server traffic stays local; requests and replies for A/B traverse the WAN. |
| C | 320 | Public-facing production services | DS-C, SVI 320 | Public service traffic uses RC and an ISP; approved management traffic stays local or arrives from A/B. |
| C | 330 | Infrastructure, management, and central monitoring | DS-C, SVI 330 | Local administration at C; monitoring and approved administration of A/B traverse the WAN. |

Guest wireless and IP phones are deployed only at A in this design. Call control is assumed to run on an internal server at C. VLANs 310 and 320 divide C's existing production-server population by exposure; they do not add another site or router. Floor-user VLANs remain floor-specific, while voice, engineering, guest, and management VLANs may span the required floors within Site A.

### 2.3 Communication between VLAN classes

Inter-VLAN access is denied unless permitted below. The same policy applies to IPv4 and IPv6, including traffic arriving from another site. Access control lists (ACLs) on the distribution-switch SVIs enforce these restrictions; a separate VLAN alone does not prevent routed access. Apply rules in the appropriate ingress and egress directions so that traffic arriving through the routed site-router uplink cannot bypass the destination VLAN's policy.

| VLAN class | Permitted communication | Restrictions |
| --- | --- | --- |
| Ordinary users: 110, 120, 130, 140, 210 | Designated DNS and application services in 310; published services in 320; Internet web access through RC. | No direct access to other user VLANs, engineering, voice, guests, robotics, or management VLANs. |
| Voice: 150 | Call-control, DNS, and time services on designated hosts in 310; local phone media within 150. | No general access to user, engineering, guest, robotics, public-server, or management VLANs; no direct Internet access. |
| Engineering: 160 | Internal DNS/applications/repository in 310, published services in 320, and Internet web access. Named engineering control workstations may access designated robots in 220 on approved control/test ports. | Other engineering devices cannot access robotics. No general access to ordinary users, voice, guests, or management VLANs. |
| Guests: 170 | Internet web access and external DNS, plus local address-configuration and neighbor-discovery traffic. | Deny all KAS destination prefixes, including public IPv4 and global IPv6 prefixes. Enable wireless client isolation to prevent guest-to-guest access. |
| Robotics: 220 | Designated telemetry collectors, repository, DNS, and time services in 310; logs to the monitoring host in 330. | No general access to user, engineering, guest, voice, or public-server VLANs, and no direct Internet access. Permit replies for approved engineering control and management flows. |
| Internal servers: 310 | Provide the listed services to authorized clients; send logs to 330; use approved external update/time services. | No unrestricted server-initiated access to client, robotics, public-server, or management networks. |
| Public servers: 320 | Serve published HTTPS services to Internet and authorized internal clients; send logs to a designated collector in 330; use approved external DNS/update/time services. | Deny other access to internal KAS VLANs. Administrative access is permitted only from named management hosts. |
| Management: 180, 230, 330 | Named administrator hosts may manage designated infrastructure and servers using SSH/HTTPS. The central monitor in 330 may poll designated devices using SNMPv3/ICMP; managed devices may send logs to it. Permit internal DNS/time and approved updates. | Membership in a management VLAN does not grant unrestricted access. Scope rules to specific source hosts, destination devices, and management services. No routine access to guests. |

These rows describe permitted application flows. Ordinary switch ACLs are stateless: explicit reverse-direction entries are needed for replies, including UDP. Such entries must be limited by host and service; they do not provide stateful session validation. Permit the necessary ARP, IPv6 Neighbor Discovery/router advertisements, address configuration, and ICMP/ICMPv6 error messages so that segmentation does not break connectivity or path-MTU discovery.

Devices within the same VLAN can communicate without passing through an SVI ACL. In particular, VLAN 220 isolates robotics from other classes but does not isolate individual robots from each other. Guest client isolation is therefore applied at the wireless access layer rather than relying on the gateway ACL.

### 2.4 Trunks, access ports, and routing boundaries

Access-switch uplinks to DS-A, DS-B, and DS-C are IEEE 802.1Q trunks. Tagged frames identify the VLAN, and each trunk permits only the VLANs needed by its attached devices and switch management.

| Access group | VLANs permitted on its distribution uplink |
| --- | --- |
| A, floor 1 / 2 / 3 / 4 | Its floor-user VLAN: 110 / 120 / 130 / 140, respectively; management 180; voice 150, engineering 160, and guest 170 only where needed. |
| B, user access | 210 and 230 |
| B, robotics access | 220 and 230 |
| B, management access | 230 |
| C, server access | 310, 320, and 330 |
| C, management access | 330 |

Ordinary endpoint ports are untagged access ports in one VLAN. A phone port may carry tagged voice VLAN 150 and untagged data in its floor-user VLAN. A guest AP uplink carries guest VLAN 170 and management VLAN 180, with the guest SSID mapped to 170. Management VLANs on access-switch uplinks serve switch/AP management; ordinary devices are not placed in those VLANs. All production VLANs are tagged on switch-to-switch trunks; VLAN 1 is not used for production, and unused ports are disabled.

Traffic within one VLAN is switched locally. Traffic between two VLANs at the same site is routed by the distribution switch's SVIs and checked against its ACLs. Remote traffic then follows the routed uplink to RA, RB, or RC and crosses the WAN. For example, an engineering workstation reaches the repository through `VLAN 160 -> DS-A -> RA -> WAN -> RC -> DS-C -> VLAN 310`.

The distribution-switch-to-router links and all WAN links are Layer-3 links, not VLAN trunks. Every VLAN is a separate broadcast domain that ends at its site's distribution switch. No Layer-2 domain is stretched between sites: Ethernet broadcasts and ARP remain local, and IPv6 link-local discovery remains on its local link. WAN redundancy is provided by OSPFv2 and OSPFv3 in Area 0.

### 2.5 Spanning tree and failure tradeoff

DS-A, DS-B, and DS-C are the preferred STP roots for their respective sites. With one logical uplink per access switch and no switch-to-switch access links, the intended Layer-2 topology contains no loops. Access-switch uplinks are forwarding root ports; distribution downlinks are forwarding designated ports. No uplink is normally blocked. STP remains enabled to protect against accidental redundant connections; endpoint ports use edge-port behavior and BPDU Guard, while switch uplinks do not.

This design favors simple operation and predictable forwarding over local redundancy. An access-uplink failure disconnects that access switch. A distribution-switch failure removes that site's VLAN gateways; failure of DS-B or its VLAN 220 SVI therefore interrupts routed robotics access, with no backup gateway. STP cannot restore these missing paths. The WAN triangle provides alternate routed paths for WAN-link failures, but it does not protect against a local distribution-switch or gateway failure.

