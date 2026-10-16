# References and evidence map

## Publication provenance

Measurements: **16 October 2026**. The post uses the captured baseline and two captured policy states, not new publication-time testing. All addresses and ASNs shown are synthetic lab values.

The companion source publication is handled separately. Links below target the intended public `main` paths and may not resolve until that source change is merged. The blog PR must remain unmerged until the source evidence is published and these links are checked.

The topology SVG is adapted from the source lab's `diagrams/topology.svg`. Its stale validation captions and unconditional export claim were replaced with topology-only descriptions. It is not a packet-flow trace.

## Official documentation

- [Virtual hub routing preference](https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference): ordering, interhub `65520-65520`, remote ExpressRoute exception, and documented ER/VPN race condition.
- [View virtual hub effective routes](https://learn.microsoft.com/en-us/azure/virtual-wan/effective-routes-virtual-hub): observation points and route interpretation.
- [Virtual WAN routing intent](https://learn.microsoft.com/en-us/azure/virtual-wan/about-routing-intent): private traffic inspection context.
- [Azure CLI: `az network vhub get-effective-routes`](https://learn.microsoft.com/en-us/cli/azure/network/vhub#az-network-vhub-get-effective-routes): command reference.
- [BIRD 2 documentation](https://bird.network.cz/?get_doc&v=20&f=bird.html): routing tables, BGP attributes, export filters, and kernel protocol.

## Three matching evidence surfaces

All source links are below the public [three-hub lab root](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub).

| State | Verdict / complete scenario | Firewall outputs | BIRD routes and exports | Directional probes |
|---|---|---|---|---|
| Baseline | [baseline-verdict.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/baseline-verdict.json) | [firewalls/](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/firewalls), `current-{eu,us,jp}-table{1,2}.txt` | [routes/](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/routes), `router-*-bird-routes.txt` and `router-*-export-azure_*.txt` | [traffic/](https://github.com/erjosito/net-lab-builder/tree/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/traffic), also embedded in baseline verdict |
| NVA policy only | [scenario-result.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-only/scenario-result.json) | Same directory, `nva-policy-only-{eu,us,jp}-table{1,2}.txt` | Same directory, `selected-routes.json`, `router-*-bird-routes.txt`, `router-*-export-azure_*.txt` | [traffic JSON](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-only/nva-policy-only-traffic.json) |
| NVA policy + JP UDR | [scenario-result.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/scenario-result.json) | Same directory, `nva-policy-and-jp-udr-{eu,us,jp}-table{1,2}.txt` | Same directory, `selected-routes.json`, `router-*-bird-routes.txt`, `router-*-export-azure_*.txt` | [traffic JSON](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/nva-policy-and-jp-udr-traffic.json) |

For kernel state and route lookups in the variants, inspect `{label}-routes-jp-decoded.json` next to the scenario result. It contains `birdRoutes`, `kernelRoutes`, `lookups`, and `exports`; do not infer FIB health solely from selected-route JSON.

## Complete BIRD configurations

These are BIRD-only configuration sources, not strongSwan credentials or WireGuard private keys.

| Site | Baseline | NVA policy only | NVA policy + JP UDR |
|---|---|---|---|
| EU | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/sources/router-eu.conf) | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-only/router-eu.conf) | [router-eu.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/router-eu.conf) |
| US | [router-us.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/sources/router-us.conf) | [router-us.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-only/router-us.conf) | [router-us.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/router-us.conf) |
| JP | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/sources/router-jp.conf) | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-only/router-jp.conf) | [router-jp.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/router-jp.conf) |
| CN | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/hrp-design-live-baseline-20261016/sources/router-cn.conf) | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-only/router-cn.conf) | [router-cn.conf](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/nva-policy-and-jp-udr/router-cn.conf) |

## Transform, collection, and restoration

- [design_backbone.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_backbone.py): exact reversible BIRD transform, five-route UDR builder, and restoration.
- [design_snapshot.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_snapshot.py): source, route, firewall, and traffic collection.
- [design_comparison.py](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_comparison.py): explicit parsing of BIRD `*` and `!` markers.
- [backbone-verdict.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/backbone-verdict.json): `PASS`, `restored: true`; traffic cells retain their individual outcomes.
- [verification-verdict.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-final-verification-20261016/verification-verdict.json): independent final verification, `PASS`.
- [power-restoration-verdict.json](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-power-restoration-20261016/power-restoration-verdict.json): `PASS`, ten original VM power states restored. This is not a claim of full resource teardown.
