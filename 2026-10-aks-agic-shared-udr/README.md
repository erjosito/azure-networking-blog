# One route table for AKS nodes and Application Gateway: no second table to maintain

Lab: tested 9 Oct; resources cleaned up 12 October 2026. [Cleanup evidence](https://github.com/erjosito/net-lab-builder/tree/main/labs/aks-agic-shared-udr/show-output/cleanup-20261012T0728Z).

With kubenet, AKS writes a route per node so traffic can reach each node's pod CIDR. If Application Gateway (AGIC backends) sits in the same VNet, it needs those pod routes too. Associating **one shared route table** with both the AKS node subnet and the Application Gateway subnet lets the gateway use the routes AKS already maintains. A separate gateway table would need its own pod routes, kept in step with the nodes and pod CIDRs.

The experiment also tested Internet egress via an NVA: Azure rejected a plain default route; split defaults hid backend health; adding `GatewayManager → Internet` restored health. These are troubleshooting observations, not a supported design.

## Who owns the routes?

| | Shared table | Separate gateway table |
|---|---|---|
| Pod routes (`10.244.0.0/24 → node`) | Written by AKS, used by both subnets | Must also be present in the gateway table |
| Operator-owned routes (egress, exceptions) | One place | Two tables to keep consistent |
| Drift risk | Gateway follows AKS-managed routes | Pod routes can go stale when nodes or pod CIDRs change |

A second table is not necessarily manual: tooling, including AGIC, can manage route-table association. The shared table simply removes the need to synchronise pod routes between two tables, so there is less to drift.

In this lab, AKS populated the pod route and AGIC configured the backend. Neither a second table nor manual backend IP entry was needed.

```text
Spoke VNet 10.21.0.0/16

  rt-shared (one table, associated with BOTH subnets below)
     10.244.0.0/24 -> VirtualAppliance 10.21.1.4   (written by AKS)
     operator routes: default / egress / exceptions

  Application Gateway Standard_v2, subnet 10.21.2.0/24  -- rt-shared
      | pod route
      v
  AKS kubenet node 10.21.1.4, subnet 10.21.1.0/24       -- rt-shared
      +-- workload pod 10.244.0.14
              | external destinations
              v
  VNet peering -> Hub NVA 10.20.1.4 -> Internet (source NAT)
```

One-node Sweden Central cluster, `loadBalancer` outbound type (not `userDefinedRouting`). The NVA had Azure NIC and Linux forwarding enabled, plus source NAT. The gateway had public and private frontends. It was **legacy, non-isolated Application Gateway v2** (`EnableApplicationGatewayNetworkIsolation` was `NotRegistered`). Do not transfer the results to network-isolated gateways or other AKS networking models.

## The catch: egress shares the table too

Every operator route added for the nodes also applies to the gateway subnet. Forcing Internet egress through an NVA collides with Application Gateway v2 requirements.

| State | Routing change | Pod Internet source IP | Backend health |
|---|---|---|---|
| Baseline | `0/0 → Internet`, AKS pod route retained | Not captured | Healthy, HTTP 200 probe |
| Literal default attempt | `0/0` next hop to NVA | No running variant | Write rejected; baseline unchanged |
| Split-default control | Add `0/1` and `128/1` to NVA | NVA public IP, two endpoints | Unknown in seven queries |
| Treatment | Add only `GatewayManager → Internet` | Same NVA public IP | Healthy in two consecutive queries |

**Baseline.** The table held `0.0.0.0/0 → Internet` and `10.244.0.0/24 → VirtualAppliance 10.21.1.4`. Both backend settings reported pod `10.244.0.14` `Healthy` (HTTP 200). A request from the NVA to the private frontend also returned 200; that follows the more-specific peering path and proves frontend access, not pod egress through the NVA.

**Rejection.** Changing the default to `VirtualAppliance 10.20.1.4` returned `ApplicationGatewaySubnetUserDefinedRouteNotAllowed`: `0.0.0.0/0` must use next hop type `Internet`. Table and associations were unchanged.

**Control.** `0.0.0.0/1` and `128.0.0.0/1` to `10.20.1.4` were admitted. By longest-prefix match they beat the retained `/0 → Internet`, except where a more-specific route (such as the pod peering route) wins. Pod requests returned the NVA's public IP from both `api.ipify.org` and `ifconfig.me/ip`. Seven backend-health queries returned `Unknown`, the last more than ten minutes after admission:

```text
address: 10.244.0.14
health: Unknown
healthProbeLog: Unable to retrieve health status data.
Check presence of NSG/UDR blocking access to ports 65503-65534
from Internet to Application Gateway.
```

The CLI exited with code 0. `Unknown` is not `Unhealthy`; command success and useful health data are separate checks.

**Treatment.** With the control left intact, adding only `GatewayManager -> Internet` to the same table (no gateway, NSG, AKS or pod change) gave a first Healthy query at **13:13:31 UTC**, 4m 52s after admission at 13:08:39 UTC. A second query at 13:15:02 UTC confirmed it. **4m 52s is an observation upper bound, not exact convergence time.** Source-IP checks still returned the NVA address afterwards.

## Scale-out check

To check AGIC's response to a new replica:

```powershell
kubectl scale deployment web -n default --replicas=2
kubectl rollout status deployment/web -n default --timeout=120s
kubectl get pods -n default -l app=web -o wide
kubectl get endpointslices -n default -l kubernetes.io/service-name=web -o wide
kubectl logs -n kube-system -l app=ingress-appgw --tail=400 --timestamps
az network application-gateway address-pool show -g rg-aks-agic-shared-udr --gateway-name agw1 -n pool-default-web-80-bp-80 -o json
az network application-gateway show-backend-health -g rg-aks-agic-shared-udr -n agw1 -o json
```

Captured 9 October: rollout added `10.244.0.18` beside `10.244.0.14`; AGIC logged an applied configuration about 14 seconds after scale. The first valid pool query (~112 seconds after scale) showed both IPs; both later reported Healthy on public and private HTTP settings. This demonstrates configuration update and backend health, not full control-plane validation. Both pods were on one node; post-scale egress and pre/post route comparison were inconclusive. [Offline evidence and caveats](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/show-output/scale-two-validation-20261009T1454Z/validation-verdict.md).

## Takeaways

- Share the table to avoid maintaining pod routes twice; keep operator routes minimal because the gateway inherits them.
- After a routing change, check admission, forwarding from the actual workload, and backend-health visibility separately.
- Backend health recovered, but this does not validate all Application Gateway control-plane functions, stability, logs, metrics, or public-client ingress/return. Treatment remained through the experiment; the lab has since been cleaned up.

**Not a production recommendation:** forcing Internet egress through an NVA is unsupported for non-isolated v2. Accepted `/1` routes and recovery with a `GatewayManager` exception are not support endorsements.

## Evidence and documentation

- [Baseline verdict and captures](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/baseline-verdict.md)
- [Literal-default rejection](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/show-output/forced-control-mutation-20261009T1241Z/verdict.json)
- [Split-default control verdict](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/show-output/split-default-validation-20261009T1254Z/split-default-control-verdict.md)
- [Treatment verdict, timings and decisive capture names](https://github.com/erjosito/net-lab-builder/blob/main/labs/aks-agic-shared-udr/show-output/gatewaymanager-validation-20261009T1309Z/treatment-verdict.md)
- Microsoft Learn: [Application Gateway infrastructure and UDR restrictions](https://learn.microsoft.com/azure/application-gateway/configuration-infrastructure), [AKS kubenet routing](https://learn.microsoft.com/azure/aks/configure-kubenet), [service tags in UDRs](https://learn.microsoft.com/azure/virtual-network/service-tags-overview).