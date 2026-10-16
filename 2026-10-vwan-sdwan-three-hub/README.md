# Virtual WAN backbone-first routing needs more than hub routing preference

Your Azure Firewall can prefer the Virtual WAN backbone while your network virtual appliance still sends the same destination over its private mesh. Changing hub routing preference does not change the appliance's import filters, BGP local preference, or the workload's return route.

That split was visible in this three-hub secured Virtual WAN lab. The EU and US firewalls selected Japan through a remote hub, but their BIRD routers still selected the direct WireGuard mesh. A combined Azure import, local-preference, and export policy changed the appliance selections. Adding a scoped Japan workload route table then made **Japan workload to EU Azure spoke, and EU Azure spoke to Japan workload, pass both TCP and ICMP probes**.

That is a useful result, not an all-green reference design: DC-to-DC tests regressed, and Japan's selected BIRD routes carried kernel-installation failure flags. The lesson is to align four decisions, then test both directions:

1. **Azure selection:** which attachment or remote hub wins after inspection?
2. **NVA selection:** is the Azure route accepted, and does it beat the mesh?
3. **Export protection:** can an Azure-learned route feed back into Azure?
4. **Workload forwarding:** does the workload actually use the intended router on the return path?

The measurements below were captured on **16 October 2026**. This post was written offline from those captures; no new cloud tests were run for publication. The [reference and evidence map](./references.md) links the complete BIRD configurations, paired firewall outputs, traffic results, and restoration verdicts. The companion [source report and captured evidence](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/backbone-policy-design-20261016/README.md) are published in the public lab repository.

## The topology: two fabrics, three Azure attachments

![Three secured Azure hubs above a four-site WireGuard mesh, with ordinary peered-VNet BGP attachments in EU and US and an IPsec attachment in Japan](./assets/topology.svg)

There are two distinct connectivity layers:

- **Azure fabric:** Standard Virtual WAN hubs in West Europe, North Central US, and Japan East, each with a Standard Azure Firewall and **PrivateTraffic-only routing intent**. There is no Internet routing intent. The firewall policy permits the private TCP port `5201` and ICMP used by the probes.
- **Private mesh:** four Linux/BIRD routers connected by six WireGuard links over a peered Azure VNet underlay. This models an inter-DC mesh. It is not the managed Virtual WAN interhub mesh.

Here, BGP is Border Gateway Protocol, an ASN identifies a BGP autonomous system, and NVA means network virtual appliance. "DC" labels synthetic on-premises networks hosted in Azure for the experiment, not actual external data centers.

| Site | Hub region | NVA ASN and address | Synthetic DC and probe | Azure spoke and probe | Azure attachment |
|---|---|---|---|---|---|
| EU | West Europe | `65011`, `10.210.0.4` in transit `10.210.0.0/24` | `10.110.0.0/24`, `10.110.0.10` | `10.10.0.0/24`, `10.10.0.10` | Peered-VNet `HubBgpConnection`, two eBGP peers |
| US | North Central US | `65012`, `10.220.0.4` in transit `10.220.0.0/24` | `10.120.0.0/24`, `10.120.0.10` | `10.20.0.0/24`, `10.20.0.10` | Peered-VNet `HubBgpConnection`, two eBGP peers |
| JP | Japan East | `65013`, `10.130.0.4` | `10.130.0.0/24`, `10.130.0.10` | `10.30.0.0/24`, `10.30.0.10` | Two strongSwan IPsec tunnels and two BGP peers |
| CN | No attached hub; hosted in Japan East | `65014`, `10.140.0.4` | `10.140.0.0/24`, router doubles as probe `.4` | None | Mesh only, no direct Virtual WAN attachment |

EU and US are **ordinary peered-VNet BGP-connected NVAs**, not integrated vendor SD-WAN appliances with VPN-gateway semantics. Japan uses Azure peers `169.254.21.2` and `169.254.21.6`, local BGP address `169.254.21.1`, and Linux XFRM interfaces `xfrm41` and `xfrm42`.

The six unique mesh adjacencies plus six Azure-facing adjacencies make **12 unique BGP adjacencies**. The mesh is configured at both endpoints, so the four BIRD configurations contain **18 endpoint entries**, not 18 unique links. Virtual WAN's hub ASN is `65515`; interhub advertisements add `65520 65520`.

**There is no ExpressRoute circuit in this lab.** `ExpressRoute` below is the name of a hub routing preference setting, not a description of deployed connectivity. "CN" is a logical site name, not a sovereign China region.

### Read the diagram in three stages

The same physical topology supports all three measured states:

| State | Hub routing preference, EU / US / JP | NVA policy | Japan workload subnet UDR |
|---|---|---|---|
| Baseline | `ASPath` / `ASPath` / `ExpressRoute` | Azure imports only spokes; mesh regional-ingress preference retained | No route-table association |
| NVA policy only | `ASPath` / `ASPath` / `ASPath` | Accept foreign DCs plus spokes from Azure at local preference `400`; preserve export guard; add JP nonlocal prepends | None |
| NVA policy + JP UDR | `ASPath` / `ASPath` / `ASPath` | Same as previous state | Five prefixes to `10.130.0.4` |

In the baseline, an appliance can choose a lower-diagram mesh link even while the firewall chooses the upper-diagram Azure interhub route. In the policy states, the BIRD selections move toward the Azure attachments. The UDR state additionally controls the Japan workload subnet's forwarding toward those selected routes. Arrows and route selections describe path intent, not packet-capture proof of physical traversal.

## Baseline: the firewall and the appliance disagree

Hub routing preference, or HRP, influences Azure's route selection. It does not reach into BIRD.

The baseline had EU and US HRP set to `ASPath`, and Japan set to `ExpressRoute`. EU and US already added **three extra copies of their own ASN** when exporting an allowed DC route other than their own DC. Japan did not add those prepends.

At both EU and US firewalls, the Japan DC prefix `10.130.0.0/24` won through **Remote Hub**, with AS path `65520-65520-65013`. At the Japan firewall, Japan's own prefix won through **VPN_S2S_Gateway**, path `65013`.

But EU and US BIRD selected `mesh_jp`, path `65013`, local preference `100`, for that same Japan prefix. This was not simply BIRD ignoring a better Azure route: the original Azure-facing import filters **accepted only the three Azure spoke prefixes, not foreign DC prefixes**.

On Japan, the EU spoke was accepted from Azure, but regional mesh policy preferred EU's mesh advertisement at local preference `300`. Other BGP routes used `100`.

| Observation point | Destination | Baseline selected source | AS path | BGP local preference |
|---|---|---|---|---|
| EU firewall | JP DC `10.130.0.0/24` | Remote Hub | `65520-65520-65013` | Not exposed here |
| US firewall | JP DC `10.130.0.0/24` | Remote Hub | `65520-65520-65013` | Not exposed here |
| JP firewall | EU DC `10.110.0.0/24` | VPN_S2S_Gateway | `65013-65011` | Not exposed here |
| EU BIRD | JP DC `10.130.0.0/24` | `mesh_jp` | `65013` | `100` |
| US BIRD | JP DC `10.130.0.0/24` | `mesh_jp` | `65013` | `100` |
| JP BIRD | EU DC `10.110.0.0/24` | `mesh_eu` | `65011` | `100` |
| JP BIRD | EU spoke `10.10.0.0/24` | `mesh_eu` | `65011 65515` | `300` |

Here is the EU BIRD baseline excerpt:

```text
10.130.0.0/24        unicast [mesh_jp 09:06:16.250 from 172.31.0.6] * (100) [AS65013i]
	dev wgeujp
	Type: BGP univ
	BGP.origin: IGP
	BGP.as_path: 65013
	BGP.next_hop: 172.31.0.6
	BGP.local_pref: 100
```

### Count the automatic ASN, not just the explicit prepends

The baseline EU export of Japan's prefix showed:

```text
BGP.as_path: 65011 65011 65011 65013
```

That is the path printed by BIRD's export view **before native eBGP inserts the local ASN**. The resulting wire advertisement contains four copies of `65011`, followed by `65013`, a total path length of five:

```text
Explicit export view: 65011 65011 65011 65013
eBGP wire path:       65011 65011 65011 65011 65013
Remote hub path:      65520 65520 65013
```

US behaves equivalently with `65012`. Those existing prepends make the local re-advertisement longer than the remote Japan VPN-origin route in this baseline. They do not make the NVA import that remote route, and they do not override the NVA's local preference.

## The combined NVA policy: accept, prefer, protect

Both policy variants set all three hubs to `ASPath`. The NVA changes are implemented in the reversible [`design_backbone.py`](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/deploy/design_backbone.py) transform.

### 1. Accept foreign DCs from Azure, but never your own DC

Each of the three Azure-facing NVAs expands the import allowlist to include the **other three DC prefixes** and **all three spokes**. Its own DC remains excluded.

This is the EU import body, applied to both Azure peers:

```bird
if net ~ [10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24,
          10.10.0.0/24, 10.20.0.0/24, 10.30.0.0/24] then {
  bgp_next_hop = 10.210.0.1;
  bgp_community = -empty-;
  bgp_community.add((65011, 1));
  bgp_local_pref = 400;
  accept;
}
reject;
```

The complete configurations matter: this is not a generic replacement filter to paste into any appliance. US retains its own next-hop rewriting and community handling. Japan retains the appropriate `169.254.21.2` or `.6` next hop for each Azure peer. Own-route origination and existing mesh policy remain unchanged.

### 2. Prefer Azure with local preference 400

BGP local preference is a router's policy for ranking paths. Higher is preferred here. Setting imported Azure routes to `400` makes them outrank the regional mesh spoke preference of `300` and ordinary mesh routes at `100`, despite a longer AS path.

For example, EU now selects:

```text
10.130.0.0/24        unicast [azure_0 10:21:01.098 from 10.250.0.69] * (100/?) [AS65013e]
	via 10.210.0.1 on eth0
	Type: BGP univ
	BGP.origin: EGP
	BGP.as_path: 65515 65520 65520 65013
	BGP.next_hop: 10.210.0.1
	BGP.local_pref: 400
```

The parenthesized `(100/?)` is **not** the `BGP.local_pref` value. Read the explicit attribute line.

### 3. Keep the export guard, and account for withdrawal

The existing Azure export guard permits DC routes only when their source is `own_dc` or `mesh_*`. It does **not** allow an `azure_*`-learned DC route to feed back into Azure.

EU and US preserve their existing prepends. Japan adds three extra `65013` prepends for nonlocal DC exports:

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
    if net != 10.130.0.0/24 then {
      bgp_path.prepend(65013);
      bgp_path.prepend(65013);
      bgp_path.prepend(65013);
    }
    accept;
  }
  reject;
}
```

**This creates an important experimental limitation.** Once an Azure-learned foreign DC route becomes the NVA's best route, the existing guard rejects that route for export back to Azure. Its previous local foreign-DC advertisement is withdrawn. The lower-priority mesh candidate can remain in BIRD without remaining advertised to Azure.

Consequently, the observed final state is the result of **combined import, local-preference, export, and HRP policy**. It does not isolate a prepend-only effect, and it does not prove that two competing advertisements remain present at steady state. Keeping the mesh candidate is also not proof of usable backup: no failure or convergence test was performed.

## Matched observations after the policy

Both policy variants captured the same selections below. Each state has two matching firewall snapshots; the NVA configurations, BIRD routes, exports, and traffic captures are preserved alongside them.

| Observation point | Destination | Baseline | Both policy variants |
|---|---|---|---|
| EU firewall | JP DC | Remote Hub, `65520-65520-65013` | Remote Hub, `65520-65520-65013` |
| US firewall | JP DC | Remote Hub, `65520-65520-65013` | Remote Hub, `65520-65520-65013` |
| JP firewall | EU DC | VPN_S2S_Gateway, `65013-65011` | Remote Hub, `65520-65520-65011` |
| EU BIRD | JP DC | `mesh_jp`, `65013`, LP `100` | `azure_0`, `65515 65520 65520 65013`, LP `400` |
| US BIRD | JP DC | `mesh_jp`, `65013`, LP `100` | `azure_1`, `65515 65520 65520 65013`, LP `400` |
| JP BIRD | EU DC | `mesh_eu`, `65011`, LP `100` | `azure_1`, `65515 65520 65520 65011`, LP `400`, **`!`** |
| JP BIRD | EU spoke | `mesh_eu`, `65011 65515`, LP `300` | `azure_1`, `65515 65520 65520`, LP `400`, **`!`** |

Notice what did **not** change: EU and US firewalls already selected the remote Japan hub. The meaningful change there was on the appliance. The extra leading `65515` in BIRD is the Azure-facing eBGP hop; the firewall view and appliance view are different observation points, not contradictory AS paths.

### Japan's `!` is a warning, not a success marker

Japan's BIRD route excerpt in the policy-only state is:

```text
10.110.0.0/24        unicast [azure_1 10:23:04.846] ! (100/?) [AS65011e]
	via 169.254.21.6 on xfrm42
	Type: BGP univ
	BGP.origin: EGP
	BGP.as_path: 65515 65520 65520 65011
	BGP.next_hop: 169.254.21.6
	BGP.local_pref: 400
```

The `!` denotes a **kernel-installation failure**, not an ordinary selected-route `*`. The capture parser explicitly handles both markers, but a selected BIRD route must not be equated with a healthy forwarding information base, or FIB.

At the same time, the captured Linux main table in both variants contains:

```text
10.10.0.0/24  via 169.254.21.6 dev xfrm42 proto bird metric 80
10.110.0.0/24 via 169.254.21.6 dev xfrm42 proto bird metric 80
```

These two lines are a compact rendering of the JSON kernel snapshot. A lookup for `10.10.0.10` also resolves through `169.254.21.6` on `xfrm42`. That supports the intended forwarding direction, but it does not erase the installation flag. Captured BIRD diagnostics include `strange next-hop` and `File exists`; the underlying issue was **not remediated** in this experiment, and these observations do not establish a definitive root cause.

## The workload route table changes the traffic result

The second variant adds one temporary, experiment-owned user-defined route table to the Japan workload subnet. All five routes use next-hop type `VirtualAppliance` and next-hop address `10.130.0.4`:

| Destination | Purpose |
|---|---|
| `10.110.0.0/24` | EU DC |
| `10.120.0.0/24` | US DC |
| `10.10.0.0/24` | EU spoke |
| `10.20.0.0/24` | US spoke |
| `10.30.0.0/24` | JP spoke |

It deliberately **excludes `10.140.0.0/24`**. CN router `10.140.0.4` is also a WireGuard outer transport endpoint. Sending that prefix back to the Japan router with a shared workload-subnet UDR would loop the router's outer transport. Overlay payload policy must not accidentally redirect the overlay's own transport endpoint.

No IPsec, strongSwan, or WireGuard configuration was changed. After capture, the original no-route-table association was restored and only the experiment's route table was deleted.

### All seven directional probe cells

Each cell below is **TCP / ICMP**. TCP was an HTTP probe to the private listener on port `5201`, not a throughput test. A router-address probe is not a substitute for a workload-address probe.

| Source -> destination | Baseline | NVA policy only | NVA policy + JP UDR |
|---|---|---|---|
| EU spoke `10.10.0.10` -> JP workload `10.130.0.10` | FAIL / FAIL | FAIL / FAIL | **PASS / PASS** |
| EU spoke `10.10.0.10` -> JP router `10.130.0.4` | FAIL / PASS | PASS / PASS | PASS / PASS |
| EU spoke `10.10.0.10` -> CN router `10.140.0.4` | FAIL / PASS | PASS / PASS | PASS / PASS |
| EU DC `10.110.0.10` -> JP workload `10.130.0.10` | PASS / PASS | PASS / PASS | **FAIL / FAIL** |
| EU DC `10.110.0.10` -> JP router `10.130.0.4` | PASS / PASS | **FAIL / FAIL** | FAIL / FAIL |
| JP workload `10.130.0.10` -> EU DC `10.110.0.10` | PASS / PASS | PASS / PASS | **FAIL / PASS** |
| JP workload `10.130.0.10` -> EU spoke `10.10.0.10` | FAIL / FAIL | FAIL / FAIL | **PASS / PASS** |

The last column demonstrates the requested **modeled on-premises workload to Azure spoke direction**, as well as the reverse initiated direction, for Japan and EU. In those two successful TCP captures, the HTTP probe returned `200`.

It also shows why the result cannot be called a complete backbone-first design. The UDR variant loses the previously working EU DC to Japan workload cell, and Japan workload to EU DC retains only ICMP success. Even policy-only breaks EU DC to Japan router. Successful router probes and successful selected-route checks cannot hide those regressions.

Workload forwarding must align with the desired forward and return paths. The transition supports that design lesson; it does not supply full packet-trace proof of symmetry or prove the physical underlay traversed by every successful probe.

## Collect the right routes in a secured hub

For an unsecured hub connection, use the hub effective-route API with the **`HubVirtualNetworkConnections`** resource type and the actual connection resource ID. In a secured hub with private routing intent, a connection view or a route pointing to the firewall is not the complete post-inspection answer.

For the firewall's onward destination choices, query the **owning hub** with the actual Azure Firewall resource ID and the **plural `AzureFirewalls`** resource type. This PowerShell command is the relevant diagnostic pattern:

```powershell
az network vhub get-effective-routes -n $hub -g $rg --resource-type 'AzureFirewalls' --resource-id $(az network vhub show -g $rg -n $hub --query 'azureFirewall.id' -o tsv) --query 'value[].{Prefix:addressPrefixes[0], ASPath:asPath, NextHopType:nextHopType}' -o table
```

Set `$hub` and `$rg` to the hub and resource group you intend to inspect. The nested `vhub show` resolves the firewall identity; it does not retrieve routes itself. Wait for the effective-route operation to complete. An HTTP `202` acceptance alone is not a captured route table. For a full archive, also retain unprojected JSON rather than only the first address prefix selected by this compact query.

Compare that result with the NVA's routing and export views:

```bash
sudo birdc 'show route table lab4 all'
sudo birdc 'show route export azure_0 all'
sudo birdc 'show route export azure_1 all'
ip -j route show table main
ip -j route get 10.10.0.10
```

These are reader diagnostics, not commands run anew for this post. Inspect the source protocol, explicit `BGP.local_pref`, full path, next-hop rewrite, export eligibility, and kernel state together. The [full config matrix](./references.md#complete-bird-configurations) makes those comparisons possible for all four routers in all three states.

## HRP is a policy input, not a universal local-wins rule

[Microsoft's HRP documentation](https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference) describes `AS Path` as preferring the shortest path before local-versus-remote preference, with a specific exception for remote ExpressRoute-learned routes. It describes ExpressRoute and VPN preferences as favoring local connections earlier.

But the same documentation explicitly warns of an **ER/VPN preference race condition**: a remote route may win when the local path is **two or more AS-path entries longer**. Do not turn the nominal ordering into an unconditional "local always wins" guarantee, particularly when deliberately lengthening local advertisements.

This post is **not a completed three-HRP benchmark**. A separate HRP matrix attempt was inconclusive because of capture parsing; a later attempt stopped on transient Japan BGP hold expiry. Both were restored. `VpnGateway` was not run. The comparison used here is the matched baseline and two fully captured combined-policy variants, not an isolated proof of every HRP mode or a new confirmation that ExpressRoute preference chooses a longer local path.

## What the experiment establishes, and what remains open

**Established by the matched captures:**

- A firewall remote-hub winner can coexist with an NVA mesh winner for the same prefix.
- Allowing foreign DC imports and assigning Azure local preference `400`, with export protection intact, changed the recorded NVA selections to Azure.
- Adding the five-route Japan UDR made the Japan workload and EU spoke pass TCP and ICMP probes in both initiated directions.
- The combined experiment restored its starting configuration. Independent final verification passed. A separate power-restoration verdict confirms all **ten originally deallocated VMs returned to deallocated**. Resources were not all deleted.

**Not established:**

- A universally working all-DC design, or remediation of Japan's BIRD installation warnings.
- A prepend-only causal result or persistent dual competing advertisements.
- Tested mesh fallback, failure convergence, latency, throughput, or a complete HRP benchmark.
- Packet-capture proof of the physical interhub path or complete flow symmetry.

The experiment's `PASS` verdict means the specified selections were measured and restoration succeeded. It does **not** turn failed traffic cells into passes.

If you want backbone-first routing, start by asking four separate questions: **What does Azure select? What does the NVA accept and prefer? What can it export back? Where does the workload send the return packet?** HRP answers only part of the first question.

## References

See [references.md](./references.md) for the state-by-state evidence map, complete configurations, collector and parser sources, official documentation, and the restoration records.
