# KAS Network Design

ESE 4070/5070 Group Network Design and Validation Project, Fall 2026.

Design a dual-stack network for Keystone Advanced Systems, a fictional engineering company with three sites: headquarters, a robotics lab, and a data center with two Internet providers.

The project covers VLAN segmentation, IPv4/IPv6 addressing, OSPF routing, BGP policy, transport behavior, and failure recovery. A representative routed network must be validated in IPMininet through connectivity, TCP throughput, packet captures, and WAN failover tests.

## Project files

| Location | Contents |
| --- | --- |
| [DESIGN.md](DESIGN.md) | Shared parameters, addressing, VLANs, and pending decisions |
| [diagrams/](diagrams/) | Editable topology and previews |
| [sections/](sections/) | Report sections |

## Required deliverables

- Team report in PDF format, including design decisions, calculations, diagrams, and validation evidence.
- IPMininet topology file, `kas.py`.
