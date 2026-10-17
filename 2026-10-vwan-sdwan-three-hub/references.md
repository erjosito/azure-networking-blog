# References and exact all-hub B2B evidence map

Current measurements: 17 October 2026. Every current A/B1/B2 table and traffic matrix uses the all-enabled rerun, not the historical mixed-setting revision.

The rerun controller, report, sanitized captures and restoration proofs are published through [erjosito/net-lab-builder#16](https://github.com/erjosito/net-lab-builder/pull/16).

[Full rerun report](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-summary-20261017/README.md) and [all 588 directional cells](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-summary-20261017/traffic.csv).

## Primary matched captures

### A: A, plus JP workload UDR

[Full scenario](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/scenario-result.json); [selected routes](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/selected-routes.json); [42-direction traffic](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/traffic-summary.json); [packet observations](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/path-observations.json).

| Site | Complete BIRD configuration | Full firewall table |
|---|---|---|
| EU | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-eu.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/A-workload-UDR-eu-table2.txt) |
| US | [router-us.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-us.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/A-workload-UDR-us-table2.txt) |
| JP | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-jp.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/A-workload-UDR-jp-table2.txt) |
| CN | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-cn.conf) | No hub attachment |

Full firewall JSON is alongside the text with a `.json` suffix. Raw BIRD selections and alternatives are in `router-{site}-bird-routes.txt`; both Azure export views are in `router-{site}-export-azure_{0,1}.txt`. CN has no Azure peers. NVA route snapshots also retain Linux routes, policy rules and lookups. The post renders all EU/JP firewall entries and all seven prefixes on EU/JP/CN, including `!` kernel-export failures.

### B1: B1, JP direct prefix returned

[Full scenario](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/scenario-result.json); [selected routes](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/selected-routes.json); [42-direction traffic](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/traffic-summary.json); [packet observations](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/path-observations.json).

| Site | Complete BIRD configuration | Full firewall table |
|---|---|---|
| EU | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-eu.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/B1-returned-eu-table2.txt) |
| US | [router-us.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-us.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/B1-returned-us-table2.txt) |
| JP | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-jp.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/B1-returned-jp-table2.txt) |
| CN | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-cn.conf) | No hub attachment |

Full firewall JSON is alongside the text with a `.json` suffix. Raw BIRD selections and alternatives are in `router-{site}-bird-routes.txt`; both Azure export views are in `router-{site}-export-azure_{0,1}.txt`. CN has no Azure peers. NVA route snapshots also retain Linux routes, policy rules and lookups. The post renders all EU/JP firewall entries and all seven prefixes on EU/JP/CN, including `!` kernel-export failures.

### B2: B2, zero extra EU/US prepends

[Full scenario](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/scenario-result.json); [selected routes](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/selected-routes.json); [42-direction traffic](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/traffic-summary.json); [packet observations](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/path-observations.json).

| Site | Complete BIRD configuration | Full firewall table |
|---|---|---|
| EU | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-eu.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/B2-eu-table2.txt) |
| US | [router-us.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-us.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/B2-us-table2.txt) |
| JP | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-jp.conf) | [table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/B2-jp-table2.txt) |
| CN | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-cn.conf) | No hub attachment |

Full firewall JSON is alongside the text with a `.json` suffix. Raw BIRD selections and alternatives are in `router-{site}-bird-routes.txt`; both Azure export views are in `router-{site}-export-azure_{0,1}.txt`. CN has no Azure peers. NVA route snapshots also retain Linux routes, policy rules and lookups. The post renders all EU/JP firewall entries and all seven prefixes on EU/JP/CN, including `!` kernel-export failures.

## Additional controls and closure

- [Mixed baseline](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-mixed-baseline-20261017/baseline/scenario-result.json).
- [All B2B baseline](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-enabled-baseline-20261017/baseline/scenario-result.json).
- [A, NVA policy only](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A/scenario-result.json).
- [A, plus JP workload UDR](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/scenario-result.json).
- [B1, ExpressRoute initial](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1/scenario-result.json).
- [B1, JP direct prefix withdrawn](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-withdrawn/scenario-result.json).
- [B1, JP direct prefix returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/scenario-result.json).
- [B1 one-ASN, initial](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN/scenario-result.json).
- [B1 one-ASN, withdrawn](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN-withdrawn/scenario-result.json).
- [B1 one-ASN, returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN-returned/scenario-result.json).
- [B1, VPN HRP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-VPN-20261017/B1-VPN/scenario-result.json).
- [B2, zero extra EU/US prepends](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/scenario-result.json).
- [Original mixed state restored](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-restore-mixed-20261017/restored/scenario-result.json).
- [Independent original-state verification](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-independent-verify-20261017/independent-verification/scenario-result.json).

[Original VM power inventory restored](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-power-stop-20261017/power-verdict.json). Exact source bytes/metadata, original mixed hub flags/HRPs and original paired firewall winners were independently restored; traffic returned to 28/42 TCP and 32/42 ICMP. Temporary A route-table cleanup is captured in the A controller's restore evidence.

Collector PASS means complete evidence and exact configuration closure, not all traffic passed. No throughput, failover or universal path-symmetry claim follows. The packet observations explicitly expose cases where reachability does not establish the intended Virtual WAN traversal.

## Historical mixed-setting evidence, not current table sources

- [Original A experiment and forwarding limitations](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/README.md).
- [Original A/B comparison, including B1 INCONCLUSIVE and B2 BLOCKED verdicts](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-design-comparison-20261016/README.md).
- [Original three-prepend route-history control](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/hrp-reselection-control-20261017/README.md).
- [Original one-ASN-difference route-history control](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/hrp-one-asn-control-20261017/README.md).
- [Independent exact reset after the historical B2 blocked proof](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-final-recovery-verification-20261016/verification-verdict.json).

Those original verdicts are preserved; the later successful controls do not retroactively turn blocked measurements into passes. Their source publication is retained in erjosito/net-lab-builder#13, erjosito/net-lab-builder#14 and erjosito/net-lab-builder#15.

## Commands, implementation and official references

- [design_b2b.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_b2b.py).
- [b2b_report.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/b2b_report.py).
- [design_backbone.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_backbone.py).
- [design_snapshot.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_snapshot.py).
- [design_comparison.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_comparison.py).
- [Hub routing preference](https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference).
- [BGP peering considerations, including branch-to-branch](https://learn.microsoft.com/en-us/azure/virtual-wan/scenario-bgp-peering-hub#benefits-and-considerations).
- [Routing intent](https://learn.microsoft.com/en-us/azure/virtual-wan/about-routing-intent).
- [Effective routes](https://learn.microsoft.com/en-us/azure/virtual-wan/effective-routes-virtual-hub).
- [BIRD 2 documentation](https://bird.network.cz/?get_doc&v=20&f=bird.html).

The diagnostic discriminators remain `AzureFirewalls` (plural) for secured firewall routes and `HubVirtualNetworkConnection` (singular) for unsecured connection routes. The topology SVG is unchanged and represents connectivity, not proof that every drawn path carries test traffic.
