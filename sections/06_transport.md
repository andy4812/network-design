## 6. End-to-end Transport and Packet Behavior

### 6.1 HTTPS connection

| Endpoint | VLAN | IPv4 address | IPv6 address |
| --- | --- | --- | --- |
| Engineering workstation at A | 160 | 10.80.2.74/26 | 2001:db8:6500:1006::10/64 |
| Software repository at C | 310 | 10.80.32.10/26 | 2001:db8:6500:3001::10/64 |

Using source port 51514 and HTTPS destination port 443, the TCP four-tuples are `(source IP, source port, destination IP, destination port)`:

- IPv4: `(10.80.2.74, 51514, 10.80.32.10, 443)`
- IPv6: `(2001:db8:6500:1006::10, 51514, 2001:db8:6500:3001::10, 443)`

These are separate example connections. Each establishes TCP with SYN, SYN-ACK, and ACK, then completes TLS setup before sending the HTTPS request. Replies reverse the source and destination addresses and ports.

### 6.2 IPv4 packet trace

The trace assumes the direct A-C route for both protocols; Section 4's OSPF costs must select that path. Assume Ethernet links, an initial TTL/Hop Limit of 64, and no fragmentation or QoS remarking.

With an empty ARP cache, the workstation sees that `10.80.32.10` is outside its local `10.80.2.64/26` subnet. It broadcasts an ARP request for gateway `10.80.2.65` to `ff:ff:ff:ff:ff:ff` in VLAN 160. DS-A replies with its VLAN 160 SVI MAC address. The workstation caches this mapping and sends the IP packet to that MAC, while retaining the repository's IP destination. It does not ARP for the remote server.

This resolution normally occurs before the SYN. The first HTTPS application-data packet reuses the learned mapping and follows the path below. MAC labels identify the interfaces; access switches between endpoints and distribution switches are omitted from the routed-hop count.

| Transmitting device | IPv4 next hop | IPv6 neighbor interface | Ethernet source MAC -> destination MAC | TTL / Hop Limit sent |
| --- | --- | --- | --- | --- |
| Workstation | 10.80.2.65 | fe80::1 on VLAN 160 | Workstation -> DS-A SVI 160 | 64 |
| DS-A | 10.80.240.14 | 2001:db8:6500:f011::3 | DS-A uplink -> RA interface toward DS-A | 63 |
| RA | 10.80.240.2 | 2001:db8:6500:f001::3 | RA interface toward RC -> RC interface toward RA | 62 |
| RC | 10.80.240.21 | 2001:db8:6500:f013::2 | RC interface toward DS-C -> DS-C uplink | 61 |
| DS-C | 10.80.32.10 | 2001:db8:6500:3001::10 | DS-C SVI 310 -> Repository | 60 |

Each forwarding device uses ARP to resolve its IPv4 next hop if that mapping is missing. DS-C resolves the repository itself because VLAN 310 is directly connected.

For this IPv4 packet, source `10.80.2.74`, destination `10.80.32.10`, protocol 6, length, identification, and fragmentation fields remain unchanged. TCP ports, sequence and acknowledgment numbers, flags, window, options, and encrypted payload also remain unchanged. There is no NAT on this inter-site path. Each of the four Layer-3 hops decrements TTL and updates the IPv4 header checksum. The TCP checksum remains valid because TTL is not part of the TCP checksum's pseudo-header. [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.1)

At each Layer-3 hop, the incoming Ethernet frame is removed and a new frame is built with the outgoing interface's source MAC, the next hop's destination MAC, and a newly computed FCS. Access switches preserve the source/destination MACs and IP TTL. They add or remove VLAN tags as needed: VLAN 160 on A's access trunk and VLAN 310 on C's access trunk. The routed links do not carry those VLANs.

### 6.3 IPv6 packet trace

The workstation learns default router `fe80::1` from DS-A's Router Advertisement. If its MAC mapping is absent, it sends an ICMPv6 Neighbor Solicitation targeting `fe80::1`, using solicited-node multicast address `ff02::1:ff00:1` and Ethernet destination `33:33:ff:00:00:01`. DS-A returns a Neighbor Advertisement containing its link-layer address. This NS/NA exchange replaces ARP; IPv6 does not use broadcast. [RFC 4861](https://www.rfc-editor.org/rfc/rfc4861.html#section-7.2)

The data packet follows the same five transmissions in the table. The transit IPv6 addresses identify the neighboring interfaces from Section 3; OSPFv3 uses their link-local addresses as next hops, and Neighbor Discovery resolves those addresses on the corresponding links. At the last hop, DS-C resolves `2001:db8:6500:3001::10` on VLAN 310.

Source `2001:db8:6500:1006::10`, destination `2001:db8:6500:3001::10`, Next Header 6, payload length, and TCP fields remain unchanged. Hop Limit decreases from 64 to 60. IPv6 has no IP-header checksum to update; its TCP checksum remains valid. Ethernet addresses and FCS are replaced at each routed hop as in the IPv4 trace.

### 6.4 Windowing over the 12 ms path

Take 10 MB as 10,000,000 bytes. For illustration, use 1,460 TCP payload bytes per segment, corresponding to a 1,500-byte IPv4 packet with minimum IP/TCP headers. Ignore TLS overhead, connection setup, loss, and ACK serialization in these estimates.

| Quantity | Calculation | Result |
| --- | --- | --- |
| Stop-and-wait payload rate | 1,460 x 8 / 0.012 | About 0.973 Mb/s |
| Segments for the file | ceil(10,000,000 / 1,460) | 6,850 |
| Stop-and-wait transfer time | 6,850 x 0.012 | About 82.2 s |
| File serialization at 10 Gb/s | 10,000,000 x 8 / 10,000,000,000 | 8 ms |
| Bandwidth-delay product at 10 Gb/s | 10,000,000,000 x 0.012 / 8 | 15 MB |

Stop-and-wait sends one segment, then leaves the link idle while awaiting its ACK. Its payload rate uses less than 0.01% of a 10 Gb/s link. TCP pipelines segments so transmission continues while earlier data is still unacknowledged.

Sustaining 10 Gb/s at this RTT requires roughly 15 MB of data in flight, assuming no slower access link or endpoint bottleneck. The sender is limited by the smaller of its congestion window and the receiver's advertised window. Window scaling is needed for a receive window this large. Slow start, loss recovery, and TCP/TLS setup increase completion time; 8 ms is only serialization time, not a predicted download time. A 10 MB transfer from a new connection may finish without reaching steady-state link capacity.

### 6.5 Transport choices

| Application | Choice | Reason |
| --- | --- | --- |
| Large software download | TCP | A reliable, ordered byte stream delivers the complete file and retransmits missing data. Sliding windows support throughput; congestion control adjusts the sending rate. Retransmission delays are acceptable because completeness matters more than a fixed delivery deadline. |
| Robot telemetry | UDP | Periodic samples are separate messages; a newer sample can replace a lost one. Sequence numbers and timestamps detect gaps and stale or reordered samples without delaying delivery. Pace traffic and reduce the rate using receiver loss feedback. This choice assumes occasional sample loss is acceptable. |
| Interactive robot control | UDP | Periodic setpoints have short deadlines, so waiting for an old command's retransmission can be harmful. Use sequence numbers, timestamps, and expiry checks. Commands requiring confirmation use application ACKs, duplicate suppression, and retries only within their deadline. Apply congestion feedback and rate limits; keep the fast control loop local and use WAN traffic for supervisory control. |
| DNS | UDP for ordinary queries; TCP for truncated responses and zone transfers | UDP preserves query/response message boundaries with no connection setup. Match replies by transaction and question; retry with backoff after loss. TCP provides reliable, ordered delivery when a full response cannot be returned over UDP. Its byte stream uses DNS length framing and TCP congestion control. [RFC 7766](https://www.rfc-editor.org/rfc/rfc7766.html#section-5) |
| Browser HTTP/3 | QUIC over UDP | QUIC supplies reliable, ordered delivery within each stream, loss recovery, flow control, and congestion control. Independent streams avoid TCP's connection-wide delivery blocking when one stream loses data, allowing unrelated responses to progress. UDP itself does not provide these guarantees. [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html#section-2) |

UDP has no built-in congestion control or delivery guarantee; the telemetry and control applications must supply the behavior listed above. [RFC 8085](https://www.rfc-editor.org/rfc/rfc8085.html#section-3.1)
