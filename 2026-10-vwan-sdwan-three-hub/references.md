# References and exact A/B1/B2 evidence map

## Scope and publication provenance

Measurements: **16 October 2026**. A prefers the Microsoft backbone; B1 and B2 attempt customer-backbone preference. B1 tests ExpressRoute HRP only, not VPN HRP. B1/B2 have **no new traffic tests**.

The post uses only these matched scenario directories beneath the public [three-hub lab](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub):

| Design | Exact capture directory | Label |
|---|---|---|
| A | [backbone-policy-design-20261016/nva-policy-and-jp-udr](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr) | `nva-policy-and-jp-udr` |
| B1 | [ab-b1-customer-20261016/B1](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1) | `B1` |
| B2 | [ab-b2-customer-20261016/B2](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2) | `B2` |

The evidence is published on public `main`, including the B1/B2 captures and recovery records merged through [erjosito/net-lab-builder#13](https://github.com/erjosito/net-lab-builder/pull/13), commit `c5bef096f4de19b8984450de801c15be8a725817`. Start with the public [A/B design comparison report](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-design-comparison-20261016/README.md).

The existing topology SVG is retained unchanged for the rewrite. It shows connectivity, not a claim that all plotted links carry the selected traffic in every design.

## Complete captured BIRD configurations

All nine links point to the exact design's captured configuration, not a reconstruction or a generic example.

| Design | EU | JP | CN |
|---|---|---|---|
| A | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/router-eu.conf) | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/router-jp.conf) | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/router-cn.conf) |
| B1 | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1/router-eu.conf) | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1/router-jp.conf) | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1/router-cn.conf) |
| B2 | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2/router-eu.conf) | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2/router-jp.conf) | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2/router-cn.conf) |

`router-us.conf`, US route output, and the US firewall captures are present in each exact scenario directory above. They support the described US symmetry; US is not inferred solely from EU.

## Full firewall effective-route captures

The post includes every row, in original order, from each of these six text captures:

| Design | EU full text | JP full text |
|---|---|---|
| A | [EU table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/nva-policy-and-jp-udr-eu-table2.txt) | [JP table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/nva-policy-and-jp-udr-jp-table2.txt) |
| B1 | [EU table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1/B1-eu-table2.txt) | [JP table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1/B1-jp-table2.txt) |
| B2 | [EU table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2/B2-eu-table2.txt) | [JP table2.txt](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2/B2-jp-table2.txt) |

For the corresponding full JSON, replace `.txt` with `.json` in the same directory. Hub metadata, intent metadata, `winners2.json`, and `snapshot2.json` are captured alongside them with the scenario label. Empty AS-path text fields are rendered as `empty`, not discarded. Default Internet and transit-VNet entries are retained.

## NVA selections, attributes, and exports

| Design | All selected routes | Full scenario |
|---|---|---|
| A | [selected-routes.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/selected-routes.json) | [scenario-result.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/scenario-result.json) |
| B1 | [selected-routes.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1/selected-routes.json) | [scenario-result.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/B1/scenario-result.json) |
| B2 | [selected-routes.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2/selected-routes.json) | [scenario-result.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/B2/scenario-result.json) |

Each exact scenario directory also contains:

- `router-{eu,jp,cn}-bird-routes.txt`: full source for protocol, `BGP.next_hop`, BIRD gateway/interface resolution, AS path, explicit `BGP.local_pref`, and `*` / `!` marker.
- `router-{eu,jp}-export-azure_{0,1}.txt`: offers to both Azure peers, before automatic eBGP local-AS insertion. CN has no Azure peer.
- `{label}-routes-{eu,jp,cn}-decoded.json`: kernel routes, lookups, and full route/export capture.

All **63 selected NVA rows**, seven prefixes at each of three sites for each of three designs, are reproduced in the post. Static `own_dc` routes have no BGP next-hop/path/local-preference attributes; those cells are explicitly `n/a`, with BIRD resolution shown separately. That resolution does not prove successful kernel installation.

## Traffic and verdict interpretation

- [A traffic JSON](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/nva-policy-and-jp-udr-traffic.json): the seven TCP/ICMP cells retained in the post. JP workload / EU spoke succeeds both ways; DC-to-DC regressions remain.
- [A backbone verdict](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/backbone-verdict.json): original combined-policy experiment `PASS`, restored true. It does not make failed traffic cells pass.
- [A source report](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/README.md): broader original experiment context. The A tables in this post use only the exact `nva-policy-and-jp-udr` capture.
- [B1 customer verdict](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b1-customer-20261016/customer-verdict.json): `INCONCLUSIVE`, restored true; intended local customer-mesh Japan path did not win at EU. The post also reports the captured remote winner at US. No forwarding tests.
- [B2 original customer verdict](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-b2-customer-20261016/customer-verdict.json): original verdict `BLOCKED`, with `RESTORE: Lease stopped or expired`. B2's route checks passed, independently of this blocked restoration proof; this original run verdict is not rewritten as a pass.
- [Fresh independent recovery verification](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-final-recovery-verification-20261016/verification-verdict.json): `PASS`, verifying exact source/metadata and restored HRPs/firewall winners after the blocked proof.
- [Router power restoration](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-router-power-restore-20261016/power-restore-verdict.json): `PASS`, restored true, only started routers changed. All four started routers returned to their original deallocated state; probe VMs were untouched.

The JP `!` kernel-export-failed markers are retained. They were not remediated. No B1/B2 traffic test, universal all-DC forwarding, failover, convergence, performance, or physical-path capture claim is made.

## Mechanism and official documentation

- [Exact A transform and UDR builder](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_backbone.py).
- [Source and route collectors](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_snapshot.py).
- [Selected-route parser](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_comparison.py), explicitly preserving `*` and `!`.
- [Virtual hub routing preference](https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference): ordering, remote ExpressRoute exception, interhub `65520-65520`, and documented race-condition caveat. B1's offered local length four versus remote length three does not meet the documented at-least-two-longer condition; no root cause is assigned from that caveat.
- [View virtual hub effective routes](https://learn.microsoft.com/en-us/azure/virtual-wan/effective-routes-virtual-hub).
- [Virtual WAN routing intent](https://learn.microsoft.com/en-us/azure/virtual-wan/about-routing-intent).
- [Azure CLI effective-route reference](https://learn.microsoft.com/en-us/cli/azure/network/vhub#az-network-vhub-get-effective-routes).
- [BIRD 2 documentation](https://bird.network.cz/?get_doc&v=20&f=bird.html).

Discriminators in the diagnostic examples: **`HubVirtualNetworkConnection` singular** for the unsecured connection, **`AzureFirewalls` plural** for the secured firewall.
