# Complete retained NAT capture

This directory contains the **complete 78-file** `nat-evidence-20261016T085133Z` capture, not just the excerpts selected for the post. Collection ran on 16 October 2026 from 08:51:33 through 08:59:24 UTC in Sweden Central. The final verdict is PASS for the claims in [verification.json](nat-evidence-20261016T085133Z/verification.json).

Start with the [original evidence summary](nat-evidence-20261016T085133Z/summary.txt), then the [file index](nat-evidence-20261016T085133Z/file-index.json). The index excludes itself and the hash manifest. The [SHA-256 manifest](nat-evidence-20261016T085133Z/sha256-manifest.json) hashes all 77 other files, including the index, and excludes itself.

## What to open

All links below stay inside this post.

| Question | Capture |
|---|---|
| Same IP, genuinely different Azure VMs? | [Verification identity details](nat-evidence-20261016T085133Z/verification.json), [Azure VMs](nat-evidence-20261016T085133Z/before-vms.json), [NICs](nat-evidence-20261016T085133Z/nics.json), [backend1 guest/IMDS](nat-evidence-20261016T085133Z/before-vm-spoke1-isolated192.json), [backend2 guest/IMDS](nat-evidence-20261016T085133Z/before-vm-spoke2-isolated192.json) |
| Which responses came back? | [Hub HTTP requests, endpoints, exact bodies and timeout](nat-evidence-20261016T085133Z/hub-vm-hub-hub10.json) |
| Full Azure peering configuration? | [Hub](nat-evidence-20261016T085133Z/after-vnet-hub.json), [spoke1](nat-evidence-20261016T085133Z/after-vnet-spoke1.json), [spoke2](nat-evidence-20261016T085133Z/after-vnet-spoke2.json) |
| Full hub effective routes? | [Hub after](nat-evidence-20261016T085133Z/routes-after-vm-hub-hub10.json) |
| Full NVA effective routes? | [NVA1](nat-evidence-20261016T085133Z/routes-after-vm-spoke1-spoke10.json), [NVA2](nat-evidence-20261016T085133Z/routes-after-vm-spoke2-spoke10.json) |
| Excluded backend NIC routes? | [Backend1](nat-evidence-20261016T085133Z/routes-after-vm-spoke1-isolated192.json), [backend2](nat-evidence-20261016T085133Z/routes-after-vm-spoke2-isolated192.json) |
| NAT rules, forwarding, unit, script, counters? | [NVA1 before](nat-evidence-20261016T085133Z/before-vm-spoke1-spoke10.json), [NVA1 after](nat-evidence-20261016T085133Z/after-vm-spoke1-spoke10.json), [NVA2 before](nat-evidence-20261016T085133Z/before-vm-spoke2-spoke10.json), [NVA2 after](nat-evidence-20261016T085133Z/after-vm-spoke2-spoke10.json) |
| Backend logs showing translated sources? | [Backend1 after](nat-evidence-20261016T085133Z/after-vm-spoke1-isolated192.json), [backend2 after](nat-evidence-20261016T085133Z/after-vm-spoke2-isolated192.json) |
| Resource inventory and retained state? | [Inventory](nat-evidence-20261016T085133Z/inventory-final.json), [final VM states](nat-evidence-20261016T085133Z/after-vms.json), [completed collector lease](nat-evidence-20261016T085133Z/lease-final.json) |

The index also includes before-route tables, all five effective-NSG responses, per-command text transcripts, readiness checks, and process-idle evidence. The `before`/`after` labels bracket this read-only HTTP evidence collection, not a topology change or comparison against the conceptual transit-VNet design.

## Integrity and sanitization

All 78 source files were copied. Existing subscription placeholders were preserved. A public-release scan checked the full folder for subscription/tenant GUIDs, credentials, tokens, SSH key material, email addresses, local user paths, and internal hostnames. Non-secret Azure resource/VM identity GUIDs are retained so VM-to-NIC-to-IMDS bindings remain independently inspectable. No source deployment script, SSH key, or custom-data payload was imported.

Three Azure-internal DNS suffixes in `nics.json` and its text transcript were replaced with stable `<INTERNAL_DNS_SUFFIX_N>` placeholders. One editorial transformation replaces the em dash in `summary.txt` with a colon. Affected byte lengths in `file-index.json` and SHA-256 entries were regenerated. All other capture payload bytes are unchanged. The manifest describes this public copy, not an untouched upstream archive.

## Limits that matter

- TCP 8080 HTTP from hub `10.0.1.4` to the two aliases is proven. Other clients, ports, protocols, performance, isolation, and transparent transit are not.
- The connection-tracking utility/table interfaces were unavailable. `tcpdump` was present but optional packet capture was omitted. The archive is not a packet trace.
- ARM RunCommand envelopes were reduced to status plus decoded guest data. Guest commands retain their command text, timestamps, exit codes, stdout, and stderr; `.txt` companions preserve collection command records.
- Snapshots are sequential, not atomic. Before/after equality checks support the unchanged-configuration claims.
- Effective-NSG calls returned empty objects and NIC/subnet associations were absent. That is API evidence, not a security approval. These lab firewall defaults are not production hardening.
- Hub cloud-init retains a completed/degraded schema-validation warning. Service readiness checks passed.
- A local collector interruption and continuation are retained in [collector-transport-interruption.json](nat-evidence-20261016T085133Z/collector-transport-interruption.json). It is provenance, not a failed final application result.
- All five VMs remained running. Nothing was cleaned up or probed again for publication.
