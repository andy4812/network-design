## 3. Dual-stack IPv4/IPv6 Addressing and Summarization

### 3.1 VLAN addresses

Assume 60 users per headquarters floor, 80 concurrent guests, and 40 internal plus 10 public-facing servers at C. Other device counts follow the project requirements.

Required IPv4 capacity is `ceil(1.25 x current devices) + 1`, including the SVI gateway. The host column shows current devices / required usable addresses. Every VLAN receives an IPv6 /64.

Each gateway resides on the VLAN's local distribution-switch SVI. The IPv6 SVI uses `::1` within its listed prefix and link-local address `fe80::1`. Hosts learn `fe80::1` as their default router through Router Advertisements; it is scoped to the local VLAN. [RFC 4861](https://www.rfc-editor.org/rfc/rfc4861.html#section-6.3.4)

| Site | VLAN / purpose | Hosts: current / required | IPv4 prefix | IPv4 gateway | IPv6 prefix | IPv6 default gateway | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 110 / Floor 1 users | 60 / 76 | 10.80.0.0/25 | 10.80.0.1 | 2001:db8:6500:1001::/64 | fe80::1 | 126 usable IPv4 addresses |
| A | 120 / Floor 2 users | 60 / 76 | 10.80.0.128/25 | 10.80.0.129 | 2001:db8:6500:1002::/64 | fe80::1 | 126 usable |
| A | 130 / Floor 3 users | 60 / 76 | 10.80.1.0/25 | 10.80.1.1 | 2001:db8:6500:1003::/64 | fe80::1 | 126 usable |
| A | 140 / Floor 4 users | 60 / 76 | 10.80.1.128/25 | 10.80.1.129 | 2001:db8:6500:1004::/64 | fe80::1 | 126 usable |
| A | 150 / Voice | 30 / 39 | 10.80.2.0/26 | 10.80.2.1 | 2001:db8:6500:1005::/64 | fe80::1 | 62 usable |
| A | 160 / Engineering | 40 / 51 | 10.80.2.64/26 | 10.80.2.65 | 2001:db8:6500:1006::/64 | fe80::1 | 62 usable |
| A | 170 / Guests | 80 / 101 | 10.80.3.0/25 | 10.80.3.1 | 2001:db8:6500:1007::/64 | fe80::1 | 126 usable; assumed guest population |
| A | 180 / Management | 20 / 26 | 10.80.2.128/27 | 10.80.2.129 | 2001:db8:6500:1008::/64 | fe80::1 | 30 usable |
| B | 210 / Users | 90 / 114 | 10.80.17.0/25 | 10.80.17.1 | 2001:db8:6500:2001::/64 | fe80::1 | 126 usable |
| B | 220 / Robotics | 120 / 151 | 10.80.16.0/24 | 10.80.16.1 | 2001:db8:6500:2002::/64 | fe80::1 | 254 usable |
| B | 230 / Management | 20 / 26 | 10.80.17.128/27 | 10.80.17.129 | 2001:db8:6500:2003::/64 | fe80::1 | 30 usable |
| C | 310 / Internal servers | 40 / 51 | 10.80.32.0/26 | 10.80.32.1 | 2001:db8:6500:3001::/64 | fe80::1 | 62 usable |
| C | 320 / Public servers | 10 / 14 | 203.0.113.0/28 | 203.0.113.1 | 2001:db8:6500:3002::/64 | fe80::1 | 14 usable; directly routed public IPv4 |
| C | 330 / Management | 20 / 26 | 10.80.32.64/27 | 10.80.32.65 | 2001:db8:6500:3003::/64 | fe80::1 | 30 usable |

### 3.2 Subnet-size calculations

A subnet with prefix length `p` provides `2^(32-p) - 2` usable IPv4 addresses. Choose the smallest subnet that fits the required capacity.

| Example | Required addresses | Selected subnet | Why the next smaller subnet fails |
| --- | --- | --- | --- |
| One A user floor | ceil(60 x 1.25) + 1 = 76 | /25: 2^7 - 2 = 126 | /26 gives 62 < 76 |
| A voice | ceil(30 x 1.25) + 1 = 39 | /26: 2^6 - 2 = 62 | /27 gives 30 < 39 |
| B robotics | ceil(120 x 1.25) + 1 = 151 | /24: 2^8 - 2 = 254 | /25 gives 126 < 151 |
| Any management VLAN | ceil(20 x 1.25) + 1 = 26 | /27: 2^5 - 2 = 30 | /28 gives 14 < 26 |
| C public servers | ceil(10 x 1.25) + 1 = 14 | /28: 2^4 - 2 = 14 | /29 gives 6 < 14 |

### 3.3 Routed links and loopbacks

IPv4 point-to-point links use /30s. IPv6 uses /127s because each link has exactly two router interfaces and no end hosts or SLAAC. This limits the link to two addresses; Subnet-Router anycast is disabled on these interfaces as required by [RFC 6164](https://www.rfc-editor.org/rfc/rfc6164.html#section-6).

For each IPv6 link below, the first named device uses the address ending in `::2`, and the second uses `::3`, within the listed prefix. ISP transit prefixes are assumed provider assignments outside KAS's blocks.

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

| Device | IPv4 loopback / OSPF router ID | IPv6 loopback |
| --- | --- | --- |
| RA | 10.80.241.1/32 | 2001:db8:6500:f100::1/128 |
| RB | 10.80.241.2/32 | 2001:db8:6500:f100::2/128 |
| RC | 10.80.241.3/32 | 2001:db8:6500:f100::3/128 |
| DS-A | 10.80.241.11/32 | 2001:db8:6500:f100::11/128 |
| DS-B | 10.80.241.12/32 | 2001:db8:6500:f100::12/128 |
| DS-C | 10.80.241.13/32 | 2001:db8:6500:f100::13/128 |

### 3.4 Site blocks, reserves, and summarization

| Site | Private IPv4 allocation | IPv6 allocation | Main contiguous IPv4 reserve |
| --- | --- | --- | --- |
| A | 10.80.0.0/20 | 2001:db8:6500:1000::/52 | 10.80.4.0 - 10.80.15.255 |
| B | 10.80.16.0/20 | 2001:db8:6500:2000::/52 | 10.80.18.0 - 10.80.31.255 |
| C | 10.80.32.0/20 | 2001:db8:6500:3000::/52 | 10.80.33.0 - 10.80.47.255 |

Unassigned gaps within these blocks remain reserved for their site. Each IPv6 /52 contains 4,096 /64s; unused /64s remain available for new VLANs.

| Reserve | Use |
| --- | --- |
| 10.80.48.0 - 10.80.239.255 | Future sites, allocated in /20 blocks |
| 10.80.240.0/20 | Routing infrastructure: 10.80.240.0/24 for point-to-point links, 10.80.241.0/24 for loopbacks; the rest reserved |
| 2001:db8:6500:f000::/52 | Routing infrastructure: reserve one /64 around each assigned /127; 2001:db8:6500:f100::/64 holds loopbacks |
| Other /52 blocks in 2001:db8:6500::/48 | Future sites |
| 203.0.113.16/28 | NAT44 pool at RC; 203.0.113.17 is initially used |
| 203.0.113.32/27, 203.0.113.64/26, 203.0.113.128/25 | Future public services |

The site /20 and /52 blocks are allocation aggregates. With all internal interfaces in Area 0, no site advertises an inter-area summary: individual VLAN, internal-link, and loopback prefixes remain visible in OSPFv2/OSPFv3. C also advertises its public-server subnet, `203.0.113.0/28`. If sites later receive separate OSPF areas, their ABRs can advertise the listed site aggregates; routing-infrastructure prefixes and C's public subnet remain separate. OSPF area aggregation occurs at area boundaries. [RFC 2328](https://www.rfc-editor.org/rfc/rfc2328.html#section-3.5)

At RC, BGP aggregation is separate: advertise `203.0.113.0/24` and `2001:db8:6500::/48` to the providers. Install discard routes for these aggregates, while more-specific routes deliver traffic to active networks. Do not export private IPv4 or provider transit prefixes.

### 3.5 NAT44 and native IPv6

RC performs NAT44 with port translation for permitted private-IPv4 traffic leaving either Internet circuit. It translates the source address and port to `203.0.113.17` and an allocated port, then uses the translation table to deliver replies. Assign `203.0.113.17/32` to an additional RC loopback and advertise that host route internally. The remainder of the NAT pool is reserved for expansion. Inter-site traffic is not translated, and VLAN 320 uses its public IPv4 addresses directly.

IPv6 traffic uses the assigned global addresses end to end. RC forwards it through the selected provider without changing the source address or transport port. NAT66 is unnecessary because each VLAN has globally routable addresses; ACLs control access in both protocols.
