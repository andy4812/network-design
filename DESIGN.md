# KAS Network Design

## Architecture
Three sites: Headquarters (A), Robotics Lab (B),
and Data Center / Internet Edge (C).

## Router Names
RA: Site A
RB: Site B
RC: Site C

## WAN Connections
A-C: 10 Gb/s, 5 ms
A-B: 2 Gb/s, 12 ms
B-C: 2 Gb/s, 10 ms

## Internal Routing
IPv4: OSPFv2 Area 0
IPv6: OSPFv3 Area 0

## Internet Routing
AS65050
ISP-1: AS64501, preferred
ISP-2: AS64502, backup

## Address Allocation
A: 10.80.0.0/20
B: 10.80.16.0/20
C: 10.80.32.0/20