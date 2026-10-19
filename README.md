# Azure Networking Blog

Hands-on diagnostics, gotchas, and field findings from deploying and troubleshooting Azure Networking labs.

## Posts

The following posts have been dynamically generated with GitHub Copilot CLI and [Squad](https://github.com/bradygaster/squad) with little to zero human intervention.

- **[2026-10] Subnet peering: expose overlapping backends without extra transit VNets**: Two distinct backends keep the same IP while unique in-spoke NAT aliases avoid an extra transit VNet layer; HTTP, effective routes, and the complete 78-file evidence archive explain the tested path and cost caveats
  - [Read post](./2026-10-subnet-peering-overlapping-spokes/)

- **[2026-10] Microsoft or customer backbone? Three Virtual WAN routing designs tested**: A and corrected B2 pass 24/24 DC/Azure directions; four B1 BGP-only reset controls now also pass 24/24 TCP and ICMP under ExpressRoute/VPN HRP, supporting a tested operational caveat rather than a scenario blocker
  - [Read post](./2026-10-vwan-sdwan-three-hub/)

- **[2026-10] One route table for AKS nodes and Application Gateway**: A completed kubenet/AGIC lab shows how a shared table reuses AKS pod routes, then records the limits of steering gateway-subnet egress through an NVA; Azure resources were cleaned up after testing
  - [Read post](./2026-10-aks-agic-shared-udr/)

- **[2026-10] Azure subnet peering prevents the direct path that full VNet peering allows**: The same endpoint pair returns 0/5, 5/5, then 0/5 with both NVAs off; effective routes explain the direct-path boundary, with a separate two-NVA transit illustration
  - [Read post](./2026-10-subnet-peering-udr-nva-transit/)

- **[2026-09] On-prem to SAP RISE with scoped VNet peering and Azure Firewall — what your design options actually are**: An architectural comparison of the four practical ways to reach a SAP RISE spoke over ExpressRoute when only a firewall subnet is peered — ARS + NVA, `summarizedGatewayPrefixes`, Azure Firewall, and the anti-pattern of widening peering
  - [Read post](./2026-09-sap-rise-scoped-peering-fwaas/) _(draft — end-to-end validation of the reference scenario in progress)_

- **[2026-09] Azure Virtual WAN: ExpressRoute-Backed and Internet-Backed IPsec Tunnels on One On-Premises Device**: How to design routing when both tunnel classes terminate on one CPE, with a floating BGP adjacency rejected and dedicated or static alternatives validated
  - [Read post](./2026-09-vwan-ipsec-over-er-backup/)

- **[2026-09] What happens when on-premises advertises `10.0.0.0/8` to Azure Virtual WAN?**: A packet-by-packet and route-table view of ExpressRoute, Private Routing Intent, and Azure Firewall's two-stage forwarding model
  - [Read post](./2026-09-vwan-rfc1918-routing-intent/)

- **[2026-08] Microsoft Foundry Agents on Private VNets: Prompt-Agent Data Proxy vs Hosted-Agent Micro VM**: Network-layer comparison of Foundry agent types: what stays the same (AgentSubnet, NSG, peering, DNS chain) and what changes (invocation URL, SDK surface, cold-start latency, ephemeral source IP, diagnostics)
  - [Read post](./2026-08-foundry-prompt-vs-hosted-networking/)

- **[2026-08] Multi-Region UDR Transit with Azure Managed VNRA: Design Guide and Observability Model**: Validated cross-region hub-spoke-VNRA topology, complete UDR chain, the narrower diagnostic surface of managed hardware, and TTL-invisible forwarding as a verification signal
  - [Read post](./2026-08-dual-hub-vnra-udr-transit/)

- **[2026-08] Are Azure public, service, and private endpoints equally fast?**: An equivalence benchmark with correctness controls and sensitivity calibration
  - [Read post](./2026-08-storage-endpoint-path-equivalence/)

- **[2026-08] When the AS-path lies**: A Virtual WAN route-map summarization race you cannot see in BGP - a validated mitigation, a negative reproduction, and a corrected false positive
  - [Read post](./2026-08-vwan-routemap-summarization-race/)

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
