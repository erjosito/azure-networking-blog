# AKS kubenet, AGIC and a shared UDR: why Healthy is not the whole story

**Draft for review. Experiment captured on 9 October 2026.**

An Application Gateway backend can disappear from health reporting while its AKS pod still reaches the Internet through your network virtual appliance. Adding `GatewayManager → Internet` restored backend-health visibility without changing the pod's observed public source IP. That is a troubleshooting distinction, not a supported forced-tunneling recipe.

Azure rejected the ordinary `0.0.0.0/0 → NVA` route. The running comparison used two more-specific `/1` routes instead. Admission, forwarding and supportability are different questions. This bounded experiment answered the first two, not the third.

## One table, two very different jobs

Application Gateway Ingress Controller (AGIC) configures pod backends. Kubenet pods are not ordinary VNet addresses: AKS writes per-node routes to reach their ranges.

The **same user-defined route (UDR) table** served the AKS node and Application Gateway subnets. AKS populated the pod route; AGIC configured the backend. Neither required manual backend IP entry or a second table.

```text
Spoke VNet 10.21.0.0/16
  Application Gateway Standard_v2, subnet 10.21.2.0/24
      |
      | pod route: 10.244.0.0/24 -> node 10.21.1.4
      v
  AKS kubenet node, subnet 10.21.1.0/24
      |
      +-- workload pod 10.244.0.14
              |
              | external destinations matched by the two /1 routes
              v
  VNet peering -> Hub NVA 10.20.1.4 -> Internet (source NAT)

  rt-shared is attached to BOTH spoke subnets.
  Treatment adds GatewayManager -> Internet to this same table.
```

This one-node Sweden Central cluster used `loadBalancer` outbound type, not `userDefinedRouting`. The NVA had Azure NIC and Linux forwarding enabled, plus source NAT. The gateway had public and private frontends.

This was **legacy, non-isolated Application Gateway v2**: `EnableApplicationGatewayNetworkIsolation` was `NotRegistered`. Do not transfer results to network-isolated gateways or other AKS networking models.

## The comparison at a glance

| State | Routing change | Pod Internet source IP | Backend health |
|---|---|---|---|
| Baseline | `0/0 → Internet`, AKS pod route retained | Not captured in baseline | Healthy, HTTP 200 probe |
| Literal default attempt | Change `0/0` next hop to NVA | No running variant | Write rejected; baseline unchanged |
| Split-default control | Add `0/1` and `128/1` to NVA | NVA public IP, two endpoints | Unknown in seven queries |
| Treatment | Add only `GatewayManager → Internet` | Same NVA public IP | Healthy in two consecutive queries |

Baseline pod egress was **not captured**; no baseline-to-control IP comparison is claimed.

### Baseline: prove the shared-table plumbing first

The shared table contained:

```text
0.0.0.0/0       -> Internet
10.244.0.0/24   -> VirtualAppliance 10.21.1.4
```

Both gateway backend settings reported pod `10.244.0.14` as `Healthy`, with `Success. Received 200 status code`. A request from the NVA to the private frontend also returned HTTP 200.

That private request follows the more-specific peering path. It proves frontend access, not NVA transit for pod Internet traffic.

### Admission: the literal default never became a running test

Changing the default to `VirtualAppliance 10.20.1.4` returned:

```text
ApplicationGatewaySubnetUserDefinedRouteNotAllowed
For routes associated to subnet containing Application Gateway V2,
please ensure '0.0.0.0/0' uses NextHopType as 'Internet'.
```

Default, pod route and associations stayed unchanged. This was rejection, not gateway failure. Unlike the initial design, the running test used an approved split-default variant.

### Control: admitted routes, lost health visibility

The two added routes were:

```text
0.0.0.0/1      -> VirtualAppliance 10.20.1.4
128.0.0.0/1    -> VirtualAppliance 10.20.1.4
```

Together they cover IPv4 and beat the retained `0.0.0.0/0 → Internet` by longest-prefix matching, unless another more-specific route wins. An Internet default in the table does not mean packets select it.

Requests originating inside the existing pod returned the NVA's public source IP from **both** `api.ipify.org` and `ifconfig.me/ip`. Independently, seven backend-health queries reported `Unknown`; the last observation completed more than ten minutes after route admission.

Health detail, with resource identifiers omitted:

```text
address: 10.244.0.14
health: Unknown
healthProbeLog: Unable to retrieve health status data.
Check presence of NSG/UDR blocking access to ports 65503-65534
from Internet to Application Gateway.
```

The CLI **exited with code 0**. Health visibility failed, not the API invocation. `Unknown` is not `Unhealthy`: it does not prove an application probe failed. Command success and useful health data are separate checks.

### Treatment: one exception, the same pod

With the verified control left intact, the treatment added only:

```text
GatewayManager -> Internet
```

No gateway, NSG, AKS outbound-type or pod configuration was changed. The pod route, both `/1` routes and the literal Internet default remained.

The first healthy query completed at **13:13:31 UTC**, 4m 52s after exception admission at 13:08:39 UTC. Both backend settings reported the same pod Healthy, with HTTP 200 probe details. A second query at 13:15:02 UTC confirmed Healthy.

**4m 52s is an observation upper bound, not exact convergence time.** Recovery could occur between observations. Both source-IP checks still returned the NVA address, also after the confirming health query.

This proves neither universal management reachability nor the egress path for every destination.

## What to take into troubleshooting, and what not to deploy

After a routing change, inspect separately:

1. **Admission:** did Azure accept the route, or reject it without changing the table?
2. **Forwarding:** did a request from the actual workload use the expected egress address?
3. **Visibility:** did backend-health return known states, not merely exit successfully?

Preserve backends, pod routes and observation points. Repeat queries; separate HTTP tests from health API results.

**Not a production recommendation:** forced tunneling is unsupported for this non-isolated v2 scenario. Accepted `/1` routes and recovery with a `GatewayManager` exception are not support endorsements.

Treatment was retained at the user's request, **not restored** to baseline. Two healthy queries do not prove long-term stability, provisioning, logs, metrics, or public-client ingress and return-path correctness.

**Pod reachability, routing admission and health visibility can diverge, even with one shared table.**

## Evidence and documentation

- [Baseline verdict and captures](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/baseline-verdict.md)
- [Literal-default rejection](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/show-output/forced-control-mutation-20261009T1241Z/verdict.json)
- [Split-default control verdict](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/show-output/split-default-validation-20261009T1254Z/split-default-control-verdict.md)
- [Treatment verdict, timings and decisive capture names](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/show-output/gatewaymanager-validation-20261009T1309Z/treatment-verdict.md)
- Microsoft Learn: [Application Gateway infrastructure and UDR restrictions](https://learn.microsoft.com/azure/application-gateway/configuration-infrastructure), [AKS kubenet routing](https://learn.microsoft.com/azure/aks/configure-kubenet), [service tags in UDRs](https://learn.microsoft.com/azure/virtual-network/service-tags-overview).
