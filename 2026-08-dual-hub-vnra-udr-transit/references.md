# References

## Source Lab

- **GitHub Lab Repository:** [erjosito/net-lab-builder/labs/dual-hub-vnra-udr-transit](https://github.com/erjosito/net-lab-builder/tree/main/labs/dual-hub-vnra-udr-transit)
  - Validation Report: `validation.md` (stage 1-v3 final, 2026-08-19)
  - Lessons Learned: `lessons-learned.md` (L1–L11)
  - Design Document: `design.md` (Trinity review, B1–B6 applied)
  - Deployment Script: `deploy.ps1` (Tank, correlation_id: vnra-c7e2a3f1)

## Evidence Artifacts

### Pre-Fix Failure (100% Loss)

- `show-output/validation/s2-test1-to-test2.json` – Initial validation, 100% packet loss
- `show-output/validation/s2-test2-to-test1.json` – Return path, 100% packet loss
- `show-output/validation/retry-20260819T185118+0200/06-test1-to-test2.json` – Retry, unchanged 100% loss
- `show-output/validation/retry-20260819T185118+0200/07-test2-to-test1.json` – Retry return, unchanged 100% loss

### Root Cause Discovery

- `show-output/validation/retry-20260819T185118+0200/04-peerings-hub1.json` – Hub1 peerings (missing allowVirtualNetworkAccess)
- `show-output/validation/retry-20260819T185118+0200/05-peerings-hub2.json` – Hub2 peerings (missing allowVirtualNetworkAccess)
- `show-output/validation/retry-20260819T185118+0200/09-vnra1-metrics.json` – Pre-fix metrics (all zero)
- `show-output/validation/retry-20260819T185118+0200/09-vnra2-metrics.json` – Pre-fix metrics (all zero)

### Fix Application

- `show-output/validation/retry-20260819T185118+0200/10-peering-access-correction.json` – PATCH applied to all six peerings
- `show-output/validation/retry-20260819T185118+0200/11-peering-access-verified.json` – Verification summary (all six peerings corrected)

### Post-Fix Success (0% Loss)

- `show-output/validation/retry-20260819T185118+0200/12-after-fix-test1-to-test2.json` – Sweden→Europe, 10/10 packets, 0% loss, avg 33.094 ms
- `show-output/validation/retry-20260819T185118+0200/13-after-fix-test2-to-test1.json` – Europe→Sweden, 10/10 packets, 0% loss, avg 31.372 ms

### Observability Evidence

- `show-output/validation/s3-test1-effective-routes.json` – Spoke1 effective routes (UDR Active)
- `show-output/validation/s3-test2-effective-routes.json` – Spoke2 effective routes (UDR Active)
- `show-output/validation/s4-nw-nexthop-test1-to-test2.json` – Network Watcher next-hop (spoke perspective)
- `show-output/validation/s4-rt-hub1-vnra-routes.json` – Hub1 VNRA route table (configured routes)
- `show-output/validation/s4-rt-hub2-vnra-routes.json` – Hub2 VNRA route table (configured routes)
- `show-output/validation/s5-a1-subnet-effectiveRouteTable.txt` – Effective route API result (HTTP 404 gap)
- `show-output/validation/s5-vnra1-get.json` – VNRA1 resource state (5-IP reservation)
- `show-output/validation/s5-vnra2-get.json` – VNRA2 resource state (5-IP reservation)
- `show-output/validation/s5-c-vnra1-metrics.json` – VNRA1 metrics post-deployment

## Microsoft Documentation

- [Virtual Network Routing Appliance Overview](https://learn.microsoft.com/azure/virtual-network/virtual-network-routing-appliance-overview)
- [Create a Virtual Network Routing Appliance](https://learn.microsoft.com/azure/virtual-network/virtual-network-routing-appliance-create)
- [Troubleshoot Virtual Network Routing Appliance](https://learn.microsoft.com/azure/virtual-network/virtual-network-routing-appliance-troubleshoot)
- [VNet Peering Overview](https://learn.microsoft.com/azure/virtual-network/virtual-network-peering-overview)
- [Create/Update VNet Peering](https://learn.microsoft.com/azure/virtual-network/virtual-network-manage-peering)
- [User-Defined Routes (UDR)](https://learn.microsoft.com/azure/virtual-network/virtual-networks-udr-overview)
- [Effective Routes](https://learn.microsoft.com/azure/virtual-network/diagnose-network-routing-problem#view-effective-routes-for-a-virtual-machine-network-interface)

## Related Blog Posts

- Cloudtrooper: [What is the Azure Virtual Network Routing Appliance?](https://blog.cloudtrooper.net/2026/03/07/what-is-the-azure-virtual-network-routing-appliance/)
- Cloudtrooper: [Don't let your Azure routes bite you](https://blog.cloudtrooper.net/2020/11/28/dont-let-your-azure-routes-bite-you/)
- Cloudtrooper: [Virtual network gateways routing in Azure](https://blog.cloudtrooper.net/2023/02/06/virtual-network-gateways-routing-in-azure/)

## Diagrams (Mermaid)

All diagrams in the lab repository under `diagrams/`:
- `01-topology-overview.md` – Network topology, VNets, subnets, VMs, VNRA instances
- `02-udr-data-path.md` – Forward and return UDR chains, hop-by-hop lookup
- `03-observability-evidence.md` – Observable surfaces (S1–S5 validation probes)
- `04-cleanup-boundary.md` – Resource dependency tree, deletion sequence

## Related Topics

- Azure Networking: Hub-and-spoke patterns
- Routing: User-defined routes (UDR), effective routes, longest-prefix match
- Peering: VNet peering flags, regional vs. global, transitive routing limits
- Network Watcher: Next-hop analysis, effective routes diagnosis
- TTL (Time To Live): Hop counting, traceroute limitations, TTL-invisible forwarding
