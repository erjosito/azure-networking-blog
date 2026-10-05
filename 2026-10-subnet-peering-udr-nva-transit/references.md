# References and evidence provenance

## Official documentation

Checked on 2026-10-04:

- [Configure subnet peering](https://learn.microsoft.com/en-us/azure/virtual-network/how-to-configure-subnet-peering): selecting local and remote subnets instead of peering complete address spaces. Consult its current prerequisites and availability restrictions before reproducing.
- [Azure virtual network traffic routing](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-networks-udr-overview): effective routing, longest-prefix selection, `VirtualAppliance` next hops, Azure NIC and guest forwarding requirements, and propagation controls.
- [Virtual network peering: service chaining](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview#service-chaining): using a virtual appliance in a peered VNet as a UDR next hop.

Documentation explains the mechanism. The measurements below support the specific result; documentation is not a substitute for a successful probe.

## Source and scope

Source lab: [sap-rise-scoped-peering-fwaas in net-lab-builder](https://github.com/erjosito/net-lab-builder/tree/main/labs/sap-rise-scoped-peering-fwaas). Repository visibility was verified as public before linking. The post's evidence copies are self-contained; readers do not need source-repository working files to inspect the comparison.

The only measurement set used is `show-output/udr-ab-20261004T165000Z`, relative to that lab. Its directory label is a collection identifier, not the observation time. The canonical guest outputs carry these UTC timestamps:

| State | Canonical source file, relative to the evidence root | Guest sample starts |
|---|---|---|
| A | `A/A-vm-hub-test-comparison-in-2-0.json` | 2026-10-04 17:47:19 |
| B | `B/B-vm-hub-test-comparison-in-1-0.json` | 2026-10-04 17:49:27 |
| A2 | `A2/A2-vm-hub-test-comparison-in-1-0.json` | 2026-10-04 17:51:48 |

For each state, the four route inputs are named `<state>-vm-<role>-effective-routes-in-1-0.json`, where `<role>` is `hub-test`, `hub-nva`, `spoke-nva`, or `workload-probe`.

A sample 1 is excluded because it used an unsupported `mtr --icmp` flag. A sample 2, B sample 1, and A2 sample 1 all use the same default-ICMP `mtr` command. No earlier `s3` captures, peered-source controls, or guest-route-only trials are mixed into this comparison.

## Included assets

| Asset | Contents |
|---|---|
| [A.json](assets/evidence/A.json) | All four A NIC effective-route tables and the canonical source probe |
| [B.json](assets/evidence/B.json) | All four B NIC effective-route tables and the canonical source probe |
| [A2.json](assets/evidence/A2.json) | All four A2 NIC effective-route tables and the canonical source probe |
| [prerequisites.json](assets/evidence/prerequisites.json) | Selected setup ledger entries and hub/spoke pre-test guest snapshots |
| [verification.json](assets/evidence/verification.json) | Independent scoped ICMP verdict and subsequent full restoration verification |
| [provenance.json](assets/evidence/provenance.json) | Original relative filenames, SHA-256 fingerprints, and transformation rules |

The original measurement files wrap Azure output as a JSON string in `stdout`. The phase assets decode that wrapper, retaining each complete effective-route `value` array and each complete Run Command `value.message`, including commands, timestamps, ping results, `mtr` reports, and the explicit standalone-traceroute availability message. Wrapper exit codes and stderr are also retained.

No numerical observations or route fields are rewritten. System route prefixes, including public-address ranges, are retained because they are routing data, not public host identifiers. Private lab IPs and generic lab VM names are preserved. Setup entries omit VM creation payloads, identity material, and unrelated operations; resource-group identifiers are replaced with `<resource-group>`. Local absolute evidence-root/journal paths in the verdict and restoration records are replaced with portable relative labels. Raw originals are untouched.

Each inline route table is a selected presentation of actual rows. Full phase assets preserve other prefixes and inactive routes, including the workload's invalid system Internet default and its active user default via the spoke NVA.

Route comparison recursively normalizes object-key and array ordering, retaining all fields and comparing route multisets per NIC. Only the source `/32` differs. The propagation flag remains `true` for the source, spoke NVA, and workload, and `false` for the hub NVA. The fixed hub `/32` takes precedence over its captured propagated `/16`; the source does not import that propagated route.

## Interpreting the verdict and restoration records

The verdict's PASS is expressly limited to the same-source ICMP A/B/A2 comparison. It is not a TCP/application verdict or proof of all reverse hops. Its restoration note records that A2 had removed the source route while common test setup still awaited restoration.

The separate restoration record, verified at `2026-10-04T18:12:32.743967+00:00`, supersedes that earlier pending-restore state. It reports PASS, no remaining operations, no pending cloud operations, and no restoration CLI processes. It verifies removal of temporary resources/settings and preservation of the original four VMs, NICs, and OS disks, with those VMs deallocated.

These are archived checks. Writing and reviewing this post required no further cloud operations.
