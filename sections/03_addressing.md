## 3. Dual-stack IPv4/IPv6 Addressing and Summarization

### 3.1 VLAN addresses

The address plan follows the VLANs and routing boundaries shown in [Section 2's topology diagram](02_layer2.md#21-physical-and-logical-topology). Private VLANs use subnets from `10.80.0.0/16`, while public servers use `203.0.113.0/28`. Every VLAN also receives a /64 from `2001:db8:6500::/48`.

IPv4 subnets allow for 25% device growth plus one SVI gateway: `ceil(1.25 x current devices) + 1` usable addresses. The table uses the population assumptions in Section 1.4 and shows each VLAN's current device count alongside its required capacity.

Both gateways reside on the local distribution-switch SVI. For IPv6, the SVI has global address `::1` within its listed prefix and link-local address `fe80::1`. Hosts learn the link-local address as their default router through Router Advertisements. Because that address is scoped to its VLAN, the same `fe80::1` can be used in every VLAN. [RFC 4861](https://www.rfc-editor.org/rfc/rfc4861.html#section-6.3.4)

| Site | VLAN / purpose | Hosts: current / required | IPv4 prefix | IPv4 gateway | IPv6 prefix | IPv6 default gateway | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 110 / Floor 1 users | 60 / 76 | 10.80.0.0/25 | 10.80.0.1 | 2001:db8:6500:1001::/64 | fe80::1 | 126 usable IPv4 addresses |
| A | 120 / Floor 2 users | 60 / 76 | 10.80.0.128/25 | 10.80.0.129 | 2001:db8:6500:1002::/64 | fe80::1 | 126 usable |
| A | 130 / Floor 3 users | 60 / 76 | 10.80.1.0/25 | 10.80.1.1 | 2001:db8:6500:1003::/64 | fe80::1 | 126 usable |
| A | 140 / Floor 4 users | 60 / 76 | 10.80.1.128/25 | 10.80.1.129 | 2001:db8:6500:1004::/64 | fe80::1 | 126 usable |
| A | 150 / Voice | 30 / 39 | 10.80.2.0/26 | 10.80.2.1 | 2001:db8:6500:1005::/64 | fe80::1 | 62 usable |
| A | 160 / Engineering | 40 / 51 | 10.80.2.64/26 | 10.80.2.65 | 2001:db8:6500:1006::/64 | fe80::1 | 62 usable |
| A | 170 / Guests | 80 / 101 | 10.80.3.0/25 | 10.80.3.1 | 2001:db8:6500:1007::/64 | fe80::1 | 126 usable |
| A | 180 / Management | 20 / 26 | 10.80.2.128/27 | 10.80.2.129 | 2001:db8:6500:1008::/64 | fe80::1 | 30 usable |
| B | 210 / Users | 90 / 114 | 10.80.17.0/25 | 10.80.17.1 | 2001:db8:6500:2001::/64 | fe80::1 | 126 usable |
| B | 220 / Robotics | 120 / 151 | 10.80.16.0/24 | 10.80.16.1 | 2001:db8:6500:2002::/64 | fe80::1 | 254 usable |
| B | 230 / Management | 20 / 26 | 10.80.17.128/27 | 10.80.17.129 | 2001:db8:6500:2003::/64 | fe80::1 | 30 usable |
| C | 310 / Internal servers | 40 / 51 | 10.80.32.0/26 | 10.80.32.1 | 2001:db8:6500:3001::/64 | fe80::1 | 62 usable |
| C | 320 / Public servers | 10 / 14 | 203.0.113.0/28 | 203.0.113.1 | 2001:db8:6500:3002::/64 | fe80::1 | 14 usable |
| C | 330 / Management | 20 / 26 | 10.80.32.64/27 | 10.80.32.65 | 2001:db8:6500:3003::/64 | fe80::1 | 30 usable |

### 3.2 Subnet-size calculations

For these VLANs, an IPv4 subnet with prefix length `p` provides `2^(32-p) - 2` usable addresses. Each allocation is the smallest subnet that meets the growth and gateway requirement, as illustrated below.

| Example | Required addresses | Selected subnet | Why the next smaller subnet fails |
| --- | --- | --- | --- |
| One A user floor | ceil(60 x 1.25) + 1 = 76 | /25: 2^7 - 2 = 126 | /26 gives 62 < 76 |
| A voice | ceil(30 x 1.25) + 1 = 39 | /26: 2^6 - 2 = 62 | /27 gives 30 < 39 |
| B robotics | ceil(120 x 1.25) + 1 = 151 | /24: 2^8 - 2 = 254 | /25 gives 126 < 151 |
| Any management VLAN | ceil(20 x 1.25) + 1 = 26 | /27: 2^5 - 2 = 30 | /28 gives 14 < 26 |
| C public servers | ceil(10 x 1.25) + 1 = 14 | /28: 2^4 - 2 = 14 | /29 gives 6 < 14 |

### 3.3 Routed links and loopbacks

Routed point-to-point links use IPv4 /30s and IPv6 /127s. Each link needs only two interface addresses and has no end hosts using SLAAC. The IPv6 /127 therefore provides exactly the required pair; Subnet-Router anycast is disabled on these interfaces as required by [RFC 6164](https://www.rfc-editor.org/rfc/rfc6164.html#section-6).

In the table below, the first named device uses the IPv6 address ending in `::2` and the second uses the address ending in `::3` within the listed prefix. Internal links draw from KAS's infrastructure blocks, while ISP transit links use assumed provider assignments outside those blocks.

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

Each routing device also receives an IPv4 /32 and an IPv6 /128 loopback. Its IPv4 loopback address serves as the router ID for both OSPFv2 and OSPFv3.

| Device | IPv4 loopback / OSPF router ID | IPv6 loopback |
| --- | --- | --- |
| RA | 10.80.241.1/32 | 2001:db8:6500:f100::1/128 |
| RB | 10.80.241.2/32 | 2001:db8:6500:f100::2/128 |
| RC | 10.80.241.3/32 | 2001:db8:6500:f100::3/128 |
| DS-A | 10.80.241.11/32 | 2001:db8:6500:f100::11/128 |
| DS-B | 10.80.241.12/32 | 2001:db8:6500:f100::12/128 |
| DS-C | 10.80.241.13/32 | 2001:db8:6500:f100::13/128 |

### 3.4 Site blocks, reserves, and summarization

Each site receives a private IPv4 /20 and an IPv6 /52, keeping its VLAN allocations together and leaving room for expansion.

| Site | Private IPv4 allocation | IPv6 allocation | Main contiguous IPv4 reserve |
| --- | --- | --- | --- |
| A | 10.80.0.0/20 | 2001:db8:6500:1000::/52 | 10.80.4.0 - 10.80.15.255 |
| B | 10.80.16.0/20 | 2001:db8:6500:2000::/52 | 10.80.18.0 - 10.80.31.255 |
| C | 10.80.32.0/20 | 2001:db8:6500:3000::/52 | 10.80.33.0 - 10.80.47.255 |

The listed IPv4 ranges and smaller unassigned gaps remain reserved for their respective sites. Each IPv6 /52 contains 4,096 /64s, with unused prefixes available for new VLANs. Separate reserves support future sites, routing infrastructure, and public services:

| Reserve | Use |
| --- | --- |
| 10.80.48.0 - 10.80.239.255 | Future sites, allocated in /20 blocks |
| 10.80.240.0/20 | Routing infrastructure: 10.80.240.0/24 for point-to-point links, 10.80.241.0/24 for loopbacks; the rest reserved |
| 2001:db8:6500:f000::/52 | Routing infrastructure: reserve one /64 around each assigned /127; 2001:db8:6500:f100::/64 holds loopbacks |
| Other /52 blocks in 2001:db8:6500::/48 | Future sites |
| 203.0.113.16/28 | NAT44 pool at RC; 203.0.113.17 is initially used |
| 203.0.113.32/27, 203.0.113.64/26, 203.0.113.128/25 | Future public services |

These allocations support future aggregation, but the current routing design uses them differently:

- **Within OSPF:** all internal interfaces belong to Area 0, so individual VLAN, internal-link, and loopback prefixes remain visible. C also advertises its public-server subnet, `203.0.113.0/28`. The site /20s and /52s are allocation blocks, not advertised site summaries.
- **If separate site areas are introduced:** area border routers can summarize the site VLANs into the listed /20s and /52s. Infrastructure prefixes and C's public IPv4 subnet remain separate because they fall outside those site blocks. OSPF inter-area summarization takes place at area boundaries. [RFC 2328](https://www.rfc-editor.org/rfc/rfc2328.html#section-3.5)
- **At the Internet edge:** RC advertises only `203.0.113.0/24` and `2001:db8:6500::/48` to the providers. Aggregate discard routes cover unused destinations, while more-specific routes deliver traffic to active networks. Private IPv4 and provider transit prefixes are excluded from exports.

### 3.5 NAT44 and native IPv6

Private IPv4 traffic needs a public source address to reach the Internet. For permitted traffic using either ISP, RC performs NAT44 with port translation, replacing the source address with `203.0.113.17` and assigning a source port. Its translation table maps replies back to the internal host. The public address is assigned to an additional RC loopback as `203.0.113.17/32` and advertised internally; the rest of the NAT pool is reserved for expansion.

Inter-site IPv4 traffic retains its original addresses, and VLAN 320 uses its public IPv4 addresses directly. IPv6 also preserves the source address and transport port through RC because every VLAN has a prefix from KAS's provider-advertised /48. No NAT66 is used. In both address families, ACLs determine which traffic is permitted.
