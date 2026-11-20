# KAS Network Design

Shared parameters for the report, [topology](diagrams/topo.drawio), and lab. Unassigned values are listed at the end.

## Sites and address blocks

| Site | Role | Router | Distribution switch | Private IPv4 block | IPv6 block |
| --- | --- | --- | --- | --- | --- |
| A | Headquarters | RA | DS-A | 10.80.0.0/20 | 2001:db8:6500:1000::/52 |
| B | Robotics lab | RB | DS-B | 10.80.16.0/20 | 2001:db8:6500:2000::/52 |
| C | Data center / Internet edge | RC | DS-C | 10.80.32.0/20 | 2001:db8:6500:3000::/52 |

| Parameter | Value |
| --- | --- |
| KAS ASN | AS65050 |
| Private IPv4 space | 10.80.0.0/16 |
| Public IPv4 space | 203.0.113.0/24 |
| Global IPv6 space | 2001:db8:6500::/48 |
| Routing infrastructure | 10.80.240.0/20; 2001:db8:6500:f000::/52 |
| Internal point-to-point IPv4 pool | 10.80.240.0/24 |
| Loopback pools | 10.80.241.0/24; 2001:db8:6500:f100::/64 |
| Public-server subnet | 203.0.113.0/28, VLAN 320 |
| NAT44 pool | 203.0.113.16/28; initially use 203.0.113.17 |
| Future-site IPv4 reserve | 10.80.48.0 - 10.80.239.255, allocated in /20 blocks |
| Future-site IPv6 reserve | Unassigned /52 blocks within the KAS /48 |
| Future public subnets | 203.0.113.32/27; 203.0.113.64/26; 203.0.113.128/25 |

Unused space within a site's blocks remains reserved for that site. Detailed reserves and sizing calculations are in [Section 3](sections/03_addressing.md).

## VLANs and gateways

Gateways are SVIs on the site's distribution switch. Every IPv6 SVI uses its listed prefix plus `::1`, with `fe80::1` as the link-local default router on that VLAN. All production VLANs are dual-stack.

| Site | VLAN | Purpose | Current devices | IPv4 prefix | IPv4 gateway | IPv6 prefix |
| --- | --- | --- | --- | --- | --- | --- |
| A | 110 | Floor 1 users | 60 | 10.80.0.0/25 | 10.80.0.1 | 2001:db8:6500:1001::/64 |
| A | 120 | Floor 2 users | 60 | 10.80.0.128/25 | 10.80.0.129 | 2001:db8:6500:1002::/64 |
| A | 130 | Floor 3 users | 60 | 10.80.1.0/25 | 10.80.1.1 | 2001:db8:6500:1003::/64 |
| A | 140 | Floor 4 users | 60 | 10.80.1.128/25 | 10.80.1.129 | 2001:db8:6500:1004::/64 |
| A | 150 | Voice | 30 | 10.80.2.0/26 | 10.80.2.1 | 2001:db8:6500:1005::/64 |
| A | 160 | Engineering | 40 | 10.80.2.64/26 | 10.80.2.65 | 2001:db8:6500:1006::/64 |
| A | 170 | Guest wireless | 80 | 10.80.3.0/25 | 10.80.3.1 | 2001:db8:6500:1007::/64 |
| A | 180 | Infrastructure / management | 20 | 10.80.2.128/27 | 10.80.2.129 | 2001:db8:6500:1008::/64 |
| B | 210 | Users | 90 | 10.80.17.0/25 | 10.80.17.1 | 2001:db8:6500:2001::/64 |
| B | 220 | Robotics / embedded systems | 120 | 10.80.16.0/24 | 10.80.16.1 | 2001:db8:6500:2002::/64 |
| B | 230 | Infrastructure / management | 20 | 10.80.17.128/27 | 10.80.17.129 | 2001:db8:6500:2003::/64 |
| C | 310 | Internal servers | 40 | 10.80.32.0/26 | 10.80.32.1 | 2001:db8:6500:3001::/64 |
| C | 320 | Public servers | 10 | 203.0.113.0/28 | 203.0.113.1 | 2001:db8:6500:3002::/64 |
| C | 330 | Infrastructure / management | 20 | 10.80.32.64/27 | 10.80.32.65 | 2001:db8:6500:3003::/64 |

- Population assumptions: 60 users per A floor; 80 concurrent guests; C's 50 servers split into 40 internal and 10 public.
- Minimum IPv4 capacity: `ceil(1.25 x current devices) + 1` usable addresses, including the gateway.
- Guest wireless and phones are deployed only at A. Internal DNS, repository, applications, and call control use VLAN 310; central monitoring uses VLAN 330.

## Layer-2 parameters

| Parameter | Value |
| --- | --- |
| Access-switch uplinks | One logical 802.1Q uplink per switch to its local distribution switch |
| Distribution-to-router links | Routed links, not trunks |
| VLAN scope | Local to one site; no VLAN stretched over the WAN |
| Preferred STP roots | DS-A, DS-B, DS-C for their respective sites |
| Normal STP state | All intended uplinks forwarding; none blocked |
| Endpoint ports | Access ports with edge-port behavior and BPDU Guard; unused ports disabled |
| Trunk tagging | Production VLANs tagged on switch-to-switch trunks; VLAN 1 unused for production |
| Gateway redundancy | None; the VRRP upgrade in Section 8 is proposed only |
| Inter-VLAN policy | Default deny, with the IPv4/IPv6 exceptions in [Section 2](sections/02_layer2.md#23-communication-between-vlan-classes) |

| Access group | Allowed uplink VLANs |
| --- | --- |
| A floor 1 / 2 / 3 / 4 | Its user VLAN 110 / 120 / 130 / 140, respectively; 180; add 150, 160, 170 only where needed |
| B users | 210, 230 |
| B robotics | 220, 230 |
| B management | 230 |
| C servers | 310, 320, 330 |
| C management | 330 |

Phone ports carry tagged voice VLAN 150 and untagged floor-user traffic. Guest AP uplinks carry VLANs 170 and 180; wireless client isolation is enabled. Access-switch boxes in the diagram represent groups, not final device counts.

## Circuits and interface addresses

| WAN circuit | Capacity | One-way propagation delay |
| --- | --- | --- |
| RA-RC / A-C | 10 Gb/s | 5 ms |
| RA-RB / A-B | 2 Gb/s | 12 ms |
| RB-RC / B-C | 2 Gb/s | 10 ms |

| Internet circuit | Provider ASN | Capacity | Role |
| --- | --- | --- | --- |
| RC to ISP-1 | AS64501 | 10 Gb/s | Preferred |
| RC to ISP-2 | AS64502 | 5 Gb/s | Backup |

IPv4 routed links use /30s; IPv6 routed links use /127s with Subnet-Router anycast disabled. For each IPv6 prefix below, the first device uses `::2` and the second uses `::3`. Reserve the enclosing /64 for each internal IPv6 link. ISP transit assignments are design assumptions.

| Devices, first / second | IPv4 prefix | IPv4 addresses, first / second | IPv6 prefix |
| --- | --- | --- | --- |
| RA / RC | 10.80.240.0/30 | 10.80.240.1 / 10.80.240.2 | 2001:db8:6500:f001::2/127 |
| RA / RB | 10.80.240.4/30 | 10.80.240.5 / 10.80.240.6 | 2001:db8:6500:f002::2/127 |
| RB / RC | 10.80.240.8/30 | 10.80.240.9 / 10.80.240.10 | 2001:db8:6500:f003::2/127 |
| DS-A / RA | 10.80.240.12/30 | 10.80.240.13 / 10.80.240.14 | 2001:db8:6500:f011::2/127 |
| DS-B / RB | 10.80.240.16/30 | 10.80.240.17 / 10.80.240.18 | 2001:db8:6500:f012::2/127 |
| DS-C / RC | 10.80.240.20/30 | 10.80.240.21 / 10.80.240.22 | 2001:db8:6500:f013::2/127 |
| ISP-1 / RC | 198.51.100.0/30 | 198.51.100.1 / 198.51.100.2 | 2001:db8:1::2/127 |
| ISP-2 / RC | 198.51.100.4/30 | 198.51.100.5 / 198.51.100.6 | 2001:db8:2::2/127 |

## Loopbacks

Use each device's IPv4 loopback address as its OSPFv2/OSPFv3 router ID.

| Device | IPv4 loopback | IPv6 loopback |
| --- | --- | --- |
| RA | 10.80.241.1/32 | 2001:db8:6500:f100::1/128 |
| RB | 10.80.241.2/32 | 2001:db8:6500:f100::2/128 |
| RC | 10.80.241.3/32 | 2001:db8:6500:f100::3/128 |
| DS-A | 10.80.241.11/32 | 2001:db8:6500:f100::11/128 |
| DS-B | 10.80.241.12/32 | 2001:db8:6500:f100::12/128 |
| DS-C | 10.80.241.13/32 | 2001:db8:6500:f100::13/128 |

RC also has `203.0.113.17/32` on an additional loopback for NAT44. Advertise that host route internally; it is not RC's router ID.

## Routing and Internet edge

| Parameter | Value |
| --- | --- |
| Internal IPv4 routing | OSPFv2, Area 0 |
| Internal IPv6 routing | OSPFv3, Area 0 |
| Site summaries | /20 and /52 blocks are allocation aggregates; no inter-area summarization in the current single-area design |
| Internal advertisements | Individual VLAN, internal-link, and loopback prefixes, including C's public-server /28 |
| Normal A-C path | Direct RA-RC, required by the Section 6 trace|
| A-C failure path | RA-RB-RC and reverse |
| External routing | IPv4 and IPv6 eBGP at RC with both providers |
| KAS Internet advertisements | 203.0.113.0/24; 2001:db8:6500::/48 |
| Aggregate handling at RC | Discard routes for the public /24 and IPv6 /48; more-specific routes for active networks |
| Export restrictions | KAS public aggregates only; no private IPv4, provider transit prefixes, or ISP-to-ISP transit |
| NAT44 | Port translation at RC for permitted private-IPv4 Internet traffic through either ISP; public address 203.0.113.17 |
| NAT exemptions | Inter-site traffic and directly addressed public servers |
| NAT66 | None |

## Shared endpoints and analysis assumptions

| Endpoint | VLAN | IPv4 | IPv6 |
| --- | --- | --- | --- |
| A engineering workstation | 160 | 10.80.2.74/26 | 2001:db8:6500:1006::10/64 |
| C software repository | 310 | 10.80.32.10/26 | 2001:db8:6500:3001::10/64 |

| Section 6 example parameter | Value |
| --- | --- |
| HTTPS connection | TCP; client port 51514, repository port 443 |
| Initial TTL / Hop Limit | 64 |
| File size | 10 MB = 10,000,000 bytes |
| RTT | 12 ms, supplied for the transport calculation |
| Illustrative IPv4 packet / TCP payload | 1,500 / 1,460 bytes with minimum headers; not a measured production MTU/MSS |
| Capacity used for window calculation | 10 Gb/s, assuming no slower link or endpoint bottleneck |
| Other trace assumptions | Ethernet links; no fragmentation or QoS remarking |

Transport choices: TCP for downloads; UDP for periodic telemetry and supervisory control; UDP with TCP fallback for DNS; QUIC/UDP for HTTP/3. Details are in [Section 6](sections/06_transport.md).

## Pending parameters

| Area | Not yet assigned or verified |
| --- | --- |
| Device configuration | Access-switch quantities/port counts, local link capacities, STP variant/priorities, and production MTU |
| Service configuration | DNS, call-control, monitoring, administrator, and robot-controller host assignments; application-specific ACL ports |

Failure expectations and the proposed gateway-redundancy upgrade are in [Section 8](sections/08_failure_analysis.md).
