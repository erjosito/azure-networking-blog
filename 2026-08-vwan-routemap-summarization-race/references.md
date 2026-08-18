# References: "When the AS-path lies: a Virtual WAN route-map summarization race you cannot see in BGP"

---

## Microsoft Learn: Virtual WAN route-maps and routing

- **Virtual WAN: about route-maps** (the summarization/AS-path-strip behaviour this post turns on)
  https://learn.microsoft.com/en-us/azure/virtual-wan/route-maps-about

- **Virtual WAN: how to use route-maps**
  https://learn.microsoft.com/en-us/azure/virtual-wan/how-to-configure-route-maps

- **Virtual WAN: about virtual hub routing**
  https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing

- **Virtual WAN: Branch-to-Branch connectivity**
  https://learn.microsoft.com/en-us/azure/virtual-wan/virtual-wan-about#branchtobranch

---

## Microsoft Learn: ExpressRoute

- **ExpressRoute routing requirements (BGP, AS-PATH, MSEE ASN 12076)**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-routing

- **ExpressRoute circuit and routing domains (private peering)**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-circuit-peerings

- **ExpressRoute Local circuits (Standard vs Local)**
  https://learn.microsoft.com/en-us/azure/expressroute/expressroute-faqs#expressroute-local

---

## Tooling used in the lab

- **`az network express-route list-route-tables`** (MSEE route table — read as JSON, not table)
  https://learn.microsoft.com/en-us/cli/azure/network/express-route#az-network-express-route-list-route-tables

- **BIRD 2 routing daemon** (the VPN branch NVA — `birdc show route`)
  https://bird.network.cz/

- **Megaport MCR / VXC** (on-prem ExpressRoute simulation via static routes + BGP export prefix-filter-list)
  https://docs.megaport.com/cloud/megaport/mcr/

---

## Lab evidence (in the `net-lab-builder` repo)

- Lab root: `labs/vwan-routemap-summarization/README.md`
- Mitigation validation: `labs/vwan-routemap-summarization/show-output/round2/65-vpnbranch-mitigation-validation.txt`
- Sampling harness summary (N=20, 3:1): `labs/vwan-routemap-summarization/show-output/round2/71-race-sampling-summary.md`
- Operational gotchas (prefix-filter-list, `bgp_status` unreliability, route-table JSON quirk): `labs/vwan-routemap-summarization/lessons-learned.md`
