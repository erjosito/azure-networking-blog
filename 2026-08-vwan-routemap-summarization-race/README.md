# When the AS-path lies: a Virtual WAN route-map summarization race you cannot see in BGP

A customer reported that a `/16` summary route, produced by a Virtual WAN outbound **route-map**, kept **disappearing and reappearing** across route recomputations. The summary was aggregated from a mix of ExpressRoute-learned `/24`s and one VNet `/24`, and it only misbehaved when **Branch-to-Branch (b2b) was disabled**. Microsoft engineering had a root cause: during aggregation the generated `/16` can **inherit the attributes of whichever contributor "wins"**, and if it inherits the ExpressRoute-origin attributes it is classified **branch-derived** and dropped because b2b is off.

This post is the field report of trying to reproduce that race in a self-contained lab. The headline is uncomfortable and, I think, more useful than a clean "reproduced it" would have been:

- The **recommended mitigation works and is deterministic** — drop the ExpressRoute-learned contributors by AS-path **before** the summarization rule runs.
- The **advertised AS-path is the wrong signal**. A route-map can only summarize with the `Replace` action, and `Replace` **strips the AS-path and BGP communities**. So the aggregate you observe always carries the hub ASN `65515` and never the tell-tale `12076` — even in the failing case. You cannot confirm or deny the bug from the attributes on the wire.
- We **did not reproduce** the intermittent retirement across hundreds of forced recomputations, first at a 3:1 and then at a 63:1 ExpressRoute-to-VNet contributor ratio. That is a negative result, not proof of immunity.
- The most instructive moment was a **false positive**: the summary "retired" at one ExpressRoute location mid-run — and the cause was an out-of-band topology change, not the race. The route table told the truth the sampling flag could not.

The lab lives at `labs\vwan-routemap-summarization` in the `net-lab-builder` repo; evidence files are the numbered text captures under `show-output\round2`.

## The problem, precisely

A VWAN hub has an outbound route-map on a branch connection. One rule matches the `/24` contributors and **summarizes** them into `10.0.0.0/16`, which is advertised to the branch. The contributors reach the hub with **different origins**:

- several `/24`s learned over **ExpressRoute private peering**, each carrying the MSEE ASN **12076** in its AS-path — the "ExpressRoute origin" marker;
- one `/24` from a directly-attached **VNet**, carrying only the hub ASN **65515**.

Microsoft's paraphrased root cause:

> The `/16` summary is generated from contributors with different origins. During aggregation the summary may inherit the attributes of either contributor. If it inherits the VNet attributes it is advertised; if it inherits the ExpressRoute/branch-learned attributes it is treated as **branch-derived** and dropped because **Branch-to-Branch is disabled** — which is why the advertisement appears inconsistent across recomputation cycles.
>
> Recommended mitigation: a higher-priority outbound rule that **drops the ExpressRoute-learned contributors by AS-path (12076)** before the summarization rule runs.

Two facts make this hard to observe, and they are the heart of the post.

## Fact 1: `Replace` is the only way to summarize, and it erases the evidence

A Virtual WAN route-map has exactly one aggregation primitive: the **`Replace` route-prefix** action. There is no dedicated "summarize" or "aggregate" verb. So the customer's summarization rule is necessarily a `Replace`, and per the Microsoft Learn [route-maps documentation](https://learn.microsoft.com/en-us/azure/virtual-wan/route-maps-about):

> When using Route-maps to summarize a set of routes, the hub router strips the BGP Community and AS-PATH attributes from those routes.

That single sentence is why the bug is so slippery. The summary we observed at the branch **always** carried `65515` and **never** `12076`, in every case we tried — both contributors present, ExpressRoute-only, b2b on, b2b off. It is tempting to conclude that a `Replace`-generated summary, re-originated by the hub as `65515`, can never be classified branch-derived.

**That conclusion does not follow.** The AS-path strip governs the **advertised** attributes. Microsoft's bug is about an **internal origin/branch classification** that the aggregate inherits during recomputation — a flag that is not visible in the stripped AS-path. Microsoft explicitly states a `Replace`-generated `/16` *can* be treated as branch-derived and then dropped. So the AS-path on the wire is the wrong signal: it is always `65515` and can never reveal the branch classification.

**The only valid signal is presence versus absence of the `/16` at the branch across many recompute cycles.**

## Fact 2: Branch-to-Branch gates the transit, so the observation point must be a VPN branch

With b2b **disabled**, the ExpressRoute-learned `/24`s (AS `12076`) never reach the VPN branch at all; with b2b **enabled** they arrive as `65515 12076 133937`. ExpressRoute-to-ExpressRoute transit is unconditionally blocked, which means the second ExpressRoute circuit can never show the b2b-governed behaviour. The customer's condition — and the only place the bug can manifest — is a **VPN branch** hanging off the hub. In the lab that branch is an Azure Linux VM running StrongSwan and BIRD, so `birdc show route 10.0.0.0/16 all` is our ground truth.

## The lab

Two VWAN hubs, two ExpressRoute circuits in a **bow-tie**, fed by a **Megaport MCR** that injects the "on-prem" prefixes as free static routes over ExpressRoute private peering. The MSEE auto-prepends AS `12076` on every one of them — reproducing the customer's ExpressRoute-origin contributors with no on-prem site and no second cloud.

```
                 Megaport MCR (AS 133937)  —— static routes 10.0.1.0/24 … 10.0.63.0/24
                   /  bow-tie VXCs (ER private peering, MSEE prepends AS 12076)  \
        [ er-eu1 ] Frankfurt                                         [ er-eu2 ] Amsterdam
     ┌────────────────────────────────────┐                 ┌──────────────────────┐
     │   hub-eu1  (swedencentral)          │   bow-tie ER    │  hub-eu2 (westeurope) │
     │   VWAN Standard, b2b = DISABLED     │═════════════════│                       │
     │                                     │                 └──────────────────────┘
     │   spoke  10.0.128.0/24  ────────────┼── VNet contributor   (AS 65515)   ×1
     │   ER-learned 10.0.1…63.0/24 ────────┼── branch contributors (AS 12076)  ×63
     │                                     │
     │   route-map summarize-out:          │  match Contains 10.0.0.0/16 → Replace 10.0.0.0/16
     └──────────────┬──────────────────────┘
                    │ IPsec + BGP (connection cx-nva1)
            [ nva1 ] Azure VM  10.100.0.4  ASN 65001  (StrongSwan + BIRD2 — the VPN branch)
```

The summary under test is `10.0.0.0/16`, aggregated from one VNet contributor (`10.0.128.0/24`) and the ExpressRoute-learned `/24`s.

## What worked: the mitigation is deterministic

The mitigation route-map places a drop rule **before** the summarization rule on the VPN connection outbound:

| Order | Rule | Match | Action |
|---|---|---|---|
| 1 | `drop-er-12076` | `asPath Contains 12076` | **Drop** (terminate) |
| 2 | `sum1` | `routePrefix Contains 10.0.0.0/16` | **Replace** → `10.0.0.0/16` |

Because every ExpressRoute-learned contributor is removed from the aggregation input first, the `/16` can only ever be built from the VNet contributor. It can never be classified branch-derived, so it can never be dropped. At the branch the `/16` is present (`65515`) and every specific `/24` is gone — proof the summary is built from the VNet route alone. Full before/after RIB capture: `show-output\round2\65-vpnbranch-mitigation-validation.txt`.

This is the correct fix regardless of whether you can reproduce the race, because it eliminates the ambiguous input entirely.

## What did not happen: the race would not fire

To hunt the intermittent drop we built a sampling harness. Each cycle it forces a fresh hub aggregation by detaching and re-attaching the `summarize-out` route-map on the VPN connection, then densely polls the branch — 30 samples per cycle of `birdc show route 10.0.0.0/16 all` — and cross-checks the same `/16` at a second ExpressRoute MSEE route table.

- **N=20 cycles at a 3:1 ExpressRoute-to-VNet ratio: 600 dense samples, 0 drops, 0 anomalies.** The `/16` was present in every single sample; the two vantage points agreed every cycle. (`show-output\round2\71-race-sampling-summary.md`.)
- We then reasoned that skewing the ratio should raise the odds of a cycle where an ExpressRoute contributor "wins" the aggregation, so we **scaled the ExpressRoute-learned set from 3 to 63 `/24`s (63:1)** and re-ran.

Scaling the contributors is itself a two-step gotcha worth recording. On the Megaport MCR you must update **both** the VXC `ipRoutes` (so the router holds the static routes) **and** the BGP export prefix-filter-list (an allow-list of exactly which prefixes the MCR advertises to Azure). Add the routes without expanding the filter list and Azure never learns them; the BGP session looks healthy and nothing arrives.

At 63:1 the first nine cycles were again clean. And then the summary "retired" at the second ExpressRoute location — which is where the real lesson lives.

## The false positive, and why the route table wins

At cycle 10 the harness flagged an anomaly: the `/16` had vanished from the er-eu2 MSEE route table and stayed gone for several cycles, while the VPN branch still held it. That is *exactly* the customer's symptom — the summary present at one place and retired at another. It is very easy to declare victory here.

Independent verification against the authoritative layer said otherwise:

```powershell
az network express-route list-route-tables -g routemap-test-rg -n er-eu2 \
  --path primary --peering-name AzurePrivatePeering -o json
# er-eu2 now holds only 192.168.2.0/23 (AS 65515) — no /16, no specifics
```

The `/16` was genuinely gone from that MSEE, but not because of an aggregation race. Enumerating the ExpressRoute connections showed that the one connection carrying the summarizing route-map toward er-eu2 **no longer existed** — it had been deleted out-of-band for an unrelated ExpressRoute Standard-to-Local test. Once that connection was gone, nothing generated the `/16` toward er-eu2; the remaining connection to that circuit had no route-map. The "retirement" was a topology change, not the bug.

Two durable lessons:

1. **An anomaly flag is a hypothesis, not a finding.** Validate every apparent reproduction against the authoritative layer — here, the MSEE route table via `az network express-route list-route-tables` (which, by the way, returns empty in table format and must be read as JSON). The sampling harness measured a real absence; it could not know *why*.
2. **Long sampling runs are fragile to out-of-band change.** A multi-hour race hunt shares the subscription with whatever else you are doing. When the environment mutates mid-run, iterations after the change are contaminated. Record topology state alongside the samples so a later reader can tell a real race from an edited lab.

## Practical takeaways

- If you summarize mixed-origin routes with a Virtual WAN route-map and run with **Branch-to-Branch disabled**, add a higher-priority rule that **drops the ExpressRoute-learned contributors by AS-path (`12076`) before** the `Replace` summarization rule. It removes the ambiguous input and makes the summary deterministically VNet-derived.
- **Do not trust the advertised AS-path** to tell you whether the bug is present. `Replace` strips it to `65515`; the branch classification that drives the drop is invisible on the wire. Presence-versus-absence of the summary over many recomputations is the only observable signal.
- **Observe at a VPN branch**, not a second ExpressRoute circuit. ExpressRoute-to-ExpressRoute transit is unconditionally blocked, so the b2b-governed behaviour can only appear on a VPN branch.
- When a reproduction "fires," **confirm it at the authoritative routing layer** and **check for out-of-band changes** before you believe it.

## Reproduce it

The lab is Azure CLI plus a Megaport MCR, deployed with the `azure-lab` workflow. Contributors are free MCR static routes, so cost is dominated by the two ExpressRoute gateways and one VPN gateway. Evidence and the sampling harness are under `labs\vwan-routemap-summarization\show-output\round2`. See [references.md](./references.md) for the Microsoft Learn sources.

*This post documents a negative primary result and a corrected false positive. The mitigation is validated; the underlying race was not reproduced in this environment. Both are reported deliberately.*
