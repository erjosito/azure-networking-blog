# Disabling VNet Peering Route Propagation on Azure `GatewaySubnet` and SD-WAN Subnets: Fixing Asymmetric Routing Across S2S VPN, SD-WAN, and ExpressRoute with Summarized UDRs

In a classic Azure hub-and-spoke network with a central firewall or Network Virtual Appliance (NVA) in the hub VNet and multiple hybrid connectivity paths (Site-to-Site VPN, ExpressRoute, and SD-WAN appliances), you want **both** directions of traffic between every on-premises site and every spoke VNet to be inspected by the central hub NVA.

As the number of spokes grows, administrators naturally want to configure a **single summarized User-Defined Route (UDR)** on `GatewaySubnet` and on any hub SD-WAN subnet (for example, `10.0.0.0/8 -> 10.0.1.4`, the central hub NVA) instead of maintaining dozens or hundreds of individual `/16` or `/24` spoke UDRs and risking hitting the **400-route per route table limit**.

Until recently, Longest Prefix Match (LPM) made that impossible: every time you peered a new spoke VNet (`10.x.0.0/16`) with the hub, Azure automatically injected a more-specific `/16` system route (`NextHopType: VNetPeering`) into `GatewaySubnet` and every other hub subnet, overriding your `/8` summary UDR and sending inbound on-premises-to-spoke traffic **directly** to the spoke while outbound spoke-to-on-premises return traffic went through the hub NVA.

Azure's public preview feature **[Disable peering route propagation](https://learn.microsoft.com/en-us/azure/virtual-network/configure-disable-peering-route-propagation?tabs=cli)** (`--disable-peering-route All`, gated by `Microsoft.Network/AllowDisablePeeringRoutes`) solves this exact problem. In this post, we build a 10-spoke hub-and-spoke lab in Azure (`swedencentral`) with **three distinct hybrid connections** (Site-to-Site VPN, SD-WAN with StrongSwan + BIRD, and ExpressRoute with a Megaport Cloud Router) to inspect the control plane and packet-by-packet data plane in detail.

---

## 1. The Lab Topology (3 Hybrid Connections: S2S VPN, SD-WAN, and ExpressRoute)

We deployed the following environment in `swedencentral` (plus Frankfurt FR5 for the Megaport Cloud Router):

- **Hybrid Connection 1: Simulated On-Premises S2S VPN (`vnet-onprem`, `172.16.0.0/16`):**
  - `vm-onprem` (`172.16.1.4`): Ubuntu 22.04 VM running **StrongSwan** (route-based IKEv2 over `vti0`) and **FRR BGP** (`ASN 65010`), peered over a Site-to-Site IPsec VPN connection (`conn-hub-onprem`) with the hub VPN Gateway (`vpngw-hub`).
- **Hybrid Connection 2: Simulated On-Premises SD-WAN (`vnet-onprem-sdwan`, `172.17.0.0/16`):**
  - `vm-onprem-sdwan` (`172.17.1.4`): Ubuntu 22.04 VM running **StrongSwan** (`swanctl` with XFRM interface `xfrm0`, `if_id 42`, `169.254.20.2/30`) and **BIRD 2.0.8 eBGP** (`ASN 65020`), connected to the hub SD-WAN NVA (`vm-hub-probe`, `10.0.2.4`, `ASN 65002`, `169.254.20.1/30`).
- **Hybrid Connection 3: ExpressRoute + Megaport Cloud Router (`172.18.0.0/16`):**
  - `er-circuit-hub` (50 Mbps Standard MeteredData ExpressRoute circuit in Frankfurt) linked via `conn-hub-er` to `ergw-hub` (`Standard` ExpressRoute Gateway in `GatewaySubnet`) and terminated on a **Megaport Cloud Router** (`jomore-copilot-mcr-disable-peering`, `ASN 65030`) over primary and secondary VXCs (`169.254.80.216/30` and `169.254.80.220/30`), advertising `172.18.0.0/16` into Azure.
- **Hub VNet (`vnet-hub`, `10.0.0.0/16`):**
  - `GatewaySubnet` (`10.0.0.0/24`): Hosts both `vpngw-hub` (`VpnGw1AZ`, `ASN 65515`, BGP peer IP `10.0.0.254`) and `ergw-hub` (`Standard`), associated with route table **`rt-gw`** (`10.0.0.0/8 -> 10.0.1.4`).
  - `snet-hub-probe` (`10.0.2.0/24`): Hosts **`vm-hub-probe`** (`10.0.2.4`), which acts both as the **Hub SD-WAN appliance** (StrongSwan + BIRD `ASN 65002`) and as our **effective-route observer** because it is associated with the **exact same `rt-gw` route table** as `GatewaySubnet`.
  - `snet-nva` (`10.0.1.0/24`): Hosts **`vm-hub-nva`** (`10.0.1.4`), the central hub firewall NVA with IP forwarding enabled and `iptables` rules that can toggle between **stateless** (`FORWARD ACCEPT` with directional packet counters) and **stateful** (`conntrack` dropping `ctstate INVALID` asymmetric replies). Its route table **`rt-nva`** has `172.17.0.0/16 -> 10.0.2.4` (for SD-WAN return traffic) and learns `172.16.0.0/16` and `172.18.0.0/16` automatically from `vpngw-hub` and `ergw-hub`.
- **10 Spoke VNets (`vnet-spoke1` .. `vnet-spoke10`, `10.1.0.0/16` .. `10.10.0.0/16`):**
  - All 10 spokes are peered with `vnet-hub` (`AllowGatewayTransit = true` on hub, `UseRemoteGateways = true` on all 10 spokes).
  - `vnet-spoke1/snet-workload` (`10.1.1.0/24`) hosts **`vm-spoke1`** (`10.1.1.4`, running an HTTP server on TCP port 80) and is associated with route table **`rt-spoke1`** (`disableBgpRoutePropagation = true`, with UDRs `10.0.0.0/8`, `172.16.0.0/16`, `172.17.0.0/16`, and `172.18.0.0/16` all pointing to `10.0.1.4`).

```
+------------------------------------+  +------------------------------------+  +------------------------------------+
| Hybrid 1: S2S VPN On-Prem          |  | Hybrid 2: SD-WAN On-Prem           |  | Hybrid 3: ExpressRoute On-Prem     |
| vnet-onprem (172.16.0.0/16)        |  | vnet-onprem-sdwan (172.17.0.0/16)  |  | Megaport MCR (Frankfurt FR5)       |
| vm-onprem (172.16.1.4)             |  | vm-onprem-sdwan (172.17.1.4)       |  | jomore-copilot-mcr-disable-peering |
| StrongSwan IKEv2 + FRR ASN 65010   |  | StrongSwan XFRM + BIRD ASN 65020   |  | ASN 65030 | Advertises 172.18.0.0/16|
+-----------------+------------------+  +-----------------+------------------+  +-----------------+------------------+
                  | S2S IPsec (vti0)                      | IPsec (xfrm0)                         | Primary + Secondary VXCs
                  | + eBGP                                | + eBGP (169.254.20.0/30)              | er-circuit-hub (50 Mbps)
                  v                                       v                                       v
+--------------------------------------------------------------------------------------------------------------------+
| Hub VNet: vnet-hub (10.0.0.0/16)                                                                                   |
|                                                                                                                    |
|   GatewaySubnet (10.0.0.0/24)  <--- Route Table: rt-gw (UDR: 10.0.0.0/8 -> 10.0.1.4)                               |
|     [vpngw-hub: VpnGw1AZ | ASN 65515 | BGP IP 10.0.0.254]                                                          |
|     [ergw-hub:  Standard ExpressRoute Gateway | Connected to er-circuit-hub]                                       |
|                                                                                                                    |
|   snet-hub-probe (10.0.2.0/24) <--- Route Table: rt-gw (UDR: 10.0.0.0/8 -> 10.0.1.4)                               |
|     [vm-hub-probe: 10.0.2.4 | Hub SD-WAN NVA: StrongSwan XFRM + BIRD ASN 65002 + Route Observer]                   |
|                                                                                                                    |
|   snet-nva (10.0.1.0/24)       <--- Route Table: rt-nva (172.17.0.0/16 -> 10.0.2.4)                                |
|     [vm-hub-nva: 10.0.1.4 | Central Hub Firewall NVA: IP Forwarding + iptables conntrack/LOG]                      |
+-----+-------+-------+-------+-------+-------+-------+-------+-------+-------+--------------------------------------+
      |       |       |       |       |       |       |       |       |       |
      | VNet Peerings (AllowGatewayTransit = true / UseRemoteGateways = true) |
      v       v       v       v       v       v       v       v       v       v
  +-------+ +---+   +---+   +---+   +---+   +---+   +---+   +---+   +---+  +----+
  |Spoke 1| |S2 |   |S3 |   |S4 |   |S5 |   |S6 |   |S7 |   |S8 |   |S9 |  |S10 |
  |10.1/16| |10.2   |10.3   |10.4   |10.5   |10.6   |10.7   |10.8   |10.9  |10.10
  +---+---+ +---+   +---+   +---+   +---+   +---+   +---+   +---+   +---+  +----+
      |
      +-- snet-workload (10.1.1.0/24) <--- Route Table: rt-spoke1 (BGP prop disabled)
            UDRs: 10.0.0.0/8, 172.16.0.0/16, 172.17.0.0/16, 172.18.0.0/16 -> 10.0.1.4
            [vm-spoke1: 10.1.1.4 | Python HTTP server :80]
```

> **Pro tip: How to inspect `GatewaySubnet`'s effective routes:** Azure does not expose `az network nic show-effective-route-table` for the managed NICs inside a VPN or ExpressRoute Gateway. By associating our Hub SD-WAN subnet (`snet-hub-probe` with `nic-vm-hub-probe`) in the same hub VNet to the **same `rt-gw` route table**, we can run `az network nic show-effective-route-table` on `nic-vm-hub-probe` to see the exact `Default`, `VNetPeering`, `VirtualNetworkGateway`, and `User` routes evaluated on `rt-gw`.

### Verifying BGP Across All 3 Hybrid Connections

1. **S2S VPN (`vm-onprem` <-> `vpngw-hub`):**
   `vpngw-hub` advertises the hub (`10.0.0.0/16`) and all 10 peered spokes (`10.1.0.0/16` .. `10.10.0.0/16`) over eBGP to `vm-onprem`, and learns `172.16.0.0/16`:
   ```text
   Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
   10.0.0.254      4      65515         3         5        0    0    0 00:00:07           11       12 N/A
   ```

2. **SD-WAN (`vm-onprem-sdwan` <-> `vm-hub-probe`):**
   Over the XFRM tunnel interface `xfrm0` (`169.254.20.0/30`), BIRD on `vm-hub-probe` (`AS65002`) exports all 11 Azure `/16` prefixes (`10.0.0.0/16` .. `10.10.0.0/16`) to `vm-onprem-sdwan` (`AS65020`), and imports `172.17.0.0/16`:
   ```text
   # On vm-onprem-sdwan (birdc show protocols all sdwan_ebgp && ip route)
   Name       Proto      Table      State  Since         Info
   sdwan_ebgp BGP        ---        up     07:35:14.468  Established   
     BGP state:          Established
       Neighbor address: 169.254.20.1
       Neighbor AS:      65002
       Local AS:         65020
       Routes:           11 imported, 1 exported, 11 preferred

   10.0.0.0/16 via 169.254.20.1 dev xfrm0 proto bird metric 32 
   10.1.0.0/16 via 169.254.20.1 dev xfrm0 proto bird metric 32 
   ...
   10.10.0.0/16 via 169.254.20.1 dev xfrm0 proto bird metric 32 
   ```

3. **ExpressRoute + Megaport MCR (`jomore-copilot-mcr-disable-peering` <-> `er-circuit-hub` / `ergw-hub`):**
   On the ExpressRoute circuit's MSEE route table and on `ergw-hub` (`az network vnet-gateway list-learned-routes -g rg-disable-peering-routes-lab -n ergw-hub -o table`), we see all 11 Azure VNet `/16` prefixes, the S2S VPN prefix (`172.16.0.0/16` via iBGP), and the ExpressRoute prefix (`172.18.0.0/16` via eBGP from Megaport MCR `AS65030`):
   ```text
   Network            NextHop    Origin    SourcePeer    AsPath       Weight
   -----------------  ---------  --------  ------------  -----------  --------
   10.0.0.0/16                   Network   10.0.0.12                  32768
   10.1.0.0/16                   Network   10.0.0.12                  32768
   ...
   10.10.0.0/16                  Network   10.0.0.12                  32768
   172.16.0.0/16      10.0.0.5   IBgp      10.0.0.5                   32768
   172.18.0.0/16      10.0.0.6   EBgp      10.0.0.6      12076-65030  32779
   172.18.0.0/16      10.0.0.7   EBgp      10.0.0.7      12076-65030  32779
   ```

---

## 2. Scenario 1: The Asymmetric Routing Trap (`disablePeeringRoute = None` + Summarized `10.0.0.0/8` UDR)

With `rt-gw` (attached to both `GatewaySubnet` and `snet-hub-probe`) holding only a single summarized UDR for all spokes:

```bash
az network route-table route create \
  -g rg-disable-peering-routes-lab \
  --route-table-name rt-gw \
  -n to-spokes-summary \
  --address-prefix 10.0.0.0/8 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.1.4
```

When we inspect the effective routes on `rt-gw` (`az network nic show-effective-route-table -g rg-disable-peering-routes-lab -n nic-vm-hub-probe -o table`), we see why the `/8` summary route fails to attract traffic destined for `10.1.1.4`:

```text
Source                 State    Address Prefix    Next Hop Type          Next Hop IP
---------------------  -------  ----------------  ---------------------  -----------------------
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
VirtualNetworkGateway  Active   172.18.0.0/16     VirtualNetworkGateway  10.2.146.34 10.2.146.35
VirtualNetworkGateway  Active   172.18.1.0/30     VirtualNetworkGateway  10.2.146.35
Default                Active   0.0.0.0/0         Internet
...
User                   Active   10.0.0.0/8        VirtualAppliance       10.0.1.4
```

Even though our `User` route (`10.0.0.0/8 -> 10.0.1.4`) is `Active`, all 10 `Default` `VNetPeering` routes (`10.1.0.0/16` .. `10.10.0.0/16`) are **also `Active`** and have a longer prefix length (`/16` vs `/8`).

### What happens on the wire across S2S VPN, SD-WAN, and ExpressRoute?

1. **Forward path (`172.16.1.4`, `172.17.1.4`, or `172.18.x.x -> vm-spoke1 10.1.1.4`):**
   - Packet arrives at `vpngw-hub`, `ergw-hub` (in `GatewaySubnet`), or `vm-hub-probe` (in `snet-hub-probe`).
   - Azure SDN looks up `10.1.1.4` in `rt-gw`, matches `Default 10.1.0.0/16 -> VNetPeering` (beating `10.0.0.0/8`), and sends the packet **directly to `vm-spoke1`**, completely bypassing `vm-hub-nva` (`10.0.1.4`).
2. **Return path (`vm-spoke1 10.1.1.4 -> 172.16.1.4 / 172.17.1.4 / 172.18.x.x`):**
   - `vm-spoke1` looks up the destination in `rt-spoke1`, matches the `User` UDRs (`172.16.0.0/16`, `172.17.0.0/16`, `172.18.0.0/16 -> VirtualAppliance 10.0.1.4`), and sends the reply (`ICMP Echo Reply` or `TCP SYN-ACK`) to `vm-hub-nva` (`10.0.1.4`).

We can prove this across both S2S VPN (`172.16.0.0/16`) and SD-WAN (`172.17.0.0/16`) simultaneously with directional `iptables` counters on `vm-hub-nva`:

- **When `vm-hub-nva` is stateless (`iptables -P FORWARD ACCEPT`):**
  Ping (`3/3`) and `curl http://10.1.1.4` (`200 OK`) succeed from both `vm-onprem` (`172.16.1.4`) and `vm-onprem-sdwan` (`172.17.1.4`), masking the bug! However, `iptables -L FORWARD -v -n` on `vm-hub-nva` reveals the exact same asymmetry for both hybrid connections:
  ```text
  Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)
   pkts bytes target     prot opt in     out     source               destination         
      0     0 ACCEPT     all  --  *      *       172.17.0.0/16        10.1.0.0/16         
      8   747 ACCEPT     all  --  *      *       10.1.0.0/16          172.17.0.0/16       
      0     0 ACCEPT     all  --  *      *       172.16.0.0/16        10.1.0.0/16         
      8   747 ACCEPT     all  --  *      *       10.1.0.0/16          172.16.0.0/16       
  ```
  Zero packets (`0 bytes`) went from either on-premises network (`172.16.0.0/16` or `172.17.0.0/16`) to `10.1.0.0/16` through `vm-hub-nva`, while all `8` reply packets (`747 bytes` per test) returned through `vm-hub-nva`!

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
  Because the central firewall NVA never saw the initial TCP `SYN` or ICMP Echo Request, Linux `conntrack` classifies `vm-spoke1`'s `SYN-ACK` and Echo Reply as `ctstate INVALID` and drops every packet.

---

## 3. Scenario 2: Suppressing Peering Routes on `rt-gw` (`--disable-peering-route All` vs. Explicit `/16` UDRs)

### How `disablePeeringRoute = All` works

The new route table property `disablePeeringRoute` (CLI flag `--disable-peering-route All`) instructs Azure not to propagate `VNetPeering` routes (nor `VirtualNetworkGateway` routes learned via peering) into subnets associated with that route table:

```bash
# 1. Register the preview feature flag
az feature register --namespace Microsoft.Network --name AllowDisablePeeringRoutes
az provider register --namespace Microsoft.Network

# 2. Disable peering route propagation on the GatewaySubnet / SD-WAN route table
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

> **Note:** Even when `disablePeeringRoute = All` is active on `GatewaySubnet`'s route table (`rt-gw`), **the VPN and ExpressRoute Gateways still advertise all peered spoke prefixes (`10.1.0.0/16` .. `10.10.0.0/16`) to on-premises via BGP**. Why? Because an Azure Virtual Network Gateway advertises the address space of the hub VNet and all peered spoke VNets from the VNet control-plane topology, not by redistributing `GatewaySubnet`'s effective route table. Disabling peering route propagation on `rt-gw` only changes how the gateway (and any hub SD-WAN NVA sharing `rt-gw`) forwards **inbound packets after decapsulation** inside Azure.

### Verifying the Symmetric Data Plane (Explicit `/16` UDRs vs. `disablePeeringRoute = All`)

Until `AllowDisablePeeringRoutes` is approved on a subscription, the only way to prevent `rt-gw`'s 10 `VNetPeering` routes from overriding the NVA path is to configure 10 explicit `/16` UDRs (`10.1.0.0/16` .. `10.10.0.0/16 -> 10.0.1.4`) on `rt-gw`.

Let's compare both approaches on `rt-gw`:

| Characteristic | Without `disablePeeringRoute` (Explicit `/16` UDRs) | With `--disable-peering-route All` |
|----------------|-----------------------------------------------------|------------------------------------|
| **UDRs required on `rt-gw`** | $N$ routes (one matching `/16` UDR per spoke VNet) | **1 route** (`10.0.0.0/8 -> 10.0.1.4`) |
| **Day-2 operation when adding Spoke 11** | Must update `rt-gw` with a new `/16` UDR | **Zero route table changes** (`10.0.0.0/8` automatically covers it) |
| **400-UDR limit risk** | High when spoke VNets have multiple address prefixes | Eliminated |
| **State of `VNetPeering` routes on `rt-gw`** | `Invalid` (shadowed by matching `/16` UDRs) | Removed from effective route table |

When we tested the 10 explicit `/16` UDRs on `rt-gw`, `az network nic show-effective-route-table -g rg-disable-peering-routes-lab -n nic-vm-hub-probe -o table` showed all 10 `VNetPeering` routes invalidated and stateful traffic from on-premises to `vm-spoke1` succeeded with **100% symmetric traversal** (`8` forward packets, `8` return packets, and `0` `ctstate INVALID` drops). Afterward, we removed the 10 `/16` UDRs so the live lab retains only the `10.0.0.0/8` summary route and showcases the 10 `Active` `VNetPeering` routes across all 3 hybrid connections.

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
User      Active   172.17.0.0/16     VirtualAppliance  10.0.1.4
User      Active   172.18.0.0/16     VirtualAppliance  10.0.1.4
```

When `vm-spoke1` (`10.1.1.4`) sends a packet matching `172.16.0.0/16`, `172.17.0.0/16`, or `172.18.0.0/16 -> VirtualAppliance 10.0.1.4`, Azure's SDN fabric must resolve how to reach the next-hop IP `10.0.1.4`. Because `10.0.1.4` is not in `vnet-spoke1` (`10.1.0.0/16`), Azure resolves `10.0.1.4` recursively using the system route `Default 10.0.0.0/16 -> VNetPeering`.

- **On `GatewaySubnet` and `snet-hub-probe` (`rt-gw`):** The central firewall NVA (`10.0.1.4`) is in the **same hub VNet** (`10.0.0.0/16`), so `rt-gw` resolves `10.0.1.4` via `Default 10.0.0.0/16 -> VnetLocal` (which is **not** removed by `--disable-peering-route All`). And when `vm-hub-nva` forwards the packet to `vm-spoke1` (`10.1.1.4`), `snet-nva` uses `rt-nva` where `10.1.0.0/16 -> VNetPeering` is still active!
- **On `vnet-spoke1/snet-workload` (`rt-spoke1`):** The NVA (`10.0.1.4`) is in a **peered VNet** (`vnet-hub`). Disabling peering routes on `rt-spoke1` removes `10.0.0.0/16 -> VNetPeering`, leaving `vnet-spoke1` with no underlay path to reach the NVA next hop `10.0.1.4`.

---

## 5. Key Takeaways

1. **Where to use `--disable-peering-route All`:** Enable it on **`GatewaySubnet`** and **hub SD-WAN subnets** (`rt-gw`, whose UDR next hop is a local hub NVA) so that a single summarized UDR (`10.0.0.0/8 -> <Hub-NVA-IP>`) can steer all inbound traffic from S2S VPN, SD-WAN, and ExpressRoute to all peered spokes without being overridden by `/16` or `/24` `VNetPeering` routes.
2. **Where NOT to use `--disable-peering-route All`:** Do **not** enable it on **`snet-nva`** (the central firewall NVA itself still needs the `VNetPeering` routes to forward inspected traffic to the spokes!) and do **not** enable it on **spoke subnets** whose UDR next hop is an NVA in the peered hub VNet.
3. **BGP advertisement is unaffected:** Disabling peering route propagation on `GatewaySubnet` does not stop the Azure VPN or ExpressRoute Gateways from advertising peered spoke prefixes to on-premises via BGP.
4. **Check feature approval before rollout:** `Microsoft.Network/AllowDisablePeeringRoutes` currently has `approvalType: ApprovalRequired` (`az feature registration show --provider-namespace Microsoft.Network --name AllowDisablePeeringRoutes`). Verify that its state has transitioned from `Pending` to `Registered` before applying `--disable-peering-route All` in production pipelines.
