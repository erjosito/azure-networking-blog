# Topology Overview: dual-hub-vnra-udr-transit

## Mermaid Diagram

```mermaid
graph TB
    subgraph Sweden["Sweden Central (swedencentral)"]
        subgraph H1["hub1-vnet (10.1.0.0/16)"]
            VNRA1["🖥️ VNRA1 (Managed)<br/>10.1.0.4<br/>VirtualNetworkApplianceSubnet<br/>(10.1.0.0/24)"]
        end
        subgraph S1["spoke1-vnet (10.10.0.0/16)"]
            TEST1["🖱️ test1-vm<br/>10.10.1.4<br/>vm-subnet (10.10.1.0/24)"]
        end
        H1 -->|Regional Peering<br/>allowForwardedTraffic=true| S1
    end

    subgraph NorthEU["North Europe (northeurope)"]
        subgraph H2["hub2-vnet (10.2.0.0/16)"]
            VNRA2["🖥️ VNRA2 (Managed)<br/>10.2.0.4<br/>VirtualNetworkApplianceSubnet<br/>(10.2.0.0/24)"]
        end
        subgraph S2["spoke2-vnet (10.20.0.0/16)"]
            TEST2["🖱️ test2-vm<br/>10.20.1.4<br/>vm-subnet (10.20.1.0/24)"]
        end
        H2 -->|Regional Peering<br/>allowForwardedTraffic=true| S2
    end

    H1 -->|Global Peering<br/>allowForwardedTraffic=true| H2

    style VNRA1 fill:#c8e6c9
    style VNRA2 fill:#c8e6c9
    style TEST1 fill:#bbdefb
    style TEST2 fill:#bbdefb
    style H1 fill:#f5f5f5
    style H2 fill:#f5f5f5
    style S1 fill:#f5f5f5
    style S2 fill:#f5f5f5
```

## Legend

- **🖥️ VNRA (Green)**: Managed Azure Virtual Network Routing Appliance (Microsoft.Network/virtualNetworkAppliances)
  - No user NIC, no OS disk, no cloud-init configuration
  - Bandwidth tier: 50 Gbps per VNRA
  - Hardware-based forwarding (invisible to TTL/traceroute probes)
  - Private IPs assigned by ARM control plane

- **🖱️ VM (Blue)**: Standard Azure VM with manageable NIC
  - test1-vm: Standard_B2ts_v2, 10.10.1.4, swedencentral
  - test2-vm: Standard_B2ts_v2, 10.20.1.4, northeurope

- **VNet Peerings**: All transit paths require `allowForwardedTraffic=true` on both directions
  - Regional peerings: hub-to-spoke within same region
  - Global peering: hub-to-hub cross-region (swedencentral ↔ northeurope)

