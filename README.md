# Azure Networking Blog

Hands-on diagnostics, gotchas, and field findings from deploying and troubleshooting Azure Networking labs.

## Posts

The following posts have been dynamically generated with GitHub Copilot CLI and [Squad](https://github.com/bradygaster/squad) with little to zero human intervention.

- **[2026-09] On-prem to SAP RISE with scoped VNet peering and Azure Firewall — what your design options actually are**: An architectural comparison of the four practical ways to reach a SAP RISE spoke over ExpressRoute when only a firewall subnet is peered — ARS + NVA, `summarizedGatewayPrefixes`, Azure Firewall, and the anti-pattern of widening peering
  - [Read post](./2026-09-sap-rise-scoped-peering-fwaas/) _(draft — end-to-end validation of the reference scenario in progress)_

- **[2026-09] Backing Up Azure Virtual WAN IPsec over ExpressRoute with Internet VPN**: Why dedicated per-tunnel BGP adjacencies survive complete ExpressRoute loss, a floating adjacency does not, and static backup requires health automation
  - [Read post](./2026-09-vwan-ipsec-over-er-backup/)

- **[2026-09] What happens when on-premises advertises `10.0.0.0/8` to Azure Virtual WAN?**: A packet-by-packet and route-table view of ExpressRoute, Private Routing Intent, and Azure Firewall's two-stage forwarding model
  - [Read post](./2026-09-vwan-rfc1918-routing-intent/)

- **[2026-08] Multi-Region UDR Transit with Azure Managed VNRA: Design Guide and Observability Model**: Validated cross-region hub-spoke-VNRA topology, complete UDR chain, the narrower diagnostic surface of managed hardware, and TTL-invisible forwarding as a verification signal
  - [Read post](./2026-08-dual-hub-vnra-udr-transit/)

- **[2026-08] Are Azure public, service, and private endpoints equally fast?**: An equivalence benchmark with correctness controls and sensitivity calibration
  - [Read post](./2026-08-storage-endpoint-path-equivalence/)
- **[2026-06] Three blind spots in the ExpressRoute DR guide**: How secured vWAN, partner-managed CEs, and vWAN route maps change ExpressRoute DR path engineering
  - [Read post](./2026-06-vwan-dual-er-symmetric/)
- **[2026-05] The route table that didn't lie**: Diagnosing ExpressRoute BGP with the Azure CLI
  - [Read post](./2026-05-expressroute-megaport-bgp/)

---

*Each post lives in its own date-prefixed folder. Clone, explore, and reproduce.*

---

## Contributing / naming convention

All post folders **must** use the naming pattern `YYYY-MM-<slug>`, where:

- `YYYY-MM` is the year and month the post was first added to this repository (use the earliest git-add date if backfilling).
- `<slug>` is a short, lowercase, hyphen-separated identifier that matches (or closely tracks) the source lab slug in [`erjosito/net-lab-builder`](https://github.com/erjosito/net-lab-builder).

Examples: `2026-05-expressroute-megaport-bgp`, `2026-08-dual-hub-vnra-udr-transit`, `2026-09-vwan-rfc1918-routing-intent`.

This keeps the post index chronologically sortable and makes cross-referencing labs and posts unambiguous.
