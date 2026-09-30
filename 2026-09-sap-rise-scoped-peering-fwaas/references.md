# References: sap-rise-scoped-peering-fwaas

## Source lab

- **GitHub Lab Repository:** [erjosito/net-lab-builder/labs/sap-rise-scoped-peering-fwaas](https://github.com/erjosito/net-lab-builder/tree/main/labs/sap-rise-scoped-peering-fwaas)
- **Design doc:** [design.md](https://github.com/erjosito/net-lab-builder/blob/main/labs/sap-rise-scoped-peering-fwaas/design.md)
- **Validation notes (including in-progress S1 status):** [validation.md](https://github.com/erjosito/net-lab-builder/blob/main/labs/sap-rise-scoped-peering-fwaas/validation.md)
- **Diagrams:** [diagrams/](https://github.com/erjosito/net-lab-builder/tree/main/labs/sap-rise-scoped-peering-fwaas/diagrams)

## Microsoft Learn / Azure docs

- Azure Route Server: [What is Azure Route Server?](https://learn.microsoft.com/en-us/azure/route-server/overview)
- Azure Route Server: [Branch-to-branch traffic with ExpressRoute and VPN](https://learn.microsoft.com/en-us/azure/route-server/expressroute-vpn-support)
- ExpressRoute: [Optimize ExpressRoute routing](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-optimize-routing)
- ExpressRoute: [About ExpressRoute virtual network gateways](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-about-virtual-network-gateways)
- Virtual Network peering: [Overview](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview)
- Virtual Network peering: [Subnet-level peering (allow multiple peering links between VNets)](https://learn.microsoft.com/en-us/azure/virtual-network/subnet-peering)
- Azure Firewall: [What is Azure Firewall?](https://learn.microsoft.com/en-us/azure/firewall/overview)
- SAP on Azure: [SAP on Azure landing zone reference architecture](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-on-azure-landing-zone-reference-architecture)

## Related posts in this repo

- [2026-09: What happens when on-premises advertises `10.0.0.0/8` to Azure Virtual WAN?](../2026-09-vwan-rfc1918-routing-intent/), a related routing-intent and firewall forwarding topic on the Virtual WAN side.
- [2026-05: The route table that didn't lie](../2026-05-expressroute-megaport-bgp/), the baseline ExpressRoute and Megaport BGP setup this lab extends.
