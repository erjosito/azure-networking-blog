# References — "Three commands that lied on a working ExpressRoute lab"

---

## Microsoft Learn — Azure ExpressRoute

- **ExpressRoute BGP communities**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-routing#bgp-communities

- **Configure ExpressRoute private peering**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-howto-routing-portal-resource-manager

- **ExpressRoute gateway SKUs and performance**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-about-virtual-network-gateways

- **ExpressRoute routing requirements (BGP MD5, AS-PATH, communities)**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-routing

- **Azure CLI: `az network express-route` reference**
  https://learn.microsoft.com/en-us/cli/azure/network/express-route

---

## Megaport

- **Megaport API v2 — product endpoint (polymorphic GET)**
  https://dev.megaport.com/#tag/Products/operation/getProductByProductUid

- **Megaport API v2 — MCR product type**
  https://dev.megaport.com/#tag/MCR

- **Megaport API v2 — VXC product type**
  https://dev.megaport.com/#tag/VXC

- **Megaport MCR technical overview**
  https://docs.megaport.com/mcr/

- **Megaport Terraform provider**
  https://registry.terraform.io/providers/megaport/megaport/latest/docs

---

## Terraform providers

- **AzureRM Terraform provider — `azurerm_express_route_circuit`**
  https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/express_route_circuit

- **AzureRM Terraform provider — `azurerm_express_route_gateway`**
  https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/express_route_gateway

- **Megaport Terraform provider — `megaport_mcr`**
  https://registry.terraform.io/providers/megaport/megaport/latest/docs/resources/megaport_mcr

- **Megaport Terraform provider — `megaport_vxc`**
  https://registry.terraform.io/providers/megaport/megaport/latest/docs/resources/megaport_vxc

---

## Lab

- **Repository:** `net-lab-builder` (GitHub: `erjosito/net-lab-builder`)
- **Lab path:** `labs/expressroute-megaport-bgp/`
- **Validation checklist:** `labs/expressroute-megaport-bgp/validation.md`
- **Lessons learned:** `labs/expressroute-megaport-bgp/lessons-learned.md`
- **Sanitized command output:** `labs/expressroute-megaport-bgp/show-output/`
- **Terraform:** `labs/expressroute-megaport-bgp/terraform/`

> Note: The repository is private at the time of writing. Paths are listed for internal reference; no public URL is available yet.
