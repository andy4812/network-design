## 4. Internal Routing and Forwarding

### 4.1 OSPF design and link costs

KAS uses OSPFv2 for internal IPv4 routing and OSPFv3 for internal IPv6 routing. All six routing devices—the site routers RA, RB, and RC and the distribution switches DS-A, DS-B, and DS-C—belong to Area 0. This single-area design keeps configuration and troubleshooting simple at the network's current size. Figure 4.1 shows the adjacencies and link costs.

Adjacencies form over the three WAN links and each site's distribution-to-router link. Through these adjacencies, the distribution switches advertise their connected VLAN prefixes, and all six devices advertise their loopbacks. VLAN SVIs and loopbacks remain passive: their prefixes are advertised, but they do not form adjacencies. Both OSPF versions use the same link costs so IPv4 and IPv6 select the same paths.

Interface costs use a **100 Gb/s** reference bandwidth:

$$
\text{Cost} = \frac{\text{Reference bandwidth}}{\text{Link bandwidth}}
$$

| Routed link | Bandwidth | Calculation | OSPF cost (each direction) |
| --- | ---: | --- | ---: |
| RA–RC | 10 Gb/s | 100/10 | 10 |
| RA–RB | 2 Gb/s | 100/2 | 50 |
| RB–RC | 2 Gb/s | 100/2 | 50 |
| DS-A–RA | 10 Gb/s (assumed) | 100/10 | 10 |
| DS-B–RB | 10 Gb/s (assumed) | 100/10 | 10 |
| DS-C–RC | 10 Gb/s (assumed) | 100/10 | 10 |

The WAN capacities come from the project requirements; the local distribution-to-router links are assumed to run at 10 Gb/s. Their cost is explicitly set to 10 in both protocols to keep path selection consistent across devices.

Within Area 0, OSPF advertises individual VLAN, routed-link, and loopback prefixes, including C's public-server subnet. The site /20 and /52 allocations listed in [Section 3.4](03_addressing.md#34-site-blocks-reserves-and-summarization) reserve address space for growth; they are not advertised as OSPF summaries.

### 4.2 Least-cost paths and ECMP

OSPF selects the path with the lowest sum of outgoing-interface costs. Between site routers, the direct links to C have lower costs than the alternatives:

| Source and destination | Normal direct path | Alternative via the third site | Selected normal path |
| --- | --- | --- | --- |
| RA → RC | RA–RC: 10 | RA–RB–RC: 50 + 50 = 100 | RA–RC |
| RB → RC | RB–RC: 50 | RB–RA–RC: 50 + 10 = 60 | RB–RC |

If A–C fails, RA reaches RC through RB at cost 100. This backup path restores connectivity but is limited to 2 Gb/s, with a one-way WAN propagation delay of `12 ms + 10 ms = 22 ms`, compared with 5 ms on the direct link. These delays exclude local links, serialization, queuing, and processing.

Paths between distribution switches also include the local routed links at both ends:

| Path | Cost | Role |
| --- | --- | --- |
| DS-A–RA–RC–DS-C | 10 + 10 + 10 = 30 | Normal A–C path |
| DS-A–RA–RB–RC–DS-C | 10 + 50 + 50 + 10 = 120 | A–C backup through B |
| DS-B–RB–RC–DS-C | 10 + 50 + 10 = 70 | Normal B–C path |
| DS-B–RB–RA–RC–DS-C | 10 + 50 + 10 + 10 = 80 | B–C alternative through A |

The extra costs leave the route preference unchanged. For example, A's engineering traffic reaches C's repository over the direct A–C link under normal conditions and through B after that link fails.

Equal-cost multipath (ECMP) is not used because the WAN alternatives have different costs and each distribution switch has only one router uplink. Both address families therefore use the same single preferred path, keeping the high-capacity A–C link primary and A–B–C as its backup.

### 4.3 Expected IPv4 and IPv6 RIB/FIB entries on RA

The routing information base (RIB) holds routes selected from connected networks, local addresses, OSPF, and default-route sources. The forwarding information base (FIB) uses those selections to determine the outgoing interface and next hop for packets. The tables below show representative entries expected on RA under normal conditions. Captured lab routes are presented separately in [Section 7](07_validation.md).

**IPv4 (RA)**

| Destination | RIB source | FIB next hop | Outgoing connection |
| --- | --- | --- | --- |
| `10.80.241.1/32` | Local RA loopback | Local delivery | RA |
| `10.80.240.0/30` | Connected | On-link | RA–RC |
| `10.80.240.4/30` | Connected | On-link | RA–RB |
| `10.80.240.12/30` | Connected | On-link | RA–DS-A |
| `10.80.2.64/26` (A engineering) | OSPFv2 | `10.80.240.13` (DS-A) | RA–DS-A |
| `10.80.16.0/24` (B robotics) | OSPFv2 | `10.80.240.6` (RB) | RA–RB |
| `10.80.32.0/26` (C internal servers) | OSPFv2 | `10.80.240.2` (RC) | RA–RC |
| `0.0.0.0/0` | OSPFv2 external default | `10.80.240.2` (RC) | RA–RC |

**IPv6 (RA)**

| Destination | RIB source | FIB next-hop router | Outgoing connection |
| --- | --- | --- | --- |
| `2001:db8:6500:f100::1/128` | Local RA loopback | Local delivery | RA |
| `2001:db8:6500:f001::2/127` | Connected | On-link | RA–RC |
| `2001:db8:6500:f002::2/127` | Connected | On-link | RA–RB |
| `2001:db8:6500:f011::2/127` | Connected | On-link | RA–DS-A |
| `2001:db8:6500:1006::/64` (A engineering) | OSPFv3 | DS-A | RA–DS-A |
| `2001:db8:6500:2002::/64` (B robotics) | OSPFv3 | RB | RA–RB |
| `2001:db8:6500:3001::/64` (C internal servers) | OSPFv3 | RC | RA–RC |
| `::/0` | OSPFv3 external default | RC | RA–RC |

OSPFv3 uses the neighbor's link-local address as the next hop. Since these interface addresses are not fixed in the design, the IPv6 table identifies each next-hop router and its outgoing connection. The connected /127s match the link assignments in Section 3.

The default entries depend on RC's Internet reachability. RC originates a default into each OSPF version only while it has a usable Internet default for that address family. Those routes come from the eBGP policy in [Section 5](05_bgp.md), keeping Internet routing inside OSPF limited to defaults.

For a packet addressed to the repository at `10.80.32.10`, A's workstation first uses its DS-A gateway. The forwarding sequence is then DS-A → RA (`10.80.240.14`) → RC (`10.80.240.2`) → DS-C (`10.80.240.21`) → repository. Traffic to the repository's IPv6 address, `2001:db8:6500:3001::10`, follows the same devices.

### 4.4 Failure detection, reconvergence, and forwarding updates

Both OSPF versions use proposed WAN Hello and Dead intervals of **10 seconds** and **40 seconds**, with matching settings at each end of an adjacency. A physical link-down indication allows failure processing to begin immediately. If the interface stays up but Hellos stop arriving, OSPF declares the adjacency failed when the Dead interval expires. These timers govern detection, not total convergence time.

After detecting an A–C failure, the routing devices update forwarding in three steps:

1. RA and RC update their link-state information and flood link-state advertisements (LSAs) through the remaining adjacencies.
2. Each OSPF version updates its own link-state database and runs a shortest-path-first (SPF) calculation, selecting RA–RB–RC as the alternative path.
3. The selected route enters the RIB, and the resulting FIB update directs RA's traffic for C through RB.

On RA, this changes the IPv4 next hop for `10.80.32.0/26` from `10.80.240.2` (RC) to `10.80.240.6` (RB). The IPv6 route to `2001:db8:6500:3001::/64` likewise uses RB over A–B. Hosts continue using their existing addresses and distribution-switch gateways throughout the change.

Packets may be lost before the new forwarding entries are installed. TCP can retransmit and reduce its congestion window; an established connection may survive if connectivity returns before it times out. Once A–C and its adjacency recover, SPF selects the lower-cost direct path again. [Section 7](07_validation.md) documents the lab's route changes and post-failure reachability; active TCP survival and convergence time were not measured.

### 4.5 Routing diagram

![KAS dual-stack OSPF topology showing Area 0 adjacencies and link costs.](../diagrams/fig4_1_kas_ospf_routing_bw.png)

*Figure 4.1. Area 0 adjacencies and link costs for both address families. Site blocks indicate address allocations.*
