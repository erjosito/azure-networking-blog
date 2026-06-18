# References: "Three blind spots in the ExpressRoute DR guide that secured vWAN and route maps exposed"

---

## Microsoft Learn: the source article and Virtual WAN

- **Designing for disaster recovery with ExpressRoute private peering** (the article this post updates)
  https://learn.microsoft.com/en-us/azure/expressroute/designing-for-disaster-recovery-with-expressroute-privatepeering

- **Virtual WAN: secured virtual hub (Azure Firewall in the hub)**
  https://learn.microsoft.com/en-us/azure/firewall-manager/secured-virtual-hub

- **Virtual WAN: route maps**
  https://learn.microsoft.com/en-us/azure/virtual-wan/route-maps-about

- **Virtual WAN: hub routing preference**
  https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference

- **ExpressRoute routing requirements (BGP, AS-PATH, MED)**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-routing

---

## BGP and ASN references

- **RFC 5398: Autonomous System (AS) number reservation for documentation use (64496-64511)**
  https://www.rfc-editor.org/rfc/rfc5398

- **RFC 6996: Autonomous System (AS) reservation for private use**
  https://www.rfc-editor.org/rfc/rfc6996

- **RFC 6793: BGP support for four-octet AS number space (and AS_TRANS 23456)**
  https://www.rfc-editor.org/rfc/rfc6793

---

## Megaport

- **Megaport MCR technical overview**
  https://docs.megaport.com/mcr/

- **Megaport Terraform provider**
  https://registry.terraform.io/providers/megaport/megaport/latest/docs

- **Megaport API v3: product action (CANCEL_NOW)**
  https://dev.megaport.com/

---

## GCP (on-premises simulator)

- **Cloud Router: route selection and BGP best-path behavior**
  https://cloud.google.com/network-connectivity/docs/router/concepts/overview

- **VPC routes: dynamic routing mode**
  https://cloud.google.com/vpc/docs/routes

---

## Terraform providers

- **AzureRM: `azurerm_express_route_circuit`**
  https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/express_route_circuit

- **AzureRM: `azurerm_virtual_hub_route_map`**
  https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/virtual_hub_route_map

- **Megaport: `megaport_mcr`**
  https://registry.terraform.io/providers/megaport/megaport/latest/docs/resources/megaport_mcr

- **Megaport: `megaport_vxc`**
  https://registry.terraform.io/providers/megaport/megaport/latest/docs/resources/megaport_vxc

---

## Lab

- **Repository:** `net-lab-builder` (GitHub: `erjosito/net-lab-builder`)
- **Lab path:** `labs/vwan-dual-er-symmetric/`
- **Design doc (route-map mechanisms, AS-path rationale):** `labs/vwan-dual-er-symmetric/design.md`, section 4
- **Sanitized command output:** `labs/vwan-dual-er-symmetric/show-output/`
- **Deploy and teardown log:** `labs/vwan-dual-er-symmetric/deploy-log.md`

> Note: The lab repository is private at the time of writing. Paths are listed for internal reference; no public URL is available yet.
