## 8. Failure Analysis, Operations, and Design Review

Each case assumes the other devices and links remain operational. These are expected outcomes, not measured recovery times.

### 8.1 Failure A: A-C WAN link fails during a download

**Immediate effect.** Packets using A-C are lost until forwarding entries change. The Section 6 download stalls, and packets already in flight may arrive out of order during the route change.

**Control plane.** RA and RC detect the failure through link-down indications or OSPF neighbor timeout. OSPFv2 and OSPFv3 update and flood their link-state information. Routers run SPF, update their routing tables, and install new next hops in the forwarding tables. The two protocols converge independently; recovery in one does not prove recovery in the other.

**Stable path.** Download data travels `C -> RC -> RB -> RA -> A`; ACKs return through `A -> RA -> RB -> RC -> C`. The distribution switches and endpoint VLANs are unchanged. The remaining WAN path has a nominal bottleneck of 2 Gb/s, shared with B's traffic. Its one-way propagation delay is `10 + 12 = 22 ms`, giving at least 44 ms round-trip propagation before other delays.

**TCP impact.** Addresses and ports remain unchanged, so existing connections can resume after convergence. TCP retransmits missing data and may reduce its congestion window following loss. Throughput is likely lower because the alternate path has less capacity and greater delay. A connection can still fail if TCP or the application times out before connectivity returns.

### 8.2 Failure B: ISP-1 fails during IPv4 and IPv6 sessions

**Immediate effect.** Internet traffic using ISP-1 is dropped while RC and external networks still select the failed path. Internal KAS traffic continues to use the WAN.

**Control plane.** Link failure or BGP session timeout invalidates routes learned through ISP-1. RC selects usable ISP-2 routes and updates its forwarding tables for both address families. External networks must also select the KAS announcements through ISP-2; changing RC's outbound route alone does not restore the return path. IPv4 and IPv6 may recover at different times. [RFC 4271](https://www.rfc-editor.org/rfc/rfc4271.html#section-9.1)

**Stable path.** Internet traffic passes through `KAS -> RC -> ISP-2`, with return traffic through ISP-2 to RC. This requires ISP-2 to provide both IPv4 and IPv6 transit and carry both public aggregates from Section 3. The available Internet circuit is now 5 Gb/s. RC remains the internal Internet exit; the inter-site topology has not changed.

**TCP impact.** RC remains operational. Private-IPv4 sessions can resume if RC retains their NAT mappings, including public address `203.0.113.17` and translated ports, and the return route becomes usable before timeout. NAT mappings must remain usable across the egress-interface change. Public-server IPv4 sessions retain their public addresses. IPv6 sessions retain their global addresses and need no NAT state, but still depend on bidirectional route recovery. None of these sessions is guaranteed to survive a long outage.

### 8.3 Failure C: Site B robotics gateway fails

**Immediate effect.** VLAN 220 loses routed access through DS-B: IPv4 gateway `10.80.16.1` and IPv6 default router `fe80::1` on that VLAN become unavailable. Robot-to-server traffic and remote engineering control stop. If only the SVI fails, same-VLAN switching can continue. If DS-B fails completely, endpoints on the same working access switch may still communicate, but paths through DS-B are lost.

**Control plane.** When DS-B detects its SVI is down, it withdraws the robotics prefixes from OSPFv2/OSPFv3. If DS-B itself fails, RB detects the lost adjacency and the routing protocols remove paths through DS-B. ARP and Neighbor Discovery cannot select a replacement gateway because none is configured. A forwarding fault that leaves the SVI and routing adjacency up may instead leave stale routes until detected operationally.

**Stable path.** There is no alternate routed path for VLAN 220. The gateway remains a single point of failure until DS-B or its SVI is restored. The WAN triangle cannot replace a failed local gateway. An SVI-only failure need not interrupt B's other VLANs; a complete DS-B failure affects all of them.

**TCP impact.** Connections crossing the robotics gateway stop receiving acknowledgments, retransmit, and eventually time out if the outage persists. They may resume after a short repair if endpoint connection state survives. Same-switch, same-VLAN connections can remain active.

### 8.4 Remaining checks

- **Section 4:** confirm that both routing protocols prefer A-C normally and select A-B-C after failure; specify failure-detection settings.
- **Section 5:** confirm usable ISP-2 routes and public-prefix advertisements in both address families, and NAT-state retention when changing Internet interfaces.
- **Section 7:** record reachability and forwarding routes after the A-C failure. If the lab uses static IPv6, distinguish its lack of automatic rerouting from the production OSPFv3 design. Report interruption durations only if measured.

### 8.5 Engineering review

The weakest part is local gateway availability: redundant WAN circuits do not protect a site from losing its sole distribution switch. RC is also a single point of failure for Internet access despite the two providers.

The first improvement would be a second distribution switch at B, where gateway loss interrupts robotics traffic. Give each access switch an uplink to both distribution switches, provide independent routed uplinks to RB, and use VRRPv3 for IPv4 and IPv6 gateway failover. The existing gateway addresses would become virtual addresses, with separate addresses for each switch. The redundant Layer-2 design would require primary/secondary STP roots and alternate blocked paths, with the active gateways aligned to the primary root. This is a proposed upgrade, not redundancy present in the current topology. [RFC 9568](https://www.rfc-editor.org/rfc/rfc9568.html#section-1)
