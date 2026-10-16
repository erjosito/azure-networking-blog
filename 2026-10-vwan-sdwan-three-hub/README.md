# Microsoft or customer backbone? Three Virtual WAN routing designs tested

Choosing a backbone is a two-sided routing decision. Azure must select the right exit from a secured Virtual WAN hub, and the customer router must select the intended onward path. Hub routing preference alone cannot align those decisions.

This three-hub lab compares a Microsoft-backbone design with two customer-backbone approaches. **The Microsoft-backbone design selected remote hubs for the measured EU/Japan DC routes. The ASPath customer-backbone design selected local attachments and retained the customer mesh. The ExpressRoute-HRP customer-backbone attempt did not achieve that local selection at EU or US.** Only the Microsoft-backbone design has workload traffic measurements, and even those show DC-to-DC regressions.

**A means Microsoft backbone preferred. B1 and B2 are two approaches intended to prefer the customer backbone.**

| Design | Intended preference | Hub routing preference, all three hubs | NVA policy and extra prepends | Measured result |
|---|---|---|---|---|
| **A** | Microsoft backbone | `ASPath` | Foreign DCs and spokes from Azure at LP `400`; three extra nonlocal DC export prepends on EU/US/JP | Remote-hub selections for the measured EU/Japan routes; JP workload and EU spoke TCP/ICMP pass both ways, but DC-to-DC failures remain |
| **B1** | Customer backbone through ExpressRoute/VPN HRP | `ExpressRoute` tested; VPN HRP **not measured** | Azure imports only spokes; regional preference; two extra nonlocal DC prepends on EU/US, none on JP | EU/US still select remote Japan hub; **intended customer-backbone selection not demonstrated** |
| **B2** | Customer backbone through ASPath and prepend control | `ASPath` | Same spoke-only import policy as B1; **zero extra** nonlocal DC prepends on EU/US, none on JP | Local EU/US BGP attachments and JP VPN win the measured DC choices; **route-control result only**, no new traffic tests |

B2 is about controlling prepends, not adding them everywhere: removing the extra EU/US prepends makes the local offer shorter than the remote-hub alternative. A is a combined import, local-preference, export, and HRP design, not a prepend-only threshold experiment.

The [documented HRP ordering](https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference) explains the intended distinction: **ExpressRoute and VPN prefer local-hub routes before comparing AS-path lengths; ASPath compares path length first and uses locality as a tie-breaker.** B1 tests the former approach, but its measured EU/US result below did not reproduce that intended local preference.

All measurements are from **16 October 2026**. The [references and exact evidence map](./references.md) identify the three matched captures, including each design's complete EU, JP and CN BIRD configurations. The public [A/B comparison report](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/ab-design-comparison-20261016/README.md) links the published source evidence.

## One topology, two possible backbones

![Three secured Azure hubs and a separate four-site private WireGuard mesh](./assets/topology.svg)

The upper fabric is Azure Standard Virtual WAN: hubs in **West Europe, North Central US, and Japan East**, with one Standard Azure Firewall each. All three use **PrivateTraffic-only routing intent**, not Internet routing intent. The lower fabric is a full six-link WireGuard mesh between four Linux/BIRD routers, over a peered Azure VNet underlay. It models the customer inter-DC backbone; it is not the managed Azure interhub mesh.

BGP means Border Gateway Protocol, ASN identifies an autonomous system, NVA means network virtual appliance, and LP below is the explicit `BGP.local_pref` attribute. DC labels are synthetic on-premises networks modeled in Azure.

| Site | Router / ASN | Synthetic DC / probe | Azure spoke / probe | Virtual WAN attachment |
|---|---|---|---|---|
| EU | `10.210.0.4`, ASN `65011`, transit `10.210.0.0/24` | `10.110.0.0/24`, `.10` | `10.10.0.0/24`, `.10` | Ordinary peered-VNet `HubBgpConnection`, two eBGP peers |
| US | `10.220.0.4`, ASN `65012`, transit `10.220.0.0/24` | `10.120.0.0/24`, `.10` | `10.20.0.0/24`, `.10` | Ordinary peered-VNet `HubBgpConnection`, two eBGP peers |
| JP | `10.130.0.4`, ASN `65013` | `10.130.0.0/24`, `.10` | `10.30.0.0/24`, `.10` | Two strongSwan IPsec tunnels and two eBGP peers |
| CN | `10.140.0.4`, ASN `65014` | `10.140.0.0/24`, router `.4` also serves as probe | None | Customer mesh only |

EU/US are not integrated vendor SD-WAN VPN gateways. This describes their actual attachment, not a claim that a particular HRP mode is generally unsupported for NVAs. Japan's BGP local address is `169.254.21.1`; its Azure peers are `169.254.21.2` and `.6`, reached over `xfrm41` and `xfrm42`.

The logical CN site is hosted in Japan East, not sovereign China. It has **no direct Azure hub attachment** and must choose a mesh ingress. There is **no ExpressRoute circuit** in this lab: `ExpressRoute` is an HRP policy name. The hub ASN is `65515`; interhub advertisements add `65520 65520`.

Six unique mesh adjacencies plus six Azure-facing adjacencies make **12 unique BGP adjacencies**, represented by **18 BIRD endpoint entries** because each customer mesh link is configured at both ends.

### How to read the tables

Each design includes the **entire EU and JP `table2.txt` firewall capture**, all ten entries, not just the destination that supports the headline. The displayed columns are the complete text capture's `Prefix`, `ASPath`, and `NextHopType`; full API JSON is linked in [references.md](./references.md).

Each NVA table includes **all seven DC/spoke prefixes** from that design's `selected-routes.json`, checked against its raw BIRD route output. The next-hop column is the actual `BGP.next_hop`, including any import rewrite. **BIRD resolution** shows the gateway or interface resolved by BIRD, not proof of successful Linux kernel installation. `n/a` means the attribute is absent on a static `own_dc` route; `empty` represents a blank firewall AS path.

`*` is the normal selected BIRD route marker. **`!` means the selected route has a kernel-export failure flag.** It is not a healthy-FIB success marker. These are selections and captured resolution, not packet-capture proof of physical traversal.

## A: Microsoft backbone preferred

The intended path is local workload or spoke, local Azure attachment, managed interhub backbone, remote attachment, and destination. To make that preference meaningful, the NVAs must accept and prefer Azure's foreign-DC routes rather than continuing to select their mesh.

### A policy: accept Azure alternatives, prefer them, prevent feedback

All three Azure-facing NVAs accept **foreign DC prefixes, never their own DC**, plus all three spokes. Accepted Azure routes get LP `400`. Existing next-hop rewriting, communities, own-route origination, and mesh policies remain in place.

The captured EU Azure import body, used on both EU Azure peers, is:

```bird
if net ~ [10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24, 10.10.0.0/24, 10.20.0.0/24, 10.30.0.0/24] then {
  bgp_next_hop = 10.210.0.1;
  bgp_community = -empty-;
  bgp_community.add((65011, 1));
  bgp_local_pref = 400;
  accept;
}
reject;
```

Japan's captured `azure_0` import body differs in the excluded own DC, next hop, and site community:

```bird
if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.140.0.0/24, 10.10.0.0/24, 10.20.0.0/24, 10.30.0.0/24] then {
  bgp_next_hop = 169.254.21.2;
  bgp_community = -empty-;
  bgp_community.add((65013, 1));
  bgp_local_pref = 400;
  accept;
}
reject;
```

Japan's `azure_1` uses `169.254.21.6`. The shared regional mesh preference remains:

```bird
function regional_preference(int ingress) {
  if (net = 10.10.0.0/24 && ingress = 65011) ||
     (net = 10.20.0.0/24 && ingress = 65012) ||
     (net = 10.30.0.0/24 && ingress = 65013) then
    bgp_local_pref = 300;
  else bgp_local_pref = 100;
}
```

Thus Azure LP `400` outranks a regional spoke's mesh LP `300` and ordinary mesh LP `100`. EU/US/JP each add **three extra own-AS copies** to nonlocal DC exports, but not to their own DC. Japan's complete export filter is:

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

EU uses the same guard, excludes its own `10.110.0.0/24` from prepending, and calls `bgp_path.prepend(65011)` three times. US applies the corresponding `65012` policy.

The **source guard matters to interpretation**. Only `own_dc` or `mesh_*` DC routes can be exported to Azure. Once an Azure-learned foreign DC route becomes best, its former local foreign-DC advertisement is suppressed by that guard. The remaining lower-priority mesh candidate does not imply that both Azure-facing advertisements remain present. **A measures combined policy, not an isolated prepend threshold**, and no fallback test was run.

### A: complete EU firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.110.0.0/24` | `65011` | HubBgpConnection |
| `10.210.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | empty | Virtual Network Connection |
| `10.140.0.0/24` | `65011-65011-65011-65011-65014` | HubBgpConnection |
| `10.130.0.0/24` | `65520-65520-65013` | Remote Hub |
| `10.30.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.120.0.0/24` | `65520-65520-65012` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

### A: complete JP firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.140.0.0/24` | `65013-65013-65013-65013-65014` | VPN_S2S_Gateway |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.120.0.0/24` | `65520-65520-65012` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `10.110.0.0/24` | `65520-65520-65011` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

The default `Internet` rows are retained because these are full captures. Their presence is not evidence of Internet routing intent or an Internet traffic test.

### A: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | n/a | via `10.210.0.1` on `eth0` | n/a | n/a | `*` |
| `10.120.0.0/24` | `azure_0` | `10.210.0.1` | via `10.210.0.1` on `eth0` | `65515 65520 65520 65012` | 400 | `*` |
| `10.130.0.0/24` | `azure_0` | `10.210.0.1` | via `10.210.0.1` on `eth0` | `65515 65520 65520 65013` | 400 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | dev `wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | via `10.210.0.1` on `eth0` | `65515` | 400 | `*` |
| `10.20.0.0/24` | `azure_0` | `10.210.0.1` | via `10.210.0.1` on `eth0` | `65515 65520 65520` | 400 | `*` |
| `10.30.0.0/24` | `azure_0` | `10.210.0.1` | via `10.210.0.1` on `eth0` | `65515 65520 65520` | 400 | `*` |

### A: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `azure_1` | `169.254.21.6` | via `169.254.21.6` on `xfrm42` | `65515 65520 65520 65011` | 400 | `!` |
| `10.120.0.0/24` | `azure_1` | `169.254.21.6` | via `169.254.21.6` on `xfrm42` | `65515 65520 65520 65012` | 400 | `!` |
| `10.130.0.0/24` | `own_dc` | n/a | dev `eth0` | n/a | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | dev `wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_1` | `169.254.21.6` | via `169.254.21.6` on `xfrm42` | `65515 65520 65520` | 400 | `!` |
| `10.20.0.0/24` | `azure_1` | `169.254.21.6` | via `169.254.21.6` on `xfrm42` | `65515 65520 65520` | 400 | `!` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | via `169.254.21.6` on `xfrm42` | `65515` | 400 | `!` |

### A: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | dev `wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | dev `wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | dev `wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | n/a | dev `eth0` | n/a | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | dev `wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | dev `wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | dev `wgjpcn` | `65013 65515` | 300 | `*` |

**US symmetry:** A's US firewall also selects JP through `Remote Hub`, path `65520-65520-65013`; its NVA selects `azure_1`, path `65515 65520 65520 65013`, LP `400`. The source captures include the complete US view.

**CN is an explicit exception to an all-Microsoft interpretation.** EU and JP still select `mesh_cn` for the CN DC; their firewalls show local re-advertisements of CN. CN itself reaches each DC by its direct mesh peer and each Azure spoke through that spoke's regional mesh ingress at LP `300`. A is Microsoft-preferred for the measured directly attached regions, not a claim that every DC path uses the Microsoft backbone.

### A's workload forwarding requirement and measured limits

A includes a five-prefix Japan workload-subnet user-defined route table, or UDR. The next hop is `10.130.0.4` for EU DC `10.110.0.0/24`, US DC `10.120.0.0/24`, and spokes `10.10.0.0/24`, `10.20.0.0/24`, `10.30.0.0/24`. This is a workload-forwarding requirement in the measured design, not something HRP configures.

The UDR deliberately excludes `10.140.0.0/24`: CN `.4` is a WireGuard outer transport endpoint, so redirecting that prefix back through the JP router on the shared subnet would loop outer transport. No IPsec or WireGuard configuration change is part of A's policy.

The existing A traffic results are below. Each cell is **TCP / ICMP**. TCP means an HTTP `200` response from the synthetic private port `5201` listener, not a throughput benchmark. The firewall policy permits these private TCP and ICMP probes.

| Source -> destination | A result |
|---|---|
| EU spoke `10.10.0.10` -> JP workload `10.130.0.10` | PASS / PASS |
| EU spoke `10.10.0.10` -> JP router `10.130.0.4` | PASS / PASS |
| EU spoke `10.10.0.10` -> CN router `10.140.0.4` | PASS / PASS |
| EU DC `10.110.0.10` -> JP workload `10.130.0.10` | **FAIL / FAIL** |
| EU DC `10.110.0.10` -> JP router `10.130.0.4` | **FAIL / FAIL** |
| JP workload `10.130.0.10` -> EU DC `10.110.0.10` | **FAIL / PASS** |
| JP workload `10.130.0.10` -> EU spoke `10.10.0.10` | PASS / PASS |

The Japan workload and EU spoke passed in both initiated directions. **DC-to-DC regressions remain; this is not universal end-to-end success.** A router probe is not a substitute for its workload.

Japan's `!` flags also remain unresolved. Captured kernel routes and lookups contain the intended XFRM paths, but BIRD diagnostics include `strange next-hop` and `File exists`. **The underlying kernel-export issue was not remediated.** Selected BIRD routes plus a successful probe do not establish an unconditionally healthy forwarding information base, or FIB, or a complete physical-path trace.

## B1: customer backbone through ExpressRoute/VPN HRP

The intended path from an Azure spoke to a foreign DC is local secured hub, local customer attachment, and customer mesh to the destination. B1 tests whether the HRP locality preference supplies that local exit while the NVAs retain the mesh.

**Only `ExpressRoute` HRP was measured**, on all three hubs. VPN HRP is an unmeasured alternative, not an equivalent validated result. EU/US use **two extra nonlocal DC prepends**, Japan none. B1 retains spoke-only Azure imports, so foreign DCs stay on the customer mesh inside the NVAs.

### B1 policy and the negative result

The captured EU Azure import body, shared with B2, is:

```bird
if net ~ [10.10.0.0/24, 10.20.0.0/24, 10.30.0.0/24] then {
  bgp_next_hop = 10.210.0.1;
  bgp_community = -empty-;
  bgp_community.add((65011, 1));
  regional_preference(65011);
  accept;
}
reject;
```

The regional-preference function is the same one shown for A. EU's own spoke comes from Azure at LP `300`; foreign spokes can prefer their regional mesh ingress at LP `300` over a nonregional Azure import at `100`. Foreign DC imports from Azure are rejected.

The EU B1 export filter is:

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
    if net != 10.110.0.0/24 then {
      bgp_path.prepend(65011);
      bgp_path.prepend(65011);
    }
        accept;
  }
  reject;
}
```

US uses two `65012` prepends. JP's nonlocal exports have **no extra prepends**. In both B designs, Japan's `azure_0` import body is:

```bird
if net ~ [10.10.0.0/24, 10.20.0.0/24, 10.30.0.0/24] then {
  bgp_next_hop = 169.254.21.2;
  bgp_community = -empty-;
  bgp_community.add((65013, 1));
  regional_preference(65013);
  accept;
}
reject;
```

Its `azure_1` uses `.6`. JP exports DCs with the same `own_dc` / `mesh_*` source guard, but no prepend statements.

For Japan's prefix, BIRD's EU export view prints `65011 65011 65013`. Native eBGP automatically inserts one more local ASN, so the **offered local wire path** is:

```text
EU BIRD export view: 65011 65011 65013
EU offered path:    65011 65011 65011 65013   (length 4)
Remote hub path:    65520 65520 65013         (length 3)
```

**The remote Japan hub still wins at both EU and US.** The observed length difference is **one**, not two. The documented HRP race-condition caveat for a local route at least two entries longer does **not explain this observation**. The capture does not establish another root cause, an unsupported-NVA rule, or a universal ER/VPN behavior.

### B1: complete EU firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.110.0.0/24` | `65011` | HubBgpConnection |
| `10.140.0.0/24` | `65011-65011-65011-65014` | HubBgpConnection |
| `10.130.0.0/24` | `65520-65520-65013` | Remote Hub |
| `10.30.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.120.0.0/24` | `65520-65520-65012` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | empty | Virtual Network Connection |
| `0.0.0.0/0` | empty | Internet |

### B1: complete JP firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `10.140.0.0/24` | `65013-65014` | VPN_S2S_Gateway |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.110.0.0/24` | `65013-65011` | VPN_S2S_Gateway |
| `10.120.0.0/24` | `65013-65012` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

### B1: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | n/a | via `10.210.0.1` on `eth0` | n/a | n/a | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.2` | dev `wgeuus` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.6` | dev `wgeujp` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | dev `wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | via `10.210.0.1` on `eth0` | `65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.2` | dev `wgeuus` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.6` | dev `wgeujp` | `65013 65515` | 300 | `*` |

### B1: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.5` | dev `wgeujp` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.13` | dev `wgusjp` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `own_dc` | n/a | dev `eth0` | n/a | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | dev `wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.5` | dev `wgeujp` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.13` | dev `wgusjp` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | via `169.254.21.6` on `xfrm42` | `65515` | 300 | `!` |

### B1: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | dev `wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | dev `wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | dev `wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | n/a | dev `eth0` | n/a | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | dev `wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | dev `wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | dev `wgjpcn` | `65013 65515` | 300 | `*` |

**US symmetry:** US retains the remote Japan winner `65520-65520-65013`, despite offering `65012-65012-65012-65013` locally. Japan's local VPN choices for EU/US do not turn this into a successful all-region customer-backbone result. The B1 verdict is `INCONCLUSIVE`, with the intended EU local-path assertion not met and restoration recorded as true. **No B1 traffic tests were run.**

## B2: customer backbone through ASPath and prepend control

B2 retains B1's spoke-only Azure import and regional mesh policy, but sets all three hubs to `ASPath` and removes EU/US extra nonlocal prepends. Japan still adds none.

EU's captured export filter becomes:

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
        accept;
  }
  reject;
}
```

The source guard is unchanged. JP's no-prepend filter in B1 and B2 is:

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then accept;
  reject;
}
```

EU's BIRD export view of Japan is now just `65013`; automatic eBGP local-AS insertion produces `65011-65013`. At length two, that local offer is shorter than `65520-65520-65013` at length three. **The captured firewall selects the local `HubBgpConnection`**, while the EU NVA retains `mesh_jp`.

### B2: complete EU firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.110.0.0/24` | `65011` | HubBgpConnection |
| `10.140.0.0/24` | `65011-65014` | HubBgpConnection |
| `10.130.0.0/24` | `65011-65013` | HubBgpConnection |
| `10.120.0.0/24` | `65011-65012` | HubBgpConnection |
| `10.210.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | empty | Virtual Network Connection |
| `10.30.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

### B2: complete JP firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.140.0.0/24` | `65013-65014` | VPN_S2S_Gateway |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.110.0.0/24` | `65013-65011` | VPN_S2S_Gateway |
| `10.120.0.0/24` | `65013-65012` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `0.0.0.0/0` | empty | Internet |

### B2: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | n/a | via `10.210.0.1` on `eth0` | n/a | n/a | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.2` | dev `wgeuus` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.6` | dev `wgeujp` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | dev `wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | via `10.210.0.1` on `eth0` | `65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.2` | dev `wgeuus` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.6` | dev `wgeujp` | `65013 65515` | 300 | `*` |

### B2: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.5` | dev `wgeujp` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.13` | dev `wgusjp` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `own_dc` | n/a | dev `eth0` | n/a | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | dev `wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.5` | dev `wgeujp` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.13` | dev `wgusjp` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | via `169.254.21.6` on `xfrm42` | `65515` | 300 | `!` |

### B2: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | dev `wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | dev `wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | dev `wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | n/a | dev `eth0` | n/a | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | dev `wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | dev `wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | dev `wgjpcn` | `65013 65515` | 300 | `*` |

**US symmetry:** US selects JP through local `HubBgpConnection`, path `65012-65013`. JP selects EU through local VPN, `65013-65011`, and US through `65013-65012`. The customer routers retain the direct DC mesh, with regional mesh ingress for foreign Azure spokes.

**B2 route checks: PASS.** These tables establish the requested route selections, not tested end-to-end forwarding. The original B2 run verdict remains **`BLOCKED`** because its lease expired during the read-only restoration proof, not because the captured route assertions failed. Do not relabel that original verdict `PASS`. A fresh independent recovery verification subsequently returned **`PASS`**, checking exact source bytes/metadata, restored HRPs, and firewall winners. **No B2 traffic tests were run**, and JP's selected local-spoke Azure route still carries `!`.

## Why China keeps a mesh ingress in every design

CN has no Azure-facing BGP session. It learns each foreign DC directly from that site's mesh router and each spoke through its regional ingress. Its captured EU mesh import body is unchanged across A/B1/B2:

```bird
bgp_next_hop = 172.31.0.9;
if net = 10.110.0.0/24 then { bgp_community = -empty-; accept; }
if net ~ [10.10.0.0/24, 10.20.0.0/24, 10.30.0.0/24] then {
  bgp_community = -empty-;
  bgp_community.add((65011, 1));
  regional_preference(65011);
  accept;
}
reject;
```

The US/JP imports apply their corresponding regional preference. That is why CN's selected spoke paths are `65011 65515`, `65012 65515`, and `65013 65515`, each at LP `300`, in all three designs. CN's own DC is originated by `own_dc`; its mesh export permits that own DC, not foreign DC transit. The complete CN configuration is linked separately for each capture, even where unchanged.

## Observe both routing decisions

For an **unsecured** VNet connection, set `$hub`, `$rg` and `$connection` to the target hub, resource group and connection name, then use **`HubVirtualNetworkConnection` singular**:

```powershell
$connectionId = az network vhub connection show -g $rg --vhub-name $hub -n $connection --query id -o tsv
az network vhub get-effective-routes -n $hub -g $rg --resource-type 'HubVirtualNetworkConnection' --resource-id $connectionId --query 'value[].{Prefix:addressPrefixes[0], ASPath:asPath, NextHopType:nextHopType}' -o table
```

For a secured hub's **post-inspection** onward choices, query the owning hub with the actual firewall ID and **`AzureFirewalls` plural**:

```powershell
az network vhub get-effective-routes -n $hub -g $rg --resource-type 'AzureFirewalls' --resource-id $(az network vhub show -g $rg -n $hub --query 'azureFirewall.id' -o tsv) --query 'value[].{Prefix:addressPrefixes[0], ASPath:asPath, NextHopType:nextHopType}' -o table
```

Set `$hub` and `$rg` for the target hub. Wait for operation completion; an HTTP `202` alone is not a captured table. Retain full JSON as well as the compact text projection, which shows only the first address prefix per entry.

Compare with the NVA:

```bash
sudo birdc 'show route table lab4 all'
sudo birdc 'show route export azure_0 all'
sudo birdc 'show route export azure_1 all'
ip -j route show table main
ip -j route get 10.10.0.10
```

CN has no `azure_*` peers; inspect its mesh peers instead. BIRD's export view shows explicit path edits **before automatic eBGP local-AS insertion**. Count that automatic ASN when comparing an offered local path to the firewall's remote-hub path. Read `BGP.local_pref` explicitly, not the parenthesized BIRD protocol-preference display.

## Design choice and evidence boundary

- **A, Microsoft preferred:** accept and prefer Azure alternatives, keep export feedback protection, and align workload forwarding. The measured JP workload/EU spoke pair works in both directions, but DC-to-DC regressions and kernel-export flags prevent calling A a universal working design. CN remains mesh-only.
- **B1, customer preferred through ER/VPN HRP:** the actual ExpressRoute-HRP capture did **not** obtain local EU/US Japan selections. VPN HRP is unmeasured. Do not deploy the intended behavior as though this test proved it.
- **B2, customer preferred through ASPath:** zero extra EU/US nonlocal prepends produced the intended local DC exit selections while retaining the customer mesh. This is a positive route-control observation, not a traffic or failover validation.

After the B work, the four started routers were returned to their original deallocated states; probe VMs were untouched, and the live task was stopped. The independent recovery and power-restoration records are linked in [references.md](./references.md). Restoration success does not repair BIRD's kernel-export warning or convert route-control captures into forwarding tests.

No design here establishes throughput, latency, convergence time, failover/failback, universal DC-to-DC forwarding, or packet-capture proof of the physical backbone. The transferable method is narrower and more useful: **choose the intended Azure exit and the intended NVA onward path separately, then validate workload forwarding rather than inferring it from either table.**
