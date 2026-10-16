# References and artifact map

Official sources retrieved on **16 October 2026**:

- [Configure subnet peering](https://learn.microsoft.com/en-us/azure/virtual-network/how-to-configure-subnet-peering): subscription allowlisting, all-region availability, supported configuration surfaces, unique participating subnets and parent spaces, nonpeered-subnet route visibility, delegated-subnet over-advertisement, and supported hardware generations.
- [Virtual Network Peerings: Create Or Update, API 2026-01-01](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/virtual-network-peerings/create-or-update?view=rest-virtualnetwork-2026-01-01): REST properties, including `peerCompleteVnets`, subnet-name selectors, and forwarding settings.
- [Azure Virtual Network pricing](https://azure.microsoft.com/en-us/pricing/details/virtual-network/): peering is billed on ingress/egress data transfer at both ends, not a fixed charge per peering link. Regional pricing and traffic direction matter. The public page's dynamic numeric prices were not available in the fetched text, so this post uses the billing model, not a quoted per-GB rate.
- [Dalsv6 sizes](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dalsv6-series): AMD fourth-generation EPYC 9004 (Genoa) host processors for the lab's `Standard_D2als_v6` selection.

## Self-contained experimental evidence

- [Archive guide](evidence/README.md): navigation, provenance, sanitization, integrity, and known gaps.
- [All-file index](evidence/nat-evidence-20261016T085133Z/file-index.json) and [SHA-256 manifest](evidence/nat-evidence-20261016T085133Z/sha256-manifest.json).
- [Independent claim verification](evidence/nat-evidence-20261016T085133Z/verification.json), including exact repeated-IP identity bindings, HTTP bodies, counter deltas, route equality, and configuration equality.
- [Hub HTTP and guest evidence](evidence/nat-evidence-20261016T085133Z/hub-vm-hub-hub10.json).
- [Azure NIC configurations](evidence/nat-evidence-20261016T085133Z/nics.json) and [Azure VM identities and NIC references](evidence/nat-evidence-20261016T085133Z/before-vms.json).
- [Hub peering definitions](evidence/nat-evidence-20261016T085133Z/after-vnet-hub.json), [spoke1](evidence/nat-evidence-20261016T085133Z/after-vnet-spoke1.json), and [spoke2](evidence/nat-evidence-20261016T085133Z/after-vnet-spoke2.json).
- [NVA1 rules, unit, script, sysctls and counters](evidence/nat-evidence-20261016T085133Z/before-vm-spoke1-spoke10.json) and [after capture](evidence/nat-evidence-20261016T085133Z/after-vm-spoke1-spoke10.json).
- [NVA2 rules, unit, script, sysctls and counters](evidence/nat-evidence-20261016T085133Z/before-vm-spoke2-spoke10.json) and [after capture](evidence/nat-evidence-20261016T085133Z/after-vm-spoke2-spoke10.json).
- [Backend1 identity and service](evidence/nat-evidence-20261016T085133Z/before-vm-spoke1-isolated192.json) and [backend2](evidence/nat-evidence-20261016T085133Z/before-vm-spoke2-isolated192.json).

The local source experiment belongs to `erjosito/net-lab-builder`, whose repository visibility was checked as public. Its new lab files were not committed remotely when this draft was prepared, so this post intentionally does not link to nonexistent source paths. Everything needed to inspect the reported result is included here. No Azure resource reads or writes were made while preparing this post.

The older transit-VNet pattern is a conceptual comparison only. Neither its performance nor its costs were measured. The retained lab estimate of approximately $10.71/day is for five VMs and disks, not an invoice or a production NVA architecture.
