# Azure Networking Blog

Hands-on diagnostics, gotchas, and field findings from deploying and troubleshooting Azure Networking labs.

The following posts have been generated with GitHub Copilot CLI and [Squad](https://github.com/bradygaster/squad).

## Posts

- **[2026-08] Microsoft Foundry Agents on Private VNets: Prompt-Agent Data Proxy vs Hosted-Agent Micro VM** — Network-layer comparison of Foundry agent types: what stays the same (AgentSubnet, NSG, peering, DNS chain) and what changes (invocation URL, SDK surface, cold-start latency, ephemeral source IP, diagnostics).
  - [Read post](./2026-08-foundry-prompt-vs-hosted-networking/)

- **[2026-08] Multi-Region UDR Transit with Azure Managed VNRA: Design Guide and Observability Model** — Validated cross-region hub-spoke-VNRA topology, complete UDR chain, the narrower diagnostic surface of managed hardware, and TTL-invisible forwarding as a verification signal.
  - [Read post](./dual-hub-vnra-udr-transit/)

- **[2026-08] Are Azure public, service, and private endpoints equally fast?** — An equivalence benchmark with correctness controls and sensitivity calibration.
  - [Read post](./2026-08-storage-endpoint-path-equivalence/)

- **[2026-06] Three blind spots in the ExpressRoute DR guide** — How secured vWAN, partner-managed CEs, and vWAN route maps change ExpressRoute DR path engineering.
  - [Read post](./2026-06-vwan-dual-er-symmetric/)

- **[2026-05] The route table that didn't lie** — Diagnosing ExpressRoute BGP with the Azure CLI.
  - [Read post](./2026-05-expressroute-megaport-bgp/)

---

*Each post lives in its own date-prefixed folder. Clone, explore, and reproduce.*
