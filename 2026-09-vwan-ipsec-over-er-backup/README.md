# Backing Up Azure Virtual WAN IPsec over ExpressRoute with Internet VPN

*A live cross-cloud test of three routing designs—and why independent BGP adjacencies are the one to take into production.*

## The decision

If you carry an IPsec tunnel over ExpressRoute and want an Internet IPsec tunnel as backup, build **dedicated BGP adjacencies for each transport**.

Do not try to float one unchanged BGP adjacency between the private and public tunnels. Moving the route to the peer is not enough: Azure Virtual WAN still associates the remote BGP identity with a particular VPN connection. Under complete ExpressRoute loss, the CPE's TCP/179 SYNs crossed the public IPsec tunnel, but Azure did not answer them.

A static aggregate over the public tunnel also provided a working backup. Private
BGP specifics were preferred during normal operation, the public aggregate took
over when the private sessions were withdrawn, and the private path became best
again when BGP was restored.

The production-oriented result is therefore:

1. Use separate private and public BGP sessions.
2. Apply deterministic preference in both directions.
3. Set convergence objectives from measured failure detection, not from the provider link's administrative state.

D3 is therefore a valid simpler alternative when a static public backup is
acceptable, although D2 provides explicit control-plane state for both
transports.

This post summarizes the sanitized lab evidence. Supporting public documentation
and source-publication status are collected in [references.md](./references.md).

## The unusual topology: VPN over two different underlays

This was not a conventional choice between ExpressRoute and VPN routes. Both candidate paths were **site-to-site VPN overlays** terminating on the same active-active Virtual WAN VPN gateway:

- The primary pair of IPsec tunnels used ExpressRoute as their underlay.
- The backup pair used the public Internet as their underlay.
- BGP ran inside the IPsec tunnels.
- Application prefixes existed only in the overlay; ExpressRoute did not carry them in clear text.

The CPE was a StrongSwan and FRR appliance in Google Cloud. Its private endpoint reached Azure through Partner Interconnect, a Megaport Cloud Router, two Azure ExpressRoute paths, and a Virtual WAN ExpressRoute gateway. Its public endpoint reached the same Virtual WAN VPN gateway through the Internet.

```mermaid
flowchart LR
    APP["Branch application prefixes"]
    CPE["Linux CPE<br/>StrongSwan + FRR"]
    PI["Partner Interconnect"]
    MCR["Megaport Cloud Router"]
    ER["ExpressRoute<br/>primary + secondary MSEE paths"]
    ERGW["vWAN ExpressRoute gateway"]
    INET["Public Internet"]
    VPNGW["vWAN VPN gateway<br/>active-active"]
    HUB["Virtual hub"]
    AZAPP["Azure workload"]

    APP --> CPE
    CPE == "Private underlay<br/>2 IPsec tunnels<br/>2 BGP sessions" ==> PI
    PI ==> MCR ==> ER ==> ERGW ==> VPNGW
    CPE -. "Public underlay<br/>2 IPsec tunnels<br/>2 BGP sessions" .-> INET
    INET -.-> VPNGW
    VPNGW --> HUB --> AZAPP
```

This distinction between **underlay** and **overlay** is essential:

- The underlay answers, "Can the IPsec endpoints reach each other?"
- IPsec answers, "Is the encrypted tunnel usable?"
- BGP answers, "Should the application route remain installed?"
- The payload test answers, "Can an application packet complete the round trip?"

Those layers do not necessarily fail at the same time. A provider can report a VXC down while BGP retains stale routes. An IPsec SA can remain listed while a filtered data plane drops every packet. A static route can remain installed indefinitely because it has no protocol neighbor to withdraw it.

## Three designs, three different failure semantics

The lab kept the four IPsec slots and their pre-shared keys unchanged after a one-time synchronization. D1, D2, and D3 changed only routing and BGP state. That invariant matters: the results compare control-plane designs, not different tunnel configurations.

```mermaid
flowchart TB
    Q{"How should the backup path learn routes?"}

    D1["D1: one floating adjacency<br/>Move only the peer route"]
    D2["D2: dedicated adjacencies<br/>Private and public peers"]
    D3["D3: private BGP specifics<br/>Public static aggregate"]

    R1["Rejected<br/>Peer reachability moved;<br/>Azure connection binding did not"]
    R2["Recommended<br/>Independent withdrawal,<br/>preference, and takeover"]
    R3["Validated alternative<br/>Failover and failback<br/>both passed"]

    Q --> D1 --> R1
    Q --> D2 --> R2
    Q --> D3 --> R3
```

### D1: why a floating BGP adjacency fails

D1 tried to preserve one ordinary BGP tuple while moving only the CPE route to the Azure neighbor between XFRM interfaces.

At first, this looked promising. While ExpressRoute was still available, moving the peer route to the public tunnel kept the session working. Packet capture revealed why: the request left through public IPsec, but Azure still had ExpressRoute reachability for the return path. The apparent "float" was asymmetric.

The decisive test removed the complete ExpressRoute transport while leaving Internet VPN operational. The CPE had only the intended floating identity, and its host route to the Azure BGP peer pointed through the public XFRM interface. Captures repeatedly showed:

```text
CPE floating identity -> Azure BGP peer: TCP SYN, destination port 179
Azure BGP peer -> CPE floating identity: no response
```

FRR remained in `Connect`. No SYN-ACK arrived.

The result exposes the difference between **routing to a BGP endpoint** and **owning that peer on a managed connection**. The CPE could redirect packets into another healthy tunnel, but Azure did not transfer the remote BGP identity from the ExpressRoute-backed VPN connection to the Internet-backed VPN connection.

This is the general lesson from D1:

> A BGP adjacency cannot be assumed portable merely because its endpoint addresses are reachable through another tunnel.

Managed gateways have configuration-plane identity and connection binding in addition to packet forwarding. A design that depends on that binding moving at failure time needs an explicit platform mechanism to move it. D1 had none.

### D2: independent adjacencies make failure explicit

D2 assigned a different BGP control plane to each path class:

- Two private sessions used the VPN-over-ExpressRoute tunnels.
- Two custom APIPA sessions used the Internet VPN tunnels.
- Private routes received local preference `200` at the CPE.
- Public routes received local preference `100`.
- Advertisements toward Azure used AS-path prepending on the public sessions so that Azure also preferred the private overlay.

The diagram below separates the **IKE endpoints**, which build the underlay-facing
IPsec SAs, from the **BGP endpoints**, which exist inside the XFRM interfaces.
The private active-active instances cross-map to the observed BGP peer routes:
Azure peer `.13` used `xfrm-pri0`, while `.12` used `xfrm-pri1`.

```mermaid
flowchart LR
    subgraph CPE["GCP Linux CPE — ASN 65050"]
        CPEPRI["Private IKE endpoint<br/>10.250.0.10"]
        CPEPUB["Public IKE endpoint<br/>34.51.158.147 (1:1 NAT)"]
        CPEBGPPRI["Private BGP source<br/>10.250.254.240"]
        CPEBGPPUB["Public BGP source<br/>169.254.21.6"]
    end

    subgraph AZ["Azure Virtual WAN VPN gateway — ASN 65515"]
        AZIKE0["Private IKE Instance0<br/>10.240.0.4"]
        AZIKE1["Private IKE Instance1<br/>10.240.0.5"]
        AZPUB0["Public IKE Instance0<br/>74.158.47.254"]
        AZPUB1["Public IKE Instance1<br/>74.158.80.26"]
        AZBGPPRI0["Private BGP peer<br/>10.240.0.13"]
        AZBGPPRI1["Private BGP peer<br/>10.240.0.12"]
        AZBGPPUB0["Public BGP peer<br/>169.254.21.5"]
        AZBGPPUB1["Public BGP peer<br/>169.254.22.5"]
    end

    CPEPRI == "pri0 — IKE/IPsec over ER" ==> AZIKE0
    CPEPRI == "pri1 — IKE/IPsec over ER" ==> AZIKE1
    CPEPUB -. "pub0 — IKE/IPsec over Internet" .-> AZPUB0
    CPEPUB -. "pub1 — IKE/IPsec over Internet" .-> AZPUB1

    CPEBGPPRI == "TCP/179 inside xfrm-pri0" ==> AZBGPPRI0
    CPEBGPPRI == "TCP/179 inside xfrm-pri1" ==> AZBGPPRI1
    CPEBGPPUB -. "TCP/179 inside xfrm-pub0" .-> AZBGPPUB0
    CPEBGPPUB -. "TCP/179 inside xfrm-pub1" .-> AZBGPPUB1
```

This produced four established sessions in the validated D2 baseline. Equal-cost paths were allowed within the private pair and within the public pair, but never across private and public transports.

That separation solves the D1 problem. Azure does not need to reinterpret one peer identity. The public connection already owns its own BGP sessions, and those sessions can remain established while private transport is healthy.

### Hub Routing Preference and path selection

The virtual hub used **Hub Routing Preference = `ASPath`**. D2 advertised the
same branch prefix, `10.253.2.0/24`, through both VPN connections:

- Private sessions advertised the natural path containing one `65050`.
- Public sessions added three `65050` prepends.
- With `ASPath`, the shorter private advertisement won on the Azure side.

The CPE made the reverse decision independently. Routes learned from the
private peers received local preference `200`; routes learned from the public
peers received local preference `100`. This provided deterministic preference
in both directions rather than assuming Azure would infer that the IPsec
underlay happened to be ExpressRoute.

The hub-level effective-route output requires careful interpretation. In the
normal capture, it showed:

```text
Prefix:         10.253.2.0/24
Next hop type:  VPN_S2S_Gateway
Route origin:   vWAN VPN gateway
AS path:        not exposed in this consolidated view
```

That output proves the selected branch prefix entered the hub through the VPN
overlay. It does **not** identify the winning VPN site or active-active
instance: both the ER-backed and Internet-backed tunnels terminate on the same
managed VPN gateway. The path-class evidence therefore came from the four BGP
session states, FRR policy, scoped XFRM routes, and payload.

| State | Azure-side selection | CPE route to `10.241.0.0/24` | Payload |
| --- | --- | --- | --- |
| Normal | Short private AS path selected for `10.253.2.0/24`; public prepended path remained standby | BGP distance 20 through `10.240.0.12/.13` on `xfrm-pri1/pri0` | Pass |
| ER failed, before withdrawal | Hub still had the stale private advertisement | Stale private BGP route remained best | Fail |
| ER failed, after convergence | Public APIPA advertisement became the selected route for the same `/24` | BGP distance 20 through `169.254.21.5/.22.5` on `xfrm-pub0/pub1` | Pass |
| ER restored | Short private path selected again | Private BGP pair became best again | Pass |

## What full ExpressRoute loss looked like

The complete private-underlay fault was injected by directly shutting the single Megaport VXC on the Google Cloud side. That one operation removed both MSEE paths while preserving Internet access. It was a cleaner fault than changing the CPE, disabling BGP manually, or applying a broad infrastructure plan.

The public BGP sessions remained established throughout. The private routes, however, did not disappear when the provider object first changed state. They remained stale until transport and BGP failure detection completed.

```mermaid
sequenceDiagram
    participant F as Fault controller
    participant ER as ExpressRoute underlay
    participant PB as Private BGP pair
    participant UB as Public BGP pair
    participant P as Payload probes

    F->>ER: Shut the GCP-side VXC
    ER-->>PB: Both private transport paths disappear
    P-->>P: Probes begin failing
    Note over PB,P: Stale private routes remain selected
    PB-->>PB: First private neighbor withdraws
    PB-->>UB: Second private neighbor withdraws
    UB-->>UB: Public pair becomes best
    P-->>P: Bidirectional payload recovers
```

The measured sequence was:

| Event | Approximate time |
| --- | ---: |
| First failed payload probe | `17:51:55Z` |
| First private neighbor withdrew | `17:54:02Z` |
| Second private neighbor withdrew; public became best | `17:54:15Z` |
| Observed stale-private-path outage | About 140 seconds |

The important number is not the VXC shutdown time. It is the interval between the first payload failure and the route change that restored payload.

This was a failure-detection result, not an intrinsic promise from Azure Virtual WAN, ExpressRoute, StrongSwan, FRR, or Megaport. Different DPD, TCP, and BGP timers—and different failure modes—can produce different convergence. Production objectives should be based on repeated measurements of the failures that matter, with the chosen timer policy documented.

### Failback

After the VXC was restored, both provider paths and the ExpressRoute underlay returned. Azure initiated fresh private IKE, but the CPE initially could not match the inbound initiator to a loaded shared key. The test did not rotate a secret or alter StrongSwan.

Initiating the already-configured private children from the CPE recovered both private SAs. The two private BGP sessions then established, private preference won again, and five payload probes completed with 0% loss.

The routing design therefore passed both takeover and failback without changing a PSK or StrongSwan configuration. Operationally, however, the restore also demonstrates that "the circuit is back" and "the preferred overlay is back" are separate milestones.

## D3: longest-prefix preference provides a simple backup

D3 tested a tempting simplification:

- Advertise two `/25` specifics over private BGP.
- Configure a covering static `/24` on the public VPN connection.
- Use a high-distance public static route in the reverse direction.

While private BGP was healthy, longest-prefix match selected the `/25`s. When private BGP was deliberately withdrawn and the Internet tunnel was healthy, the public `/24` carried the traffic successfully.

The preference existed independently in each direction:

| Direction | Primary | Backup | Why primary wins |
| --- | --- | --- | --- |
| Azure to branch | Private BGP `10.253.3.0/25` and `10.253.3.128/25` | Public static `10.253.3.0/24` | Longest-prefix match |
| CPE to Azure | Private BGP `10.241.0.0/24`, distance 20 | Public XFRM static routes, distance 250 | Lower administrative distance |

The CPE diagnostics made the transition explicit. In normal state, the BGP
route was best while the static route remained installed but inactive:

```text
10.241.0.0/24 via BGP, distance 20, best
  10.240.0.12 via xfrm-pri1
  10.240.0.13 via xfrm-pri0

10.241.0.0/24 via static, distance 250
  xfrm-pub0
  xfrm-pub1
```

After both private BGP neighbors were shut down, the route changed to:

```text
10.241.0.0/24 via static, distance 250, best
  xfrm-pub0
  xfrm-pub1
```

With a healthy Internet tunnel, that state passed payload. Restoring private
BGP restored the distance-20 route and payload continued to pass. **D3
failback therefore worked.**

The MSEE route table cannot show this `/25` versus `/24` decision. MSEE is part
of the ExpressRoute **underlay** and saw the route to the CPE's private IPsec
endpoint, `10.250.0.10/32`. The D3 application prefixes were encrypted inside
IPsec and appeared only in VPN/vHub overlay routing. Looking for
`10.253.3.0/25` at the MSEE would mix the two routing layers.

The D3 result was successful in both directions: withdrawing private BGP moved
traffic to the public static backup, and restoring private BGP returned traffic
to the more-specific private routes.

## Operational implications

### Prefer explicit path ownership

The robust design gives each transport its own peer addresses, sessions, policy, and failure state. That makes withdrawal meaningful and troubleshooting bounded. You can answer:

- Which transport owns this neighbor?
- Which session learned this route?
- Which path is preferred in each direction?
- Did the route withdraw when its transport failed?

With a floating identity, those questions become ambiguous at the exact moment when clarity matters.

### Engineer both directions

Private preference was implemented independently:

- At the CPE, local preference favored private-learned Azure routes.
- Toward Azure, AS-path prepending made public advertisements less attractive.

Solving only one direction risks asymmetric traffic, stateful-firewall surprises, or a test that appears healthy because the return path is still using the primary transport—as D1 demonstrated before full ExpressRoute loss.

### Tune and test convergence deliberately

The roughly 140-second interruption was dominated by stale private-path detection. If that exceeds the recovery objective, possible responses include reviewed BGP timer changes, BFD where the complete platform path supports it, stronger tunnel liveness, or application-level retry and redundancy.

Do not tune one timer in isolation. Aggressive values can turn transient packet loss into session churn, and a fast BGP withdrawal does not help if the underlying tunnel or managed gateway retains stale state elsewhere.

### Treat routing-mode changes as maintenance events

There is one final caveat. After D3, the Azure public connection was switched from static mode back to D2 BGP mode without re-establishing the public SAs. The custom APIPA configuration was still present, and the CPE's SYNs crossed both public XFRM interfaces, but Azure did not answer them.

The live final state therefore must **not** be described as four established BGP sessions. It had four IPsec SAs, the two private BGP adjacencies, private best-path selection, and healthy payload; the public APIPA BGP listeners had not resumed.

That later mode-switch behavior does not invalidate the earlier completed D2 failure and failback test, which began with four established sessions and proved public takeover. It does mean that changing a live connection between static and BGP modes should have its own maintenance procedure, including tunnel re-establishment and validation, rather than being treated as a harmless route-only edit.

## Practical design checklist

For a similar deployment:

- [ ] Build separate VPN connections or links for private and public transport identity.
- [ ] Give each path class dedicated BGP peer addresses.
- [ ] Verify all active-active sessions individually.
- [ ] Pin IKE endpoint routes to the intended underlay to prevent recursion.
- [ ] Keep application prefixes out of the clear-text ExpressRoute underlay.
- [ ] Apply private-over-public preference in both directions.
- [ ] Prevent ECMP across unlike path classes.
- [ ] Test complete private-underlay loss, not only a BGP shutdown.
- [ ] Measure first packet loss, route withdrawal, recovery, and failback separately.
- [ ] Revalidate or re-establish tunnels after changing a connection's routing mode.

## Bottom line

An Internet VPN can back up IPsec over ExpressRoute in Azure Virtual WAN, but the reliable unit of failover is the **adjacency**, not merely the route to a peer.

Dedicated per-tunnel BGP sessions survived complete ExpressRoute loss and
provided deterministic failback. One floating adjacency failed because Azure's
peer identity remained bound to the private connection.

A static aggregate also passed failover and failback, making it a valid simpler
alternative when the reduced control-plane visibility is acceptable.
