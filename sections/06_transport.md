## 6. End-to-end Transport and Packet Behavior

### 6.1 HTTPS connection

An engineering workstation at A downloads software from the repository at C. The examples below trace separate IPv4 and IPv6 HTTPS connections between these endpoints.

| Endpoint | VLAN | IPv4 address | IPv6 address |
| --- | --- | --- | --- |
| Engineering workstation at A | 160 | 10.80.2.74/26 | 2001:db8:6500:1006::10/64 |
| Software repository at C | 310 | 10.80.32.10/26 | 2001:db8:6500:3001::10/64 |

Each connection uses client port 51514 and server port 443. Its TCP four-tuple is `(source IP, source port, destination IP, destination port)`:

- IPv4: `(10.80.2.74, 51514, 10.80.32.10, 443)`
- IPv6: `(2001:db8:6500:1006::10, 51514, 2001:db8:6500:3001::10, 443)`

Both examples begin with the TCP handshake: SYN, SYN-ACK, and ACK. TLS setup follows before the client sends its HTTPS request. Server replies reverse the source and destination addresses and ports.

### 6.2 IPv4 packet trace

Both traces follow the normal A–C path selected by the OSPF costs in [Section 4](04_routing.md): workstation → DS-A → RA → RC → DS-C → repository. They assume Ethernet links, an initial TTL or Hop Limit of 64, and no fragmentation or QoS remarking.

The workstation recognizes that `10.80.32.10` is outside its local `10.80.2.64/26` subnet and sends the packet through gateway `10.80.2.65`. With an empty ARP cache, it first broadcasts an ARP request for that gateway to `ff:ff:ff:ff:ff:ff` in VLAN 160. DS-A replies with its VLAN 160 SVI MAC address, which the workstation caches. The outgoing frame then uses DS-A's MAC as its destination while the enclosed IP packet retains the repository's destination address.

ARP resolution normally precedes the SYN, so the first HTTPS application-data packet reuses the learned mapping. The table shows its five transmissions across four routed hops, with the equivalent IPv6 forwarding alongside. MAC labels identify interfaces; access switches do not count as routed hops.

| Transmitting device | IPv4 next hop | IPv6 neighbor interface | Ethernet source MAC -> destination MAC | TTL / Hop Limit sent |
| --- | --- | --- | --- | --- |
| Workstation | 10.80.2.65 | fe80::1 on VLAN 160 | Workstation -> DS-A SVI 160 | 64 |
| DS-A | 10.80.240.14 | 2001:db8:6500:f011::3 | DS-A uplink -> RA interface toward DS-A | 63 |
| RA | 10.80.240.2 | 2001:db8:6500:f001::3 | RA interface toward RC -> RC interface toward RA | 62 |
| RC | 10.80.240.21 | 2001:db8:6500:f013::2 | RC interface toward DS-C -> DS-C uplink | 61 |
| DS-C | 10.80.32.10 | 2001:db8:6500:3001::10 | DS-C SVI 310 -> Repository | 60 |

At each routed hop, the forwarding device resolves its next-hop MAC through ARP if needed. DS-C resolves the repository's MAC directly because VLAN 310 is locally connected.

The packet changes only where forwarding requires it:

- **IPv4:** source `10.80.2.74`, destination `10.80.32.10`, protocol 6, length, identification, and fragmentation fields remain unchanged. Each router decrements TTL and updates the header checksum, reducing TTL from 64 to 60 across the path.
- **TCP:** ports, sequence and acknowledgment numbers, flags, window, options, and encrypted payload remain unchanged. No NAT occurs between sites. The TCP checksum stays valid because TTL is outside its pseudo-header. [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.1)
- **Ethernet:** each router removes the incoming frame and builds a new one using its outgoing-interface MAC, the next-hop MAC, and a newly computed frame check sequence (FCS).

Access switches preserve the source and destination MAC addresses and the IP TTL. They add or remove VLAN tags as needed, carrying VLAN 160 on A's access trunk and VLAN 310 on C's access trunk. These VLANs end at the distribution switches and do not cross the routed links.

### 6.3 IPv6 packet trace

IPv6 follows the same route but uses Neighbor Discovery to resolve MAC addresses. The workstation learns default router `fe80::1` from DS-A's Router Advertisement. If the gateway's MAC mapping is missing, the workstation sends an ICMPv6 Neighbor Solicitation for `fe80::1` to solicited-node multicast address `ff02::1:ff00:1`, using Ethernet destination `33:33:ff:00:00:01`. DS-A returns its link-layer address in a Neighbor Advertisement. This exchange replaces ARP and uses multicast rather than broadcast. [RFC 4861](https://www.rfc-editor.org/rfc/rfc4861.html#section-7.2)

Once the mapping is available, the data packet follows the five transmissions in Section 6.2. The table's transit IPv6 addresses identify the interfaces assigned in Section 3; OSPFv3 uses their link-local addresses as next hops. Each forwarding device uses Neighbor Discovery on its outgoing link as needed. At the final hop, DS-C resolves the repository address, `2001:db8:6500:3001::10`, on VLAN 310.

Across the path, source `2001:db8:6500:1006::10`, destination `2001:db8:6500:3001::10`, Next Header 6, payload length, and TCP fields remain unchanged. Each router reduces Hop Limit by one, so the repository receives the packet with a value of 60. IPv6 has no IP-header checksum, and the TCP checksum remains valid. Ethernet addresses and FCS change at each routed hop as in the IPv4 trace.

### 6.4 Windowing with a 12 ms RTT

The windowing comparison uses a 12 ms round-trip time (RTT) and a 10 MB file, where 10 MB is 10,000,000 bytes. Each full segment carries 1,460 payload bytes in a 1,500-byte IPv4 packet with minimum IP and TCP headers. The estimates exclude TLS overhead, connection setup, loss, and ACK serialization.

| Quantity | Calculation | Result |
| --- | --- | --- |
| Stop-and-wait payload rate | 1,460 x 8 / 0.012 | About 0.973 Mb/s |
| Segments for the file | ceil(10,000,000 / 1,460) | 6,850 |
| Stop-and-wait transfer time | 6,850 x 0.012 | About 82.2 s |
| File serialization at 10 Gb/s | 10,000,000 x 8 / 10,000,000,000 | 8 ms |
| Bandwidth-delay product at 10 Gb/s | 10,000,000,000 x 0.012 / 8 | 15 MB |

Stop-and-wait leaves the link idle after each segment until its ACK returns. At this RTT, its payload rate uses less than 0.01% of a 10 Gb/s link. TCP avoids that idle period by allowing multiple segments to remain unacknowledged, so the sender can continue transmitting while ACKs travel back.

Keeping a 10 Gb/s path busy at this RTT requires roughly 15 MB in flight, assuming no slower access link or endpoint bottleneck. The smaller of the congestion window and the receiver's advertised window limits how much the sender can have outstanding. Both must therefore support that amount, and the receive window requires TCP window scaling.

The 8 ms figure measures only file serialization. Completion also depends on propagation, TCP/TLS setup, slow start, and any loss recovery. Because the 10 MB file is smaller than the path's 15 MB bandwidth-delay product, a new connection may finish the transfer before reaching steady-state capacity.

### 6.5 Transport choices

The transport choice depends on whether the application needs every byte delivered or can replace late data with a newer update.

| Application | Choice | Reason |
| --- | --- | --- |
| Large software download | TCP | Reliable, ordered delivery and retransmission preserve the complete file. Sliding windows support throughput, while congestion control adjusts the sending rate. Completeness takes priority over a fixed delivery deadline. |
| Robot telemetry | UDP | A newer periodic sample can replace a lost one, assuming occasional loss is acceptable. Application sequence numbers and timestamps identify gaps and stale or reordered samples. Pacing and receiver loss feedback control the sending rate. |
| Interactive robot control | UDP | Periodic setpoints have short deadlines, so stale commands must expire. The application uses sequence numbers, timestamps, and expiry checks; commands needing confirmation also use ACKs, duplicate suppression, and retries within their deadline. Congestion feedback and rate limits constrain traffic. Fast control loops stay local, with WAN traffic limited to supervisory control. |
| DNS | UDP for ordinary queries; TCP for truncated responses and zone transfers | UDP preserves query/response message boundaries with no connection setup. Match replies by transaction and question; retry with backoff after loss. TCP provides reliable, ordered delivery when a full response cannot be returned over UDP. Its byte stream uses DNS length framing and TCP congestion control. [RFC 7766](https://www.rfc-editor.org/rfc/rfc7766.html#section-5) |
| Browser HTTP/3 | QUIC over UDP | QUIC supplies reliable, ordered delivery within each stream, loss recovery, flow control, and congestion control. Independent streams avoid TCP's connection-wide delivery blocking when one stream loses data, allowing unrelated responses to progress. UDP itself does not provide these guarantees. [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html#section-2) |

For telemetry and control, these safeguards belong to the application: UDP itself provides neither delivery guarantees nor congestion control. [RFC 8085](https://www.rfc-editor.org/rfc/rfc8085.html#section-3.1)
