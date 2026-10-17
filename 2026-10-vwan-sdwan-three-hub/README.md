# Microsoft or customer backbone? Three Virtual WAN routing designs tested

**A prefers Microsoft's backbone; B1 and B2 prefer the customer backbone.** Azure's hub exit selection and the NVA's onward selection must agree. This rerun enables branch-to-branch at WAN level and on all three hubs and measures both routes and workload forwarding.

The matched mixed-setting and all-enabled baselines have identical DC-prefix firewall winners and **0 changed traffic outcomes out of 42 directional cells**. WAN-level B2B was already enabled; only Japan's hub flag changes from false to true. Original NVA sources, metadata, HRPs and PrivateTraffic routing intent are held constant. This isolates the flag for the baseline; it does not prove that the flag is irrelevant for every route history or supported topology.

**The B1 history dependency also reproduces with B2B enabled on every hub.** Under ExpressRoute HRP, EU/US initially retain remote Japan length three. Withdrawing only Japan's direct export selects local length-five paths; returning the export leaves those longer local paths selected. The separate EU length-four versus remote length-three control repeats the dependency. Source bytes/metadata and HRPs are identical between the initial and returned states. The mixed B2B flags therefore do not explain away that observation.

Traffic and routing are separate findings: B1's returned three-prepend state still passes only 28/42 TCP and 32/42 ICMP directions. VPN HRP selects longer local Japan paths in its measured state, with 32/42 TCP and 34/42 ICMP passes; that sequential control is not proof of a universal ER/VPN difference independent of route history. B2 passes 36/42 for both: all six failures are Japan workload <-> Azure spoke directions. A with the workload UDR passes 38/42 TCP and 40/42 ICMP; EU/US DC -> Japan workload fails both protocols, and the reverse initiated DC traffic fails TCP but passes ICMP. None is an all-pairs forwarding success.

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

## What the three designs configure

| Design | All-hub HRP | NVA policy |
|---|---|---|
| A: Microsoft | ASPath | Foreign DC/spoke Azure imports at LP 400; three nonlocal prepends on EU/US/JP; optional JP workload UDR measured separately |
| B1: customer | ExpressRoute; VpnGateway measured separately | Spoke-only Azure imports; three extra nonlocal EU/US prepends; JP none |
| B2: customer | ASPath | Spoke-only Azure imports; zero extra EU/US/JP prepends |

The [documented HRP ordering](https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference) prioritizes locality under ExpressRoute/VPN and path length under ASPath. The B1 initial, withdrawn and returned states below expose the measured selection history rather than assuming every HRP update recomputes the same winner.

## Forwarding results, not just routing tables

| Measured state | TCP / 42 | ICMP / 42 |
|---|---|---|
| [Mixed baseline](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-mixed-baseline-20261017/baseline/traffic-summary.json) | 28 | 32 |
| [All B2B baseline](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-enabled-baseline-20261017/baseline/traffic-summary.json) | 28 | 32 |
| [A, NVA policy only](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A/traffic-summary.json) | 36 | 36 |
| [A, plus JP workload UDR](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/traffic-summary.json) | 38 | 40 |
| [B1, ExpressRoute initial](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1/traffic-summary.json) | 28 | 32 |
| [B1, JP direct prefix withdrawn](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-withdrawn/traffic-summary.json) | 28 | 32 |
| [B1, JP direct prefix returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/traffic-summary.json) | 28 | 32 |
| [B1 one-ASN, initial](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN/traffic-summary.json) | 30 | 33 |
| [B1 one-ASN, withdrawn](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN-withdrawn/traffic-summary.json) | 30 | 33 |
| [B1 one-ASN, returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN-returned/traffic-summary.json) | 30 | 33 |
| [B1, VPN HRP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-VPN-20261017/B1-VPN/traffic-summary.json) | 32 | 34 |
| [B2, zero extra EU/US prepends](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/traffic-summary.json) | 36 | 36 |

Every measured state has full firewall effective tables for all three hubs, paired stable DC-prefix winners at least 120 seconds apart, full BIRD sources and selected/alternative routes on all four routers, and an explicitly sourced 42-direction TCP/ICMP matrix. The seven endpoints are four synthetic DCs and three Azure spokes: 12 DC-to-DC, 24 DC/spoke and six spoke-to-spoke directions. TCP requires HTTP 200 on the private port 5201 listener and matching local/remote addresses; ICMP uses source-bound ping. P/F below means TCP PASS / ICMP FAIL.

Bounded tcpdump captures on every router observe inner test packets on physical, WireGuard and XFRM interfaces; management traffic and encrypted transport payloads are not collected. The interface observations are not a throughput measurement or a complete symmetry proof. Failed SYNs/ICMP attempts can still appear in a capture. In particular, A's policy-only EU/JP DC reachability is not proof of the intended Virtual WAN path: the measured EU-to-JP DC packets appeared on EU's physical interfaces, but the expected Japan NVA/XFRM segment was not observed; the reverse initiated DC traffic was not observed on the NVAs. The peered underlay and workload routing must be considered rather than treating an HTTP success as proof of Microsoft interhub transit. `!` in a BIRD table is a kernel-export failure marker, not healthy Linux forwarding. A collector verdict of PASS means complete measurements and exact configuration closure, not 42 successful traffic directions.

## How to read the captured tables

Each design below contains the full EU and Japan firewall table, not a filtered supporting prefix. US is collected too and available in the matched evidence. EU, Japan and CN NVA tables include all seven DC/spoke prefixes. BGP next hop and BIRD resolution are distinct attributes. `n/a` means absent on a static route; `empty` means a blank firewall AS path. The primary A state includes the workload UDR; primary B1 is the returned three-prepend state.

## A: Microsoft backbone preferred

All hubs use `ASPath`. The three Azure-facing NVAs accept foreign DC and spoke routes from Azure at LP 400. EU/US/JP add three extra own-AS copies for nonlocal DC exports. The export source guard prevents feeding an Azure-learned best route back into Azure. CN remains mesh-only, so this is not an all-prefix Microsoft-only design.

The primary capture includes the five-prefix Japan workload UDR to `10.130.0.4`; the policy-only control is measured separately. The UDR covers EU/US DCs and all three Azure spokes, not CN's transport endpoint.

Matched state: [A, plus JP workload UDR](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/scenario-result.json). Full BIRD configurations: [EU](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-eu.conf), [US](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-us.conf), [JP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-jp.conf), [CN](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-cn.conf).

### A: complete EU firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.210.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | empty | Virtual Network Connection |
| `10.110.0.0/24` | `65011` | HubBgpConnection |
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
| `10.140.0.0/24` | `65013-65013-65013-65013-65014` | VPN_S2S_Gateway |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.120.0.0/24` | `65520-65520-65012` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `10.110.0.0/24` | `65520-65520-65011` | Remote Hub |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `0.0.0.0/0` | empty | Internet |

### A: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | `n/a` | `via 10.210.0.1 on eth0` | `n/a` | n/a | `*` |
| `10.120.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520 65012` | 400 | `*` |
| `10.130.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520 65013` | 400 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | `dev wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515` | 400 | `*` |
| `10.20.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520` | 400 | `*` |
| `10.30.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520` | 400 | `*` |

### A: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520 65011` | 400 | `!` |
| `10.120.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520 65012` | 400 | `!` |
| `10.130.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | `dev wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520` | 400 | `!` |
| `10.20.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520` | 400 | `!` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515` | 400 | `!` |

### A: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013 65515` | 300 | `*` |

### A: captured EU export policy

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
        if net != 10.110.0.0/24 then {
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
        }
        accept;
  }
  reject;
}
```

### A: all 42 traffic directions

| Source / destination | dc-eu | dc-us | dc-jp | cn | spoke-eu | spoke-us | spoke-jp |
|---|---|---|---|---|---|---|---|
| dc-eu | - | P/P | F/F | P/P | P/P | P/P | P/P |
| dc-us | P/P | - | F/F | P/P | P/P | P/P | P/P |
| dc-jp | F/P | F/P | - | P/P | P/P | P/P | P/P |
| cn | P/P | P/P | P/P | - | P/P | P/P | P/P |
| spoke-eu | P/P | P/P | P/P | P/P | - | P/P | P/P |
| spoke-us | P/P | P/P | P/P | P/P | P/P | - | P/P |
| spoke-jp | P/P | P/P | P/P | P/P | P/P | P/P | - |

## B1: Customer backbone through HRP

The primary capture uses `ExpressRoute` on all hubs, the original three extra EU/US nonlocal prepends, no extra Japan prepends, and spoke-only Azure imports. It is the final state after withdrawing and restoring only Japan's direct `10.130.0.0/24` Azure export. Mesh exports and tunnel configurations are unchanged.

The initial state, withdrawal, return, one-ASN-difference replay and `VpnGateway` HRP control are reported separately below. A final local winner must not be presented as proof that the HRP change alone produced it.

Matched state: [B1, JP direct prefix returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/scenario-result.json). Full BIRD configurations: [EU](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-eu.conf), [US](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-us.conf), [JP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-jp.conf), [CN](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-cn.conf).

### B1: complete EU firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.110.0.0/24` | `65011` | HubBgpConnection |
| `10.210.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | empty | Virtual Network Connection |
| `10.130.0.0/24` | `65011-65011-65011-65011-65013` | HubBgpConnection |
| `10.30.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.120.0.0/24` | `65520-65520-65012` | Remote Hub |
| `10.140.0.0/24` | `65520-65520-65013-65014` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

### B1: complete JP firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.140.0.0/24` | `65013-65014` | VPN_S2S_Gateway |
| `10.120.0.0/24` | `65013-65012` | VPN_S2S_Gateway |
| `10.110.0.0/24` | `65013-65011` | VPN_S2S_Gateway |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

### B1: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | `n/a` | `via 10.210.0.1 on eth0` | `n/a` | n/a | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | `dev wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013 65515` | 300 | `*` |

### B1: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | `dev wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515` | 300 | `!` |

### B1: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013 65515` | 300 | `*` |

### B1: captured EU export policy

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
        if net != 10.110.0.0/24 then {
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
        }
        accept;
  }
  reject;
}
```

### B1: all 42 traffic directions

| Source / destination | dc-eu | dc-us | dc-jp | cn | spoke-eu | spoke-us | spoke-jp |
|---|---|---|---|---|---|---|---|
| dc-eu | - | P/P | P/P | P/P | P/P | F/F | P/P |
| dc-us | P/P | - | P/P | P/P | F/F | P/P | P/P |
| dc-jp | P/P | P/P | - | P/P | F/F | F/F | F/F |
| cn | P/P | P/P | P/P | - | F/F | F/F | P/P |
| spoke-eu | P/P | F/P | F/F | F/P | - | P/P | P/P |
| spoke-us | F/P | P/P | F/F | F/P | P/P | - | P/P |
| spoke-jp | P/P | P/P | F/F | P/P | P/P | P/P | - |

## B2: Customer backbone through AS-path control

All hubs use `ASPath`. EU/US nonlocal extra prepends are removed; Japan still has no extra prepends. Azure imports remain spoke-only, so NVAs keep foreign DCs on their mesh. Removing prepends shortens the local offer; this is not a claim that adding prepends everywhere favors the customer backbone.

Matched state: [B2, zero extra EU/US prepends](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/scenario-result.json). Full BIRD configurations: [EU](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-eu.conf), [US](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-us.conf), [JP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-jp.conf), [CN](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-cn.conf).

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
| `10.120.0.0/24` | `65013-65012` | VPN_S2S_Gateway |
| `10.110.0.0/24` | `65013-65011` | VPN_S2S_Gateway |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `0.0.0.0/0` | empty | Internet |

### B2: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | `n/a` | `via 10.210.0.1 on eth0` | `n/a` | n/a | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | `dev wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013 65515` | 300 | `*` |

### B2: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | `dev wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515` | 300 | `!` |

### B2: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013 65515` | 300 | `*` |

### B2: captured EU export policy

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
        accept;
  }
  reject;
}
```

### B2: all 42 traffic directions

| Source / destination | dc-eu | dc-us | dc-jp | cn | spoke-eu | spoke-us | spoke-jp |
|---|---|---|---|---|---|---|---|
| dc-eu | - | P/P | P/P | P/P | P/P | P/P | P/P |
| dc-us | P/P | - | P/P | P/P | P/P | P/P | P/P |
| dc-jp | P/P | P/P | - | P/P | F/F | F/F | F/F |
| cn | P/P | P/P | P/P | - | P/P | P/P | P/P |
| spoke-eu | P/P | P/P | F/F | P/P | - | P/P | P/P |
| spoke-us | P/P | P/P | F/F | P/P | P/P | - | P/P |
| spoke-jp | P/P | P/P | F/F | P/P | P/P | P/P | - |

## B1 initial selection and controlled route return

| State | EU Japan path | US Japan path |
|---|---|---|
| B1, ExpressRoute initial | `65520-65520-65013` (Remote Hub) | `65520-65520-65013` (Remote Hub) |
| B1, JP direct prefix withdrawn | `65011-65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1, JP direct prefix returned | `65011-65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1 one-ASN, initial | `65520-65520-65013` (Remote Hub) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1 one-ASN, withdrawn | `65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1 one-ASN, returned | `65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1, VPN HRP | `65011-65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |

The three-prepend control offers local length five versus remote length three; the separate EU two-prepend control offers local four versus remote three. Only Japan's direct Azure prefix export is withdrawn; mesh exports and tunnels stay up. The earlier mixed-setting controls demonstrated different winners with identical configuration before/after re-advertisement. These new all-enabled results must be read alongside them, not used to invent an Azure-internal race/cache explanation. The published two-or-more-longer HRP caveat does not by itself explain every one-ASN case.

## Packet-interface evidence

| State / packet direction | EU | US | JP | CN |
|---|---|---|---|---|
| A, NVA policy only: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, enP40243s1 Out, eth0 In, eth0 Out | not observed | not observed | not observed |
| A, NVA policy only: `10.130.0.10` -> `10.110.0.10` | not observed | not observed | not observed | not observed |
| A, NVA policy only: `10.10.0.10` -> `10.130.0.10` | not observed | not observed | enP2749s1 Out, eth0 Out, xfrm42 In | not observed |
| A, NVA policy only: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | not observed | not observed |
| A, plus JP workload UDR: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, enP40243s1 Out, eth0 In, eth0 Out | not observed | not observed | not observed |
| A, plus JP workload UDR: `10.130.0.10` -> `10.110.0.10` | enP40243s1 In, enP40243s1 Out, eth0 In, eth0 Out | not observed | enP2749s1 In, eth0 In, xfrm42 Out | not observed |
| A, plus JP workload UDR: `10.10.0.10` -> `10.130.0.10` | not observed | not observed | enP2749s1 Out, eth0 Out, xfrm41 In, xfrm42 In | not observed |
| A, plus JP workload UDR: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | enP2749s1 In, eth0 In, xfrm42 Out | not observed |
| B1, JP direct prefix returned: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B1, JP direct prefix returned: `10.130.0.10` -> `10.110.0.10` | not observed | not observed | not observed | not observed |
| B1, JP direct prefix returned: `10.10.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B1, JP direct prefix returned: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | not observed | not observed |
| B2, zero extra EU/US prepends: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B2, zero extra EU/US prepends: `10.130.0.10` -> `10.110.0.10` | not observed | not observed | not observed | not observed |
| B2, zero extra EU/US prepends: `10.10.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B2, zero extra EU/US prepends: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | not observed | not observed |

## Conclusions and boundaries

Enabling Japan's hub flag alone did not change this baseline's firewall winners or traffic outcomes. The configuration inconsistency therefore was not sufficient to explain those failures. The per-design traffic matrices above establish exactly which workload directions passed; selected routes alone do not establish a successful backbone design. Residual failures and any `!` flags remain failures, not success-shaped exceptions. No bandwidth advantage was measured. Configuration, original hub settings and original VM power states were restored after the rerun.

[Full rerun report and raw evidence](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-summary-20261017/README.md). Earlier mixed-setting results and their original verdicts remain linked in [references.md](./references.md).

## Retrieve effective routes

With routing intent, query the firewall, not a spoke connection:

```powershell
az network vhub get-effective-routes -n $hub -g $rg `
  --resource-type 'AzureFirewalls' `
  --resource-id $(az network vhub show -g $rg -n $hub --query 'azureFirewall.id' -o tsv) `
  --query 'value[].{Prefix:addressPrefixes[0], ASPath:asPath, NextHopType:nextHopType}' -o table
```

Without routing intent, query the VNet connection using the singular discriminator:

```powershell
$connectionId = az network vhub connection show -g $rg --vhub-name $hub `
  -n $connection --query id -o tsv
az network vhub get-effective-routes -n $hub -g $rg `
  --resource-type 'HubVirtualNetworkConnection' --resource-id $connectionId -o json
```

On each NVA, retain `birdc show route table lab4 all`, `birdc show route export azure_0 all`, `birdc show route export azure_1 all`, `ip -j route show table main`, and the full BIRD configuration. CN has no Azure peers.

## What the three designs configure

| Design | All-hub HRP | NVA policy |
|---|---|---|
| A: Microsoft | ASPath | Foreign DC/spoke Azure imports at LP 400; three nonlocal prepends on EU/US/JP; optional JP workload UDR measured separately |
| B1: customer | ExpressRoute; VpnGateway measured separately | Spoke-only Azure imports; three extra nonlocal EU/US prepends; JP none |
| B2: customer | ASPath | Spoke-only Azure imports; zero extra EU/US/JP prepends |

The [documented HRP ordering](https://learn.microsoft.com/en-us/azure/virtual-wan/about-virtual-hub-routing-preference) prioritizes locality under ExpressRoute/VPN and path length under ASPath. The B1 initial, withdrawn and returned states below expose the measured selection history rather than assuming every HRP update recomputes the same winner.

## Forwarding results, not just routing tables

| Measured state | TCP / 42 | ICMP / 42 |
|---|---|---|
| [Mixed baseline](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-mixed-baseline-20261017/baseline/traffic-summary.json) | 28 | 32 |
| [All B2B baseline](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-enabled-baseline-20261017/baseline/traffic-summary.json) | 28 | 32 |
| [A, NVA policy only](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A/traffic-summary.json) | 36 | 36 |
| [A, plus JP workload UDR](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/traffic-summary.json) | 38 | 40 |
| [B1, ExpressRoute initial](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1/traffic-summary.json) | 28 | 32 |
| [B1, JP direct prefix withdrawn](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-withdrawn/traffic-summary.json) | 28 | 32 |
| [B1, JP direct prefix returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/traffic-summary.json) | 28 | 32 |
| [B1 one-ASN, initial](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN/traffic-summary.json) | 30 | 33 |
| [B1 one-ASN, withdrawn](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN-withdrawn/traffic-summary.json) | 30 | 33 |
| [B1 one-ASN, returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-one-ASN-20261017/B1-one-ASN-returned/traffic-summary.json) | 30 | 33 |
| [B1, VPN HRP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-VPN-20261017/B1-VPN/traffic-summary.json) | 32 | 34 |
| [B2, zero extra EU/US prepends](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/traffic-summary.json) | 36 | 36 |

Every measured state has full firewall effective tables for all three hubs, paired stable DC-prefix winners at least 120 seconds apart, full BIRD sources and selected/alternative routes on all four routers, and an explicitly sourced 42-direction TCP/ICMP matrix. The seven endpoints are four synthetic DCs and three Azure spokes: 12 DC-to-DC, 24 DC/spoke and six spoke-to-spoke directions. TCP requires HTTP 200 on the private port 5201 listener and matching local/remote addresses; ICMP uses source-bound ping. P/F below means TCP PASS / ICMP FAIL.

Bounded tcpdump captures on every router observe inner test packets on physical, WireGuard and XFRM interfaces; management traffic and encrypted transport payloads are not collected. The interface observations are not a throughput measurement or a complete symmetry proof. Failed SYNs/ICMP attempts can still appear in a capture. In particular, A's policy-only EU/JP DC reachability is not proof of the intended Virtual WAN path: the measured EU-to-JP DC packets appeared on EU's physical interfaces, but the expected Japan NVA/XFRM segment was not observed; the reverse initiated DC traffic was not observed on the NVAs. The peered underlay and workload routing must be considered rather than treating an HTTP success as proof of Microsoft interhub transit. `!` in a BIRD table is a kernel-export failure marker, not healthy Linux forwarding. A collector verdict of PASS means complete measurements and exact configuration closure, not 42 successful traffic directions.

During B1's three-prepend withdrawal, Japan's firewall exposes two equal-length remote Japan-prefix entries, one through EU and one through US. All twelve hub/prefix keys remain present, but there are thirteen rows. The inherited single-winner check therefore records `complete: false`; this flag is retained in raw evidence and does not mean a prefix was missing in that state.

## How to read the captured tables

Each design below contains the full EU and Japan firewall table, not a filtered supporting prefix. US is collected too and available in the matched evidence. EU, Japan and CN NVA tables include all seven DC/spoke prefixes. BGP next hop and BIRD resolution are distinct attributes. `n/a` means absent on a static route; `empty` means a blank firewall AS path. The primary A state includes the workload UDR; primary B1 is the returned three-prepend state.

## A: Microsoft backbone preferred

All hubs use `ASPath`. The three Azure-facing NVAs accept foreign DC and spoke routes from Azure at LP 400. EU/US/JP add three extra own-AS copies for nonlocal DC exports. The export source guard prevents feeding an Azure-learned best route back into Azure. CN remains mesh-only, so this is not an all-prefix Microsoft-only design.

The primary capture includes the five-prefix Japan workload UDR to `10.130.0.4`; the policy-only control is measured separately. The UDR covers EU/US DCs and all three Azure spokes, not CN's transport endpoint.

Matched state: [A, plus JP workload UDR](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/scenario-result.json). Full BIRD configurations: [EU](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-eu.conf), [US](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-us.conf), [JP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-jp.conf), [CN](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-A-20261017/A-workload-UDR/router-cn.conf).

### A: complete EU firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.210.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | empty | Virtual Network Connection |
| `10.110.0.0/24` | `65011` | HubBgpConnection |
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
| `10.140.0.0/24` | `65013-65013-65013-65013-65014` | VPN_S2S_Gateway |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.120.0.0/24` | `65520-65520-65012` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `10.110.0.0/24` | `65520-65520-65011` | Remote Hub |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `0.0.0.0/0` | empty | Internet |

### A: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | `n/a` | `via 10.210.0.1 on eth0` | `n/a` | n/a | `*` |
| `10.120.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520 65012` | 400 | `*` |
| `10.130.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520 65013` | 400 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | `dev wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515` | 400 | `*` |
| `10.20.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520` | 400 | `*` |
| `10.30.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515 65520 65520` | 400 | `*` |

### A: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520 65011` | 400 | `!` |
| `10.120.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520 65012` | 400 | `!` |
| `10.130.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | `dev wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520` | 400 | `!` |
| `10.20.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515 65520 65520` | 400 | `!` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515` | 400 | `!` |

### A: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013 65515` | 300 | `*` |

### A: captured EU export policy

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
        if net != 10.110.0.0/24 then {
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
        }
        accept;
  }
  reject;
}
```

### A: all 42 traffic directions

| Source / destination | dc-eu | dc-us | dc-jp | cn | spoke-eu | spoke-us | spoke-jp |
|---|---|---|---|---|---|---|---|
| dc-eu | - | P/P | F/F | P/P | P/P | P/P | P/P |
| dc-us | P/P | - | F/F | P/P | P/P | P/P | P/P |
| dc-jp | F/P | F/P | - | P/P | P/P | P/P | P/P |
| cn | P/P | P/P | P/P | - | P/P | P/P | P/P |
| spoke-eu | P/P | P/P | P/P | P/P | - | P/P | P/P |
| spoke-us | P/P | P/P | P/P | P/P | P/P | - | P/P |
| spoke-jp | P/P | P/P | P/P | P/P | P/P | P/P | - |

## B1: Customer backbone through HRP

The primary capture uses `ExpressRoute` on all hubs, the original three extra EU/US nonlocal prepends, no extra Japan prepends, and spoke-only Azure imports. It is the final state after withdrawing and restoring only Japan's direct `10.130.0.0/24` Azure export. Mesh exports and tunnel configurations are unchanged.

The initial state, withdrawal, return, one-ASN-difference replay and `VpnGateway` HRP control are reported separately below. A final local winner must not be presented as proof that the HRP change alone produced it.

Matched state: [B1, JP direct prefix returned](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/scenario-result.json). Full BIRD configurations: [EU](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-eu.conf), [US](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-us.conf), [JP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-jp.conf), [CN](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B1-20261017/B1-returned/router-cn.conf).

### B1: complete EU firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.110.0.0/24` | `65011` | HubBgpConnection |
| `10.210.0.0/24` | empty | Virtual Network Connection |
| `10.10.0.0/24` | empty | Virtual Network Connection |
| `10.130.0.0/24` | `65011-65011-65011-65011-65013` | HubBgpConnection |
| `10.30.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.120.0.0/24` | `65520-65520-65012` | Remote Hub |
| `10.140.0.0/24` | `65520-65520-65013-65014` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

### B1: complete JP firewall table

| Prefix | ASPath | NextHopType |
|---|---|---|
| `10.140.0.0/24` | `65013-65014` | VPN_S2S_Gateway |
| `10.120.0.0/24` | `65013-65012` | VPN_S2S_Gateway |
| `10.110.0.0/24` | `65013-65011` | VPN_S2S_Gateway |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `0.0.0.0/0` | empty | Internet |

### B1: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | `n/a` | `via 10.210.0.1 on eth0` | `n/a` | n/a | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | `dev wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013 65515` | 300 | `*` |

### B1: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | `dev wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515` | 300 | `!` |

### B1: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013 65515` | 300 | `*` |

### B1: captured EU export policy

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
        if net != 10.110.0.0/24 then {
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
            bgp_path.prepend(65011);
        }
        accept;
  }
  reject;
}
```

### B1: all 42 traffic directions

| Source / destination | dc-eu | dc-us | dc-jp | cn | spoke-eu | spoke-us | spoke-jp |
|---|---|---|---|---|---|---|---|
| dc-eu | - | P/P | P/P | P/P | P/P | F/F | P/P |
| dc-us | P/P | - | P/P | P/P | F/F | P/P | P/P |
| dc-jp | P/P | P/P | - | P/P | F/F | F/F | F/F |
| cn | P/P | P/P | P/P | - | F/F | F/F | P/P |
| spoke-eu | P/P | F/P | F/F | F/P | - | P/P | P/P |
| spoke-us | F/P | P/P | F/F | F/P | P/P | - | P/P |
| spoke-jp | P/P | P/P | F/F | P/P | P/P | P/P | - |

## B2: Customer backbone through AS-path control

All hubs use `ASPath`. EU/US nonlocal extra prepends are removed; Japan still has no extra prepends. Azure imports remain spoke-only, so NVAs keep foreign DCs on their mesh. Removing prepends shortens the local offer; this is not a claim that adding prepends everywhere favors the customer backbone.

Matched state: [B2, zero extra EU/US prepends](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/scenario-result.json). Full BIRD configurations: [EU](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-eu.conf), [US](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-us.conf), [JP](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-jp.conf), [CN](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-B2-20261017/B2/router-cn.conf).

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
| `10.120.0.0/24` | `65013-65012` | VPN_S2S_Gateway |
| `10.110.0.0/24` | `65013-65011` | VPN_S2S_Gateway |
| `10.130.0.0/24` | `65013` | VPN_S2S_Gateway |
| `10.10.0.0/24` | `65520-65520` | Remote Hub |
| `10.220.0.0/24` | `65520-65520` | Remote Hub |
| `10.20.0.0/24` | `65520-65520` | Remote Hub |
| `10.210.0.0/24` | `65520-65520` | Remote Hub |
| `10.30.0.0/24` | empty | Virtual Network Connection |
| `0.0.0.0/0` | empty | Internet |

### B2: EU selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `own_dc` | `n/a` | `via 10.210.0.1 on eth0` | `n/a` | n/a | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.10` | `dev wgeucn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `azure_0` | `10.210.0.1` | `via 10.210.0.1 on eth0` | `65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.2` | `dev wgeuus` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.6` | `dev wgeujp` | `65013 65515` | 300 | `*` |

### B2: JP selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.140.0.0/24` | `mesh_cn` | `172.31.0.22` | `dev wgjpcn` | `65014` | 100 | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.5` | `dev wgeujp` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.13` | `dev wgusjp` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `azure_1` | `169.254.21.6` | `via 169.254.21.6 on xfrm42` | `65515` | 300 | `!` |

### B2: CN selected NVA routes

| Prefix | Protocol | BGP next hop | BIRD resolution | ASPath | LP | Marker |
|---|---|---|---|---|---|---|
| `10.110.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011` | 100 | `*` |
| `10.120.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012` | 100 | `*` |
| `10.130.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013` | 100 | `*` |
| `10.140.0.0/24` | `own_dc` | `n/a` | `dev eth0` | `n/a` | n/a | `*` |
| `10.10.0.0/24` | `mesh_eu` | `172.31.0.9` | `dev wgeucn` | `65011 65515` | 300 | `*` |
| `10.20.0.0/24` | `mesh_us` | `172.31.0.17` | `dev wguscn` | `65012 65515` | 300 | `*` |
| `10.30.0.0/24` | `mesh_jp` | `172.31.0.21` | `dev wgjpcn` | `65013 65515` | 300 | `*` |

### B2: captured EU export policy

```bird
filter azure_export {
  if net ~ [10.110.0.0/24, 10.120.0.0/24, 10.130.0.0/24, 10.140.0.0/24] &&
     (proto = "own_dc" || proto ~ "mesh_*") then {
        accept;
  }
  reject;
}
```

### B2: all 42 traffic directions

| Source / destination | dc-eu | dc-us | dc-jp | cn | spoke-eu | spoke-us | spoke-jp |
|---|---|---|---|---|---|---|---|
| dc-eu | - | P/P | P/P | P/P | P/P | P/P | P/P |
| dc-us | P/P | - | P/P | P/P | P/P | P/P | P/P |
| dc-jp | P/P | P/P | - | P/P | F/F | F/F | F/F |
| cn | P/P | P/P | P/P | - | P/P | P/P | P/P |
| spoke-eu | P/P | P/P | F/F | P/P | - | P/P | P/P |
| spoke-us | P/P | P/P | F/F | P/P | P/P | - | P/P |
| spoke-jp | P/P | P/P | F/F | P/P | P/P | P/P | - |

## B1 initial selection and controlled route return

| State | EU Japan path | US Japan path |
|---|---|---|
| B1, ExpressRoute initial | `65520-65520-65013` (Remote Hub) | `65520-65520-65013` (Remote Hub) |
| B1, JP direct prefix withdrawn | `65011-65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1, JP direct prefix returned | `65011-65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1 one-ASN, initial | `65520-65520-65013` (Remote Hub) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1 one-ASN, withdrawn | `65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1 one-ASN, returned | `65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |
| B1, VPN HRP | `65011-65011-65011-65011-65013` (HubBgpConnection) | `65012-65012-65012-65012-65013` (HubBgpConnection) |

The three-prepend control offers local length five versus remote length three; the separate EU two-prepend control offers local four versus remote three. Only Japan's direct Azure prefix export is withdrawn; mesh exports and tunnels stay up. The earlier mixed-setting controls demonstrated different winners with identical configuration before/after re-advertisement. These new all-enabled results must be read alongside them, not used to invent an Azure-internal race/cache explanation. The published two-or-more-longer HRP caveat does not by itself explain every one-ASN case.

## Packet-interface evidence

| State / packet direction | EU | US | JP | CN |
|---|---|---|---|---|
| A, NVA policy only: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, enP40243s1 Out, eth0 In, eth0 Out | not observed | not observed | not observed |
| A, NVA policy only: `10.130.0.10` -> `10.110.0.10` | not observed | not observed | not observed | not observed |
| A, NVA policy only: `10.10.0.10` -> `10.130.0.10` | not observed | not observed | enP2749s1 Out, eth0 Out, xfrm42 In | not observed |
| A, NVA policy only: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | not observed | not observed |
| A, plus JP workload UDR: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, enP40243s1 Out, eth0 In, eth0 Out | not observed | not observed | not observed |
| A, plus JP workload UDR: `10.130.0.10` -> `10.110.0.10` | enP40243s1 In, enP40243s1 Out, eth0 In, eth0 Out | not observed | enP2749s1 In, eth0 In, xfrm42 Out | not observed |
| A, plus JP workload UDR: `10.10.0.10` -> `10.130.0.10` | not observed | not observed | enP2749s1 Out, eth0 Out, xfrm41 In, xfrm42 In | not observed |
| A, plus JP workload UDR: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | enP2749s1 In, eth0 In, xfrm42 Out | not observed |
| B1, JP direct prefix returned: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B1, JP direct prefix returned: `10.130.0.10` -> `10.110.0.10` | not observed | not observed | not observed | not observed |
| B1, JP direct prefix returned: `10.10.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B1, JP direct prefix returned: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | not observed | not observed |
| B2, zero extra EU/US prepends: `10.110.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B2, zero extra EU/US prepends: `10.130.0.10` -> `10.110.0.10` | not observed | not observed | not observed | not observed |
| B2, zero extra EU/US prepends: `10.10.0.10` -> `10.130.0.10` | enP40243s1 In, eth0 In, wgeujp Out | not observed | enP2749s1 Out, eth0 Out, wgeujp In | not observed |
| B2, zero extra EU/US prepends: `10.130.0.10` -> `10.10.0.10` | not observed | not observed | not observed | not observed |

## Conclusions and boundaries

Enabling Japan's hub flag alone did not change this baseline's firewall winners or traffic outcomes. The configuration inconsistency therefore was not sufficient to explain those failures. The per-design traffic matrices above establish exactly which workload directions passed; selected routes alone do not establish a successful backbone design. Residual failures and any `!` flags remain failures, not success-shaped exceptions. No bandwidth advantage was measured. Configuration, original hub settings and original VM power states were restored after the rerun.

[Full rerun report and raw evidence](https://github.com/erjosito/net-lab-builder/blob/main/labs/vwan-sdwan-three-hub/show-output/b2b-summary-20261017/README.md). Earlier mixed-setting results and their original verdicts remain linked in [references.md](./references.md).

## Retrieve effective routes

With routing intent, query the firewall, not a spoke connection:

```powershell
az network vhub get-effective-routes -n $hub -g $rg `
  --resource-type 'AzureFirewalls' `
  --resource-id $(az network vhub show -g $rg -n $hub --query 'azureFirewall.id' -o tsv) `
  --query 'value[].{Prefix:addressPrefixes[0], ASPath:asPath, NextHopType:nextHopType}' -o table
```

Without routing intent, query the VNet connection using the singular discriminator:

```powershell
$connectionId = az network vhub connection show -g $rg --vhub-name $hub `
  -n $connection --query id -o tsv
az network vhub get-effective-routes -n $hub -g $rg `
  --resource-type 'HubVirtualNetworkConnection' --resource-id $connectionId -o json
```

On each NVA, retain `birdc show route table lab4 all`, `birdc show route export azure_0 all`, `birdc show route export azure_1 all`, `ip -j route show table main`, and the full BIRD configuration. CN has no Azure peers.
