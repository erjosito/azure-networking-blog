# References and evidence provenance

## Official documentation

Checked on 2026-10-05:

- [Configure subnet peering](https://learn.microsoft.com/en-us/azure/virtual-network/how-to-configure-subnet-peering): selecting local and remote subnets instead of peering complete address spaces. Under **Subnet peering checks and limitations**, item 2 requires delete/recreate to change peering type. Item 4 describes visible remote peered-subnet routes on non-peered subnets even though packets are dropped before reaching the VM. The page requires subscription allowlisting, lists configuration methods, and specifies VM-generation restrictions; consult it before reproducing.
- [Azure virtual network traffic routing](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-networks-udr-overview): longest-prefix selection, configured versus effective routing, and permitted UDR next-hop types. Its **User-defined routes** section explicitly says that Virtual network peering cannot be specified as a UDR next-hop type.
- [Virtual network peering: service chaining](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview#service-chaining): using a virtual appliance in a peered VNet as a UDR next hop.

Documentation explains the mechanism. The measurements below support the specific result; documentation is not a substitute for a successful probe.

## Source and two distinct experiments

Source lab: [sap-rise-scoped-peering-fwaas in net-lab-builder](https://github.com/erjosito/net-lab-builder/tree/main/labs/sap-rise-scoped-peering-fwaas). Repository visibility was verified as public before linking. The post's evidence copies are self-contained; readers do not need source-repository working files to inspect the comparison.

The primary experiment is the **2026-10-05 direct-path comparison**, bundled below. The **2026-10-04 A/B/A2 transit illustration** is preserved independently, with its original assets unchanged. Their shared private addresses must not be mistaken for a single continuous test state: NVAs are off in the direct comparison and running in the successful historical transit test.

## Primary evidence: direct-path enforcement, 2026-10-05

Source collection identifier: `show-output/enforcement-direct-20261005T081250Z`, relative to the lab. New raw files are not linked from the source repository because publication does not depend on them being tracked remotely. Every required measurement is bundled in this post.

| State | Guest UTC | Ping | Asset |
|---|---|---|---|
| Subnet peering | 08:15:00 | 0/5 | [subnet.json](assets/enforcement/subnet.json) |
| Full VNet peering | 08:24:16 | 5/5 | [full.json](assets/enforcement/full.json) |
| Subnet peering restored | 08:27:50 | 0/5 | [restored.json](assets/enforcement/restored.json) |
| Remote `VnetLocal` UDR probe | 08:17:10 | 0/5; effective `/32` is `None` | [vnetlocal.json](assets/enforcement/vnetlocal.json) |

Each of the three comparison assets contains complete decoded **two-endpoint** NIC effective-route outputs, complete source Run Command output, selected configured route-table fields, both peering directions and selected VM power/identity fields. It does not claim new NVA effective-route captures while those VMs were deallocated.

Additional evidence:

- [VNetPeering rejection](assets/enforcement/vnetpeering-rejection.json): the requested fields, exact CLI service error, an independent empty-table read and no-replay reconciliation. No HTTP status number is inferred.
- [NSG controls](assets/enforcement/nsg-controls.json): creation and pre-removal snapshots of the same narrow ICMP rule on both endpoint NSGs, not separate per-phase NSG reads.
- [Verification](assets/enforcement/verification.json): independent saved-evidence experiment verdict, explicit untested cases, and separate restoration PASS. The restoration comparison found 44 unequal leaves: 41 ETags and three disk ownership-update timestamps, with no configuration differences after those exclusions. Final reads span 08:33:01 through 08:33:47 UTC. This is a saved-state check, not a fresh observation during publication or a disk-content equivalence claim.
- [Provenance](assets/enforcement/provenance.json): every selected raw source filename and SHA-256, with transformation rules by output type.
- Diagram sources: [direct comparison SVG](assets/enforcement-contrast.svg) and [historical transit SVG](assets/historical-transit.svg). The post embeds their locally rendered PNGs for predictable inline display.

### Sanitization and fidelity

Raw JSON wrappers store their output in a `stdout` string. Exports decode it to `output`, retaining UTC/completion timestamps, status, exit code and stderr. Effective-route arrays and Run Command `value[].message` are retained in full without rewriting route fields, private IPs, packet counts, timings or guest command text.

Configuration and power records are allowlisted projections, not copies of full VM resources: route names/properties and propagation settings; peering properties excluding resource IDs/GUIDs; VM names, power and private IPs; and only the test NSG rules. VM IDs become stable SHA-256 fingerprints so identity continuity can be checked without publishing the IDs. Associated subnet IDs become subnet names. Keys, VM profiles, subscription/resource-group IDs, public host IPs, local paths and unrelated resource material are omitted. Public system-route ranges are retained as routing data.

The verification file is an explicitly selected summary, not a replacement raw verifier record. Source hashes refer to untouched originals. The source Linux gateway was observed in every phase; workload Linux routing was not separately captured. Phase power snapshots and the saved change record support the NVAs-off control, not continuous power telemetry.

## Historical evidence: deliberately configured transit, 2026-10-04

This measurement set is `show-output/udr-ab-20261004T165000Z`, relative to the lab. Its directory label is a collection identifier, not the observation time. The canonical guest outputs carry these UTC timestamps:

| State | Canonical source file, relative to the evidence root | Guest sample starts |
|---|---|---|
| A | `A/A-vm-hub-test-comparison-in-2-0.json` | 2026-10-04 17:47:19 |
| B | `B/B-vm-hub-test-comparison-in-1-0.json` | 2026-10-04 17:49:27 |
| A2 | `A2/A2-vm-hub-test-comparison-in-1-0.json` | 2026-10-04 17:51:48 |

For each state, the four route inputs are named `<state>-vm-<role>-effective-routes-in-1-0.json`, where `<role>` is `hub-test`, `hub-nva`, `spoke-nva`, or `workload-probe`.

A sample 1 is excluded because it used an unsupported `mtr --icmp` flag. A sample 2, B sample 1, and A2 sample 1 all use the same default-ICMP `mtr` command. No earlier `s3` captures, peered-source controls, or guest-route-only trials are mixed into this comparison.

### Preserved historical assets

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

Route comparison recursively normalizes object-key and array ordering, retaining all fields and comparing route multisets per NIC. Only the source `/32` differs. The `disableBgpRoutePropagation` flag remains `true` for the source, spoke NVA, and workload, and `false` for the hub NVA. The fixed hub `/32` takes precedence over its captured propagated `/16`; the source does not import that propagated route.

### Interpreting the historical verdict and restoration records

The verdict's PASS is expressly limited to the same-source ICMP A/B/A2 comparison. It is not a TCP/application verdict or proof of all reverse hops. Its restoration note records that A2 had removed the source route while common test setup still awaited restoration.

The separate restoration record, verified at `2026-10-04T18:12:32.743967+00:00`, supersedes that earlier pending-restore state. It reports PASS, no remaining operations, no pending cloud operations, and no restoration CLI processes. It verifies removal of temporary resources/settings and preservation of the original four VMs, NICs, and OS disks, with those VMs deallocated.

These are archived checks. Writing and reviewing this post required no further cloud operations.
