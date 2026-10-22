# Disabling VNet Peering Route Propagation on Azure `GatewaySubnet`: Fixing Asymmetric Routing with Summarized UDRs

In a classic Azure hub-and-spoke network with a central firewall or Network Virtual Appliance (NVA) in the hub VNet and a VPN or ExpressRoute Gateway in `GatewaySubnet`, you want **both** directions of traffic between on-premises and every spoke VNet to be inspected by the hub NVA.

As the number of spokes grows, administrators naturally want to configure a **single summarized User-Defined Route (UDR)** on `GatewaySubnet`—for example, `10.0.0.0/8 -> 10.0.1.4` (the hub NVA)—instead of maintaining dozens or hundreds of individual `/16` or `/24` spoke UDRs on `GatewaySubnet` and risking hitting the **400-route per route table limit**.

Until recently,Longest Prefix Match (LPM) made that impossible: every time you peered a new spoke VNet (`10.x.0.0/16`) with the hub, Azure automatically injected a more-specific `/16` system route (`NextHopType: VNetPeering`) into `GatewaySubnet`, overriding your `/8` summary UDR and sending inbound on-premises-to-spoke traffic **directly** to the spoke while outbound spoke-to-on-premises return traffic went through the hub NVA.

Azure's public preview feature **[Disable peering route propagation](https://learn.microsoft.com/en-us/azure/virtual-network/configure-disable-peering-route-propagation?tabs=cli)** (`--disable-peering-route All`, gated by `Microsoft.Network/AllowDisablePeeringRoutes`) solves this exact problem. In this post, we build a 10-spoke hub-and-spoke + S2S VPN + NVA lab in Azure (`swedencentral`) to inspect the control plane and packet-by-packet data plane in detail.

---

## 1. The Lab Topology

We deployed the following environment in `swedencentral`:

- **Simulated On-Premises VNet (`vnet-onprem`, `172.16.0.0/16`):**
  - `vm-onprem` (`172.16.1.4`): Ubuntu 22.04 VM running **StrongSwan** (route-based IKEv2 over `vti0`) and **FRR BGP** (`ASN 65010`), peered over a Site-to-Site IPsec VPN connection (`conn-hub-onprem`) with the hub VPN Gateway.
- **Hub VNet (`vnet-hub`, `10.0.0.0/16`):**
  - `GatewaySubnet` (`10.0.0.0/24`): Hosts `vpngw-hub` (`VpnGw1AZ`, `ASN 65515`, BGP peer IP `10.0.0.254`), associated with route table **`rt-gw`**.
  - `snet-nva` (`10.0.1.0/24`): Hosts **`vm-hub-nva`** (`10.0.1.4`), a Linux NVA with IP forwarding enabled and `iptables` rules that can toggle between **stateless** (`FORWARD ACCEPT` with directional packet counters) and **stateful** (`conntrack` dropping `ctstate INVALID` asymmetric replies).
  - `snet-hub-probe` (`10.0.2.0/24`): Hosts **`vm-hub-probe`** (`10.0.2.4`), associated with the **exact same `rt-gw` route table** as `GatewaySubnet`.
- **10 Spoke VNets (`vnet-spoke1` .. `vnet-spoke10`, `10.1.0.0/16` .. `10.10.0.0/16`):**
  - All 10 spokes are peered with `vnet-hub` (`AllowGatewayTransit = true` on hub, `UseRemoteGateways = true` on all 10 spokes).
  - `vnet-spoke1/snet-workload` (`10.1.1.0/24`) hosts **`vm-spoke1`** (`10.1.1.4`, running an HTTP server on TCP port 80) and is associated with route table **`rt-spoke1`** (`disableBgpRoutePropagation = true`, with UDRs `172.16.0.0/16 -> 10.0.1.4` and `10.0.0.0/8 -> 10.0.1.4`).

```
+-----------------------------------------------------------------------------------+
| Simulated On-Premises VNet: vnet-onprem (172.16.0.0/16)                           |
|   snet-onprem (172.16.1.0/24)                                                     |
|     [vm-onprem: 172.16.1.4 | StrongSwan IKEv2 + FRR BGP ASN 65010]                |
+-----------------------------------------+-----------------------------------------+
                                          | S2S IPsec VPN + eBGP (vti0)
                                          v
+-----------------------------------------------------------------------------------+
| Hub VNet: vnet-hub (10.0.0.0/16)                                                  |
|                                                                                   |
|   GatewaySubnet (10.0.0.0/24)  <--- Route Table: rt-gw                            |
|     [vpngw-hub: VpnGw1AZ | ASN 65515 | BGP IP 10.0.0.254]                         |
|                                                                                   |
|   snet-hub-probe (10.0.2.0/24) <--- Route Table: rt-gw (effective route observer) |
|     [vm-hub-probe: 10.0.2.4]                                                      |
|                                                                                   |
|   snet-nva (10.0.1.0/24)                                                          |
|     [vm-hub-nva: 10.0.1.4 | IP Forwarding + iptables conntrack/LOG]               |
+-----+-------+-------+-------+-------+-------+-------+-------+-------+-------+-----+
      |       |       |       |       |       |       |       |       |       |
      | VNet Peerings (AllowGatewayTransit = true / UseRemoteGateways = true) |
      v       v       v       v       v       v       v       v       v       v
  +-------+ +---+   +---+   +---+   +---+   +---+   +---+   +---+   +---+  +----+
  |Spoke 1| |S2 |   |S3 |   |S4 |   |S5 |   |S6 |   |S7 |   |S8 |   |S9 |  |S10 |
  |10.1/16| |10.2   |10.3   |10.4   |10.5   |10.6   |10.7   |10.8   |10.9  |10.10
  +---+---+ +---+   +---+   +---+   +---+   +---+   +---+   +---+   +---+  +----+
      |
      +-- snet-workload (10.1.1.0/24) <--- Route Table: rt-spoke1 (BGP prop disabled)
            [vm-spoke1: 10.1.1.4 | Python HTTP server :80]
```

> **Pro tip — How to inspect `GatewaySubnet`'s effective routes:** Azure does not expose `az network nic show-effective-route-table` for the managed NICs inside a VPN or ExpressRoute Gateway. By associating a lightweight probe subnet (`snet-hub-probe` with `nic-vm-hub-probe`) in the same hub VNet to the **same `rt-gw` route table**, you can run `az network nic show-effective-route-table` on `nic-vm-hub-probe` to see the exact `Default`, `VNetPeering`, `VirtualNetworkGateway`, and `User` routes evaluated on `rt-gw`.

First, let's verify that `vpngw-hub` advertises the hub (`10.0.0.0/16`) and all 10 peered spokes (`10.1.0.0/16` .. `10.10.0.0/16`) over eBGP to `vm-onprem`:

```text
# On vm-onprem (vtysh -c "show ip bgp summary" && vtysh -c "show ip route bgp")
Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.0.254      4      65515         3         5        0    0    0 00:00:07           11       12 N/A

B>  10.0.0.0/16 [20/0] via 10.0.0.254 (recursive), weight 1, 00:00:07
  *                      via 10.0.0.254, vti0 onlink, weight 1, 00:00:07
B>  10.1.0.0/16 [20/0] via 10.0.0.254 (recursive), weight 1, 00:00:07
...
B>  10.10.0.0/16 [20/0] via 10.0.0.254 (recursive), weight 1, 00:00:07
```

And on the Azure side (`az network vnet-gateway list-learned-routes` and `list-advertised-routes`):

```text
# Learned routes on vpngw-hub
Network        NextHop     Origin    SourcePeer    AsPath    Weight
-------------  ----------  --------  ------------  --------  --------
10.0.0.0/16                Network   10.0.0.254              32768
10.1.0.0/16                Network   10.0.0.254              32768
...
10.10.0.0/16               Network   10.0.0.254              32768
172.16.0.0/16  172.16.1.4  EBgp      172.16.1.4    65010     32768
```

---

## 2. Scenario 1: The Asymmetric Routing Trap (`disablePeeringRoute = None` + Summarized `10.0.0.0/8` UDR)

Suppose we configure `rt-gw` (attached to `GatewaySubnet`) with a single summarized UDR for all spokes:

```bash
az network route-table route create \
  -g rg-disable-peering-routes-lab \
  --route-table-name rt-gw \
  -n route-to-spokes-summary \
  --address-prefix 10.0.0.0/8 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.1.4
```

When we inspect the effective routes on `rt-gw` (`az network nic show-effective-route-table -g rg-disable-peering-routes-lab -n nic-vm-hub-probe -o table`), we see why the `/8` summary route fails to attract traffic destined for `10.1.1.4`:

```text
Source                 State    Address Prefix    Next Hop Type          Next Hop IP
---------------------  -------  ----------------  ---------------------  --------------
Default                Active   10.0.0.0/16       VnetLocal
Default                Active   10.1.0.0/16       VNetPeering
Default                Active   10.2.0.0/16       VNetPeering
Default                Active   10.3.0.0/16       VNetPeering
Default                Active   10.4.0.0/16       VNetPeering
Default                Active   10.5.0.0/16       VNetPeering
Default                Active   10.6.0.0/16       VNetPeering
Default                Active   10.7.0.0/16       VNetPeering
Default                Active   10.8.0.0/16       VNetPeering
Default                Active   10.9.0.0/16       VNetPeering
Default                Active   10.10.0.0/16      VNetPeering
VirtualNetworkGateway  Active   172.16.0.0/16     VirtualNetworkGateway  20.240.221.177
VirtualNetworkGateway  Active   172.16.1.4/32     VirtualNetworkGateway  20.240.221.177
Default                Active   0.0.0.0/0         Internet
...
User                   Active   10.0.0.0/8        VirtualAppliance       10.0.1.4
```

Even though our `User` route (`10.0.0.0/8 -> 10.0.1.4`) is `Active`, all 10 `Default` `VNetPeering` routes (`10.1.0.0/16` .. `10.10.0.0/16`) are **also `Active`** and have a longer prefix length (`/16` vs `/8`).

### What happens on the wire?

1. **Forward path (`vm-onprem 172.16.1.4 -> vm-spoke1 10.1.1.4`):**
   - Packet arrives at `vpngw-hub` over IPsec.
   - `vpngw-hub` looks up `10.1.1.4`, matches `Default 10.1.0.0/16 -> VNetPeering` (beating `10.0.0.0/8`), and sends the packet **directly to `vm-spoke1`**, completely bypassing `vm-hub-nva` (`10.0.1.4`).
2. **Return path (`vm-spoke1 10.1.1.4 -> vm-onprem 172.16.1.4`):**
   - `vm-spoke1` looks up `172.16.1.4` in `rt-spoke1`, matches `User 172.16.0.0/16 -> VirtualAppliance 10.0.1.4`, and sends the reply (`ICMP Echo Reply` or `TCP SYN-ACK`) to `vm-hub-nva` (`10.0.1.4`).

We can prove this with directional `iptables` counters on `vm-hub-nva`:

- **When `vm-hub-nva` is stateless (`iptables -P FORWARD ACCEPT`):**
  Ping (`3/3`) and `curl http://10.1.1.4` (`200 OK`) succeed from `vm-onprem`, masking the bug! However, `iptables -L FORWARD -v -n` on `vm-hub-nva` reveals the asymmetry:
  ```text
  Chain FORWARD (policy ACCEPT 8 packets, 747 bytes)
   pkts bytes target     prot opt in     out     source               destination         
      0     0 LOG        all  --  *      *       172.16.0.0/16        10.0.0.0/8           LOG flags 0 level 4 prefix "NVA_FWD_ONPREM_TO_SPOKE: "
      8   747 LOG        all  --  *      *       10.0.0.0/8           172.16.0.0/16        LOG flags 0 level 4 prefix "NVA_FWD_SPOKE_TO_ONPREM: "
  ```
  Zero packets (`0 bytes`) went from on-premises to the spoke through the NVA, while all `8` reply packets (`747 bytes`) returned through the NVA!

- **When `vm-hub-nva` is stateful (standard firewall behavior with `conntrack`):**
  Both `ping` and `curl http://10.1.1.4` **fail completely** (`100% packet loss` and connection timeout):
  ```text
  === [S1 Stateful] Ping 10.1.1.4 from 172.16.1.4 ===
  PING 10.1.1.4 (10.1.1.4) from 172.16.1.4 : 56(84) bytes of data.
  --- 10.1.1.4 ping statistics ---
  3 packets transmitted, 0 received, 100% packet loss, time 2061ms

  === [S1 Stateful] HTTP GET http://10.1.1.4 from 172.16.1.4 ===
  curl: (28) Connection timed out after 5001 milliseconds
  ```
  Checking `vm-hub-nva`'s stateful `FORWARD` counters and kernel log shows why:
  ```text
  pkts bytes target     prot opt in     out     source               destination         
     0     0 LOG        all  --  *      *       172.16.0.0/16        10.0.0.0/8           LOG flags 0 level 4 prefix "NVA_FWD_ONPREM_TO_SPOKE: "
    11   732 LOG        all  --  *      *       10.0.0.0/8           172.16.0.0/16        LOG flags 0 level 4 prefix "NVA_FWD_SPOKE_TO_ONPREM: "
     0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
     0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate NEW tcp flags:0x17/0x02
     0     0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate NEW icmptype 8
    11   732 LOG        all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate INVALID LOG flags 0 level 4 prefix "NVA_DROP_ASYM_INVALID: "
    11   732 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate INVALID

  [ 1983.344746] NVA_DROP_ASYM_INVALID: IN=eth0 OUT=eth0 SRC=10.1.1.4 DST=172.16.1.4 LEN=60 PROTO=TCP SPT=80 DPT=46380 ACK SYN
  ```
  Because the NVA never saw the initial TCP `SYN` or ICMP Echo Request, Linux `conntrack` classifies `vm-spoke1`'s `SYN-ACK` and Echo Reply as `ctstate INVALID` and drops every packet.

---

## 3. Scenario 2: Suppressing Peering Routes on `rt-gw` (`--disable-peering-route All` vs. Explicit `/16` UDRs)

### How `disablePeeringRoute = All` works

The new route table property `disablePeeringRoute` (CLI flag `--disable-peering-route All`) instructs Azure not to propagate `VNetPeering` routes (nor `VirtualNetworkGateway` routes learned via peering) into subnets associated with that route table:

```bash
# 1. Register the preview feature flag
az feature register --namespace Microsoft.Network --name AllowDisablePeeringRoutes
az provider register --namespace Microsoft.Network

# 2. Disable peering route propagation on the GatewaySubnet route table
az network route-table update \
  -g rg-disable-peering-routes-lab \
  -n rt-gw \
  --disable-peering-route All
```

### Important Operational Gotcha: `AllowDisablePeeringRoutes` is `ApprovalRequired`

While testing this feature in our subscription, we noticed that `az feature show --namespace Microsoft.Network --name AllowDisablePeeringRoutes` remained in `Pending` state well past the 15-minute window mentioned in the docs. Querying the underlying `subscriptionFeatureRegistrations` resource via `az feature registration show` explains why:

```json
{
  "name": "AllowDisablePeeringRoutes",
  "properties": {
    "approvalType": "ApprovalRequired",
    "description": "Enabling customers to use newly created feature AllowDisablePeeringRoutes in their routes",
    "providerNamespace": "Microsoft.Network",
    "releaseDate": "2025-08-20T22:51:47.519752+00:00",
    "state": "Pending"
  }
}
```

Because `"approvalType"` is `"ApprovalRequired"` (rather than `"AutoApproval"`), registering the feature submits an approval request to the Azure Virtual Network product team. If you run `az network route-table update --disable-peering-route All` while the feature is still `Pending`, ARM rejects the call with:

```text
ERROR: (UnauthorizedClientApplication) Unauthorized client application id DisablePeeringRoute is not supported.
```

> **Note:** Even when `disablePeeringRoute = All` is active on `GatewaySubnet`'s route table (`rt-gw`), **the VPN/ExpressRoute Gateway itself still advertises all peered spoke prefixes (`10.1.0.0/16` .. `10.10.0.0/16`) to on-premises via BGP**. Why? Because an Azure Virtual Network Gateway advertises the address space of the hub VNet and all peered spoke VNets from the VNet control-plane topology, not by redistributing `GatewaySubnet`'s effective route table. Disabling peering route propagation on `rt-gw` only changes how the gateway forwards **inbound packets after decapsulation** inside Azure.

### Verifying the Symmetric Data Plane (Explicit `/16` UDRs vs. `disablePeeringRoute = All`)

Until `AllowDisablePeeringRoutes` is approved on a subscription, the only way to prevent `GatewaySubnet`'s 10 `VNetPeering` routes from overriding the NVA path is to configure 10 explicit `/16` UDRs (`10.1.0.0/16` .. `10.10.0.0/16 -> 10.0.1.4`) on `rt-gw`.

Let's compare both approaches on `rt-gw`:

| Characteristic | Without `disablePeeringRoute` (Explicit `/16` UDRs) | With `--disable-peering-route All` |
|----------------|-----------------------------------------------------|------------------------------------|
| **UDRs required on `rt-gw`** | $N$ routes (one matching `/16` UDR per spoke VNet) | **1 route** (`10.0.0.0/8 -> 10.0.1.4`) |
| **Day-2 operation when adding Spoke 11** | Must update `rt-gw` with a new `/16` UDR | **Zero route table changes** (`10.0.0.0/8` automatically covers it) |
| **400-UDR limit risk** | High when spoke VNets have multiple address prefixes | Eliminated |
| **State of `VNetPeering` routes on `rt-gw`** | `Invalid` (shadowed by matching `/16` UDRs) | Removed from effective route table |

When we apply the `/16` UDRs on `rt-gw`, `az network nic show-effective-route-table -g rg-disable-peering-routes-lab -n nic-vm-hub-probe -o table` shows all 10 `VNetPeering` routes invalidated:

```text
Source                 State    Address Prefix    Next Hop Type          Next Hop IP
---------------------  -------  ----------------  ---------------------  --------------
Default                Active   10.0.0.0/16       VnetLocal
Default                Invalid  10.10.0.0/16      VNetPeering
Default                Invalid  10.1.0.0/16       VNetPeering
Default                Invalid  10.2.0.0/16       VNetPeering
...
Default                Invalid  10.9.0.0/16       VNetPeering
VirtualNetworkGateway  Active   172.16.0.0/16     VirtualNetworkGateway  20.240.221.177
User                   Active   10.0.0.0/8        VirtualAppliance       10.0.1.4
User                   Active   10.1.0.0/16       VirtualAppliance       10.0.1.4
...
User                   Active   10.10.0.0/16      VirtualAppliance       10.0.1.4
```

Now, with `vm-hub-nva` still in **strict stateful firewall mode**, we re-test `ping` and `curl http://10.1.1.4` from `vm-onprem` (`172.16.1.4`):

```text
=== [S2 Workaround Stateful] Ping 10.1.1.4 from 172.16.1.4 ===
PING 10.1.1.4 (10.1.1.4) from 172.16.1.4 : 56(84) bytes of data.
64 bytes from 10.1.1.4: icmp_seq=1 ttl=63 time=4.21 ms
64 bytes from 10.1.1.4: icmp_seq=2 ttl=63 time=2.97 ms
64 bytes from 10.1.1.4: icmp_seq=3 ttl=63 time=2.92 ms

--- 10.1.1.4 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms

=== [S2 Workaround Stateful] HTTP GET http://10.1.1.4 from 172.16.1.4 ===
< HTTP/1.0 200 OK
SPOKE1_OK hostname=vm-spoke1 ip=10.1.1.4
```

And `iptables -L FORWARD -v -n` on `vm-hub-nva` confirms **100% symmetric traversal** (`8` forward packets from `172.16.1.4 -> 10.1.1.4`, `8` return packets from `10.1.1.4 -> 172.16.1.4`, and `0` `ctstate INVALID` drops):

```text
Chain FORWARD (policy DROP 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    8   592 LOG        all  --  *      *       172.16.0.0/16        10.0.0.0/8           LOG flags 0 level 4 prefix "NVA_FWD_ONPREM_TO_SPOKE: "
    8   747 LOG        all  --  *      *       10.0.0.0/8           172.16.0.0/16        LOG flags 0 level 4 prefix "NVA_FWD_SPOKE_TO_ONPREM: "
   14  1195 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
    1    60 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate NEW tcp flags:0x17/0x02
    1    84 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate NEW icmptype 8
    0     0 LOG        all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate INVALID LOG flags 0 level 4 prefix "NVA_DROP_ASYM_INVALID: "
    0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate INVALID
```

---

## 4. Scenario 3: Why You Must NOT Enable `disablePeeringRoute = All` on Spoke Route Tables

A natural follow-up question is: *"Can I also enable `--disable-peering-route All` on my spoke route tables (`rt-spoke1`) so spoke subnets don't learn peering routes?"*

If your NVA lives in the **peered hub VNet** (`10.0.1.4` in `vnet-hub`), the answer is **No**. Microsoft's documentation notes this limitation:

> *Traffic drops if you configure a user-defined route (UDR) with a virtual appliance next hop located in a peered virtual network and disable peering routes on that subnet.*

Looking at `nic-vm-spoke1`'s effective route table (`az network nic show-effective-route-table -g rg-disable-peering-routes-lab -n nic-vm-spoke1 -o table`) makes the reason crystal clear:

```text
Source    State    Address Prefix    Next Hop Type     Next Hop IP
--------  -------  ----------------  ----------------  -------------
Default   Active   10.1.0.0/16       VnetLocal
Default   Active   10.0.0.0/16       VNetPeering
Default   Active   0.0.0.0/0         Internet
...
User      Active   172.16.0.0/16     VirtualAppliance  10.0.1.4
User      Active   10.0.0.0/8        VirtualAppliance  10.0.1.4
```

When `vm-spoke1` (`10.1.1.4`) sends a packet matching `172.16.0.0/16 -> VirtualAppliance 10.0.1.4`, Azure's SDN fabric must resolve how to reach the next-hop IP `10.0.1.4`. Because `10.0.1.4` is not in `vnet-spoke1` (`10.1.0.0/16`), Azure resolves `10.0.1.4` recursively using the system route `Default 10.0.0.0/16 -> VNetPeering`.

- **On `GatewaySubnet` (`rt-gw`):** The NVA (`10.0.1.4`) is in the **same hub VNet** (`10.0.0.0/16`), so `rt-gw` resolves `10.0.1.4` via `Default 10.0.0.0/16 -> VnetLocal` (which is **not** removed by `--disable-peering-route All`). And when `vm-hub-nva` forwards the packet to `vm-spoke1` (`10.1.1.4`), `snet-nva` uses its own route table where `10.1.0.0/16 -> VNetPeering` is still active!
- **On `vnet-spoke1/snet-workload` (`rt-spoke1`):** The NVA (`10.0.1.4`) is in a **peered VNet** (`vnet-hub`). Disabling peering routes on `rt-spoke1` removes `10.0.0.0/16 -> VNetPeering`, leaving `vnet-spoke1` with no underlay path to reach the NVA next hop `10.0.1.4`.

---

## 5. Key Takeaways

1. **Where to use `--disable-peering-route All`:** Enable it on **`GatewaySubnet`** (or hub subnets whose UDR next hop is a local hub NVA) so that a single summarized UDR (`10.0.0.0/8 -> <Hub-NVA-IP>`) can steer all inbound traffic to all peered spokes without being overridden by `/16` or `/24` `VNetPeering` routes.
2. **Where NOT to use `--disable-peering-route All`:** Do **not** enable it on **`snet-nva`** (the NVA itself still needs the `VNetPeering` routes to forward inspected traffic to the spokes!) and do **not** enable it on **spoke subnets** whose UDR next hop is an NVA in the peered hub VNet.
3. **BGP advertisement is unaffected:** Disabling peering route propagation on `GatewaySubnet` does not stop the Azure VPN/ExpressRoute Gateway from advertising peered spoke prefixes to on-premises via BGP.
4. **Check feature approval before rollout:** `Microsoft.Network/AllowDisablePeeringRoutes` currently has `approvalType: ApprovalRequired` (`az feature registration show --provider-namespace Microsoft.Network --name AllowDisablePeeringRoutes`). Verify that its state has transitioned from `Pending` to `Registered` before applying `--disable-peering-route All` in production pipelines.
