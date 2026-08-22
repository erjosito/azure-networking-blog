# Microsoft Foundry Agents on Private VNets: Prompt-Agent Data Proxy vs Hosted-Agent Micro VM

*Target audience: Azure Networking practitioners comfortable with VNets, NSGs, Private Link, VNet peering, and Azure DNS Private Resolver. No prior Foundry knowledge assumed.*

*Published: 2026-08-22 · Source lab: [foundry-agent-prompt-vs-hosted-networking](https://github.com/erjosito/net-lab-builder/tree/main/labs/foundry-agent-prompt-vs-hosted-networking)*

---

## The answer in one paragraph

If you are designing the VNet, NSG, and DNS architecture for Azure AI Foundry agents, **the two agent types look nearly identical from your network's point of view**: both use addresses from the same delegated `AgentSubnet`, obey the same NSG rules and UDRs you apply to that subnet, traverse the same VNet peering to reach private tool endpoints, and share the same DNS forwarding chain — with DNS Private Resolver SNAT hiding the original caller type from your custom DNS server. The meaningful differences are operational, not topological: prompt agents invoke tools through a Microsoft-managed **data proxy** you cannot inspect or SSH into, while hosted agents run **your Python code** inside an ephemeral Micro VM with its own AgentSubnet NIC; this distinction changes the invocation URL, SDK surface, cold-start latency, egress source IP behaviour, and diagnostic method — but it does not create a second VNet integration to design or a second NSG policy to maintain.

This post walks through four network paths (invocation ingress, prompt-tool egress, hosted-tool egress, and client-side function calling), the empirical evidence for each, and the practical differences that matter for a network engineer who has to deploy, secure, or troubleshoot Foundry agents in a private VNet.

---

## Contents

1. [Foundry Architecture Primer for Networking Engineers](#1-foundry-architecture-primer-for-networking-engineers)
2. [Lab Topology](#2-lab-topology)
3. [The Four Packet Paths](#3-the-four-packet-paths)
4. [Similarities: What Stays the Same](#4-similarities-what-stays-the-same)
5. [Differences: What Changes Per Agent Type](#5-differences-what-changes-per-agent-type)
6. [Empirical Evidence](#6-empirical-evidence)
7. [Code Walkthrough](#7-code-walkthrough)
8. [Diagnostic Lessons](#8-diagnostic-lessons)
9. [Design Checklist](#9-design-checklist)
10. [References](#references)

---

## 1. Foundry Architecture Primer for Networking Engineers

Azure AI Foundry is Microsoft's platform for building and deploying AI agents. From a networking perspective, three infrastructure concepts determine everything:

| Term | What it is | Your closest Azure analogy |
|------|-----------|---------------------------|
| **Foundry account** | An Azure resource (`Microsoft.CognitiveServices/accounts`, kind `AIServices`) exposing a single HTTPS endpoint: `<account>.services.ai.azure.com` | Azure API Management gateway — one DNS name, multiple APIs underneath |
| **Foundry project** | A logical namespace under the account with its own RBAC scope and endpoint prefix | An APIM product or backend pool |
| **Private endpoint** | When private networking is enabled, a standard Azure Private Endpoint in your VNet's `PESubnet` gives VNet-internal resources a private IP for the account endpoint. A private DNS zone `privatelink.services.ai.azure.com` provides split-horizon resolution. | Identical to Storage, Key Vault, or any other Private Link-enabled service |

The two concepts specific to Foundry agents:

### AgentSubnet — Foundry's network injection point

Foundry injects its managed compute into a subnet you designate, delegated to `Microsoft.App/environments`. This is the **only** subnet Foundry touches in your VNet. NSG rules and UDRs you apply to `AgentSubnet` directly govern what Foundry's managed components can reach — analogous to App Service VNet Integration, ACI network injection, or Azure Container Apps environment injection.

**What lives in AgentSubnet (Microsoft-managed, not customer-deployed):**

- **Data proxy** — handles HTTP tool calls on behalf of prompt agents. Its internal architecture is undocumented; you observe it only as a source IP in your tool server's access log.
- **Micro VM NIC** — a dedicated NIC allocated per hosted-agent invocation. Your Python code's HTTP calls originate from this NIC.

### Prompt agent vs hosted agent

| Aspect | Prompt agent | Hosted agent |
|--------|-------------|-------------|
| Code location | None — tools are OpenAPI endpoint declarations | Your `main.py`, running in a Micro VM |
| Tool execution | Foundry data proxy calls the OpenAPI URL | Your Python `requests.get()` in the Micro VM |
| Network egress | Data proxy IP from AgentSubnet | Micro VM NIC IP from same AgentSubnet |
| Deployment unit | Configuration only (system prompt + OpenAPI JSON) | Source ZIP or container image |
| Invocation protocol | Assistants API `/openai/v1/threads` then `/runs` | OpenAI Responses API stateless POST at `/agents/<name>/endpoint/protocols/openai/responses` |
| SDK control plane | Portal only (as of `azure-ai-projects` 2.3.0) | `AIProjectClient.get_openai_client(agent_name=...)` |
| Cold-start latency | Sub-second (data proxy is always-on) | 36-124 s observed (Micro VM boot + container pull) |

> **Terminology note:** "Data proxy" and "Micro VM" appear in community and Microsoft documentation, but their internal implementations are not fully described. In this post: *observed* = confirmed by `src_ip` in an HTTP echo response; *documented* = stated in an official Microsoft Learn article; *inferred* = deduced from observed behaviour consistent with documented architecture.

### Microsoft-managed vs customer-owned

| Resource | Owner | Notes |
|----------|-------|-------|
| Foundry platform (Tools Service, model inference) | **Microsoft** | Not visible in your subscription |
| Data proxy IP in AgentSubnet | **Microsoft** (injected into customer VNet) | NSG/UDR apply; you cannot configure the component |
| Micro VM NIC in AgentSubnet | **Microsoft** (injected per invocation) | Ephemeral; NSG/UDR apply |
| AgentSubnet | **Customer** | Must be delegated to `Microsoft.App/environments`; customer sets NSG and UDR |
| Private endpoint | **Customer** | Standard Azure PE |
| Private DNS zones | **Customer** | Standard Azure Private DNS |
| DNS Private Resolver | **Customer** (optional) | Needed only if custom DNS forwarding is required |

---

## 2. Lab Topology

The lab uses two peered VNets in Sweden Central. No VPN gateway. DNS Private Resolver with a forwarding ruleset routes `tools.lab` queries to a `dnsmasq` instance on `vm-tools-echo`.

The diagram below shows the full topology. Notice that **both** the data proxy and the Micro VM NIC are inside the same `AgentSubnet` (192.168.0.0/24). The VNet peering is the single data-plane bridge between Foundry's managed compute and the tool target VMs.

![Lab topology: vnet-foundry (192.168.0.0/16) peered to vnet-tools (10.1.0.0/16). AgentSubnet (192.168.0.0/24, delegated to Microsoft.App/environments) hosts both the data proxy (prompt agent, src_ip 192.168.0.x) and Micro VM NIC (hosted agent, src_ip 192.168.0.y). DNS Outbound EP (192.168.3.20) SNATs to pool 192.168.3.21-25 before forwarding to dnsmasq on vm-tools-echo.](assets/01-peered-tools-topology.png)

*[SVG](assets/01-peered-tools-topology.svg) · [Excalidraw source](assets/01-peered-tools-topology.excalidraw) · [Mermaid source](assets/01-peered-tools-topology.mmd)*

**Subnet map:**

| Subnet | CIDR | Contents |
|--------|------|----------|
| AgentSubnet | 192.168.0.0/24 | Data proxy (prompt agent) + Micro VM NICs (hosted agent) |
| PESubnet | 192.168.1.0/24 | Foundry private endpoints |
| MgmtSubnet | 192.168.2.0/27 | `vm-diag` 192.168.2.4 |
| DNSInboundSubnet | 192.168.3.0/28 | DNS Resolver inbound EP 192.168.3.4 |
| DNSOutboundSubnet | 192.168.3.16/28 | DNS Resolver outbound EP 192.168.3.20; SNAT pool .21-25 |
| EchoSubnet (vnet-tools) | 10.1.100.0/24 | `vm-tools-echo` — echo service + dnsmasq |
| CtrlSubnet (vnet-tools) | 10.1.200.0/24 | `vm-tools-ctrl` — echo service |

---

## 3. The Four Packet Paths

The diagram below compares the three egress paths side by side. Paths 1 and 2 both terminate at the data proxy before reaching the tool server — the agent's code and the caller are not in the data path. Path 3 (hosted direct code) is where your Python runs in the data path.

![Three egress paths: Path 1 (prompt agent) — caller to Tools Service to data proxy to tool server (src_ip 192.168.0.x, baseline evidence). Path 2 (hosted agent Toolbox) — caller to Micro VM to data proxy to tool server. Path 3 (hosted agent direct Python code, confirmed) — caller to Micro VM (requests.get) directly to tool server; src_ip 192.168.0.y changes per invocation.](assets/03-agent-egress-paths.png)

*[SVG](assets/03-agent-egress-paths.svg) · [Excalidraw source](assets/03-agent-egress-paths.excalidraw) · [Mermaid source](assets/03-agent-egress-paths.mmd)*

### Path 1 — Invocation ingress: Caller to Foundry endpoint

Every agent type starts here. The caller sends HTTPS to `<account>.services.ai.azure.com`:

```
Caller
  Public path (workstation outside VNet):
    Public DNS resolves to public IP; TCP 443 to Foundry public endpoint

  Private path (vm-diag inside VNet):
    privatelink.services.ai.azure.com zone resolves to PE IP (192.168.1.x in PESubnet)
    TCP 443 via private endpoint to Foundry
```

URL differs by agent type:
- **Prompt agent:** `/openai/v1/threads` (create) then `/openai/v1/threads/{id}/runs` — the Assistants API.
- **Hosted agent:** `/api/projects/<project>/agents/<name>/endpoint/protocols/openai/responses` — the OpenAI Responses API, stateless.

RBAC for hosted agent invocation: **Foundry Agent Consumer** role at project scope ([docs](https://learn.microsoft.com/azure/foundry/concepts/rbac-ai-foundry)).

### Path 2 — Prompt-tool egress: Data proxy to tool target

> **Evidence scope:** This path uses evidence from the sibling lab (2026-08-14) and was **not re-run** in this lab. `azure-ai-projects 2.3.0` does not expose an Assistants API; prompt agents with HTTP Connection resources can only be created and invoked through the Foundry portal. The path is confirmed documented behaviour; the observed source IPs are from prior lab runs.

```
Foundry Tools Service
  -> Data Proxy (AgentSubnet 192.168.0.x, Microsoft-managed)
  -> DNS: 168.63.129.16 -> DNS Resolver outbound EP (SNAT pool 192.168.3.21-25)
         -> dnsmasq (10.1.100.4:53) -> A 10.1.100.4
  -> TCP 80 via VNet peering -> vm-tools-echo 10.1.100.4
  src_ip observed at target: 192.168.0.49, 192.168.0.239  (AgentSubnet /24)
  Status: BASELINE from sibling lab (2026-08-14); not empirically re-run here.
```

The data proxy cannot be configured, SSHed into, or inspected directly. Its existence is inferred from observed `src_ip` values and the [Foundry private networking docs](https://learn.microsoft.com/azure/foundry/how-to/configure-private-link). *(Inferred/undocumented internal architecture.)*

### Path 3 — Hosted-tool egress: Micro VM NIC to tool target

This is the path your Python code takes when calling `requests.get()` inside a hosted agent:

```
Hosted agent code (main.py, requests.get)
  -> Micro VM NIC (AgentSubnet 192.168.0.y, Microsoft-managed, ephemeral)
  -> DNS: 168.63.129.16 -> DNS Resolver outbound EP -> dnsmasq -> A 10.1.100.4
  -> TCP 80 via VNet peering -> vm-tools-echo 10.1.100.4
  src_ip observed: 192.168.0.238, .28, .110, .92, .142, .165, .124
  (changes per invocation -- ephemeral Micro VM NIC allocation)
  Status: CONFIRMED -- 7 invocations (2026-08-21)
```

The Micro VM NIC uses the **same AgentSubnet** and same DNS forwarding chain as the data proxy ([docs](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent-code)).

### Path 4 — Client-side function calling: Caller executes tools directly

Not a Foundry agent path — the model returns `tool_calls` JSON and the **caller's own machine** executes the HTTP calls:

```
Caller -> LLM call to /openai/v1/ (standard Foundry OpenAI endpoint)
       -> Model returns tool_calls JSON
       -> Caller executes HTTP calls from its own NIC

From workstation (outside VNet):
  DNS query for echo.tools.lab -> FAIL
  [Errno 11001] getaddrinfo failed -- tools.lab not resolvable outside VNet

From vm-diag (inside VNet, deduced):
  DNS resolves via same chain -> 10.1.100.4
  src_ip at target: 192.168.2.4 (MgmtSubnet -- NOT AgentSubnet)
```

This path proves the VNet isolation design: private tool targets require a VNet-internal egress path — hosted agent or data proxy. Client-side function calling from outside the VNet cannot reach private endpoints.

---

## 4. Similarities: What Stays the Same

### Same subnet, same NSG, same peering

Both the data proxy and the Micro VM NIC draw addresses from `AgentSubnet` (192.168.0.0/24). A single NSG on `AgentSubnet`, a single bidirectional VNet peering, and a single inbound NSG rule on the tool-target subnet cover both agent types. Rules 110 and 120 are identical for both — only 125 and 126 are hosted-agent-specific (deployment only):

**AgentSubnet outbound rules (nsg-agentsubnet):**

| Priority | Direction | Destination | Port | Purpose |
|----------|-----------|-------------|------|---------|
| 110 | Outbound | `10.1.100.0/24` | 80, 443 | Tool calls to echo VM (both agent types) |
| 120 | Outbound | `10.1.200.0/24` | 80, 443 | Tool calls to ctrl VM (both agent types) |
| 125 | Outbound | `MicrosoftContainerRegistry` | 443 | MCR base image pull (hosted deploy only) |
| 126 | Outbound | `AzureActiveDirectory` | 443 | Hosted agent auth (deploy + runtime) |

**nsg-tools inbound rules (EchoSubnet and CtrlSubnet):**

| Priority | Direction | Source | Port | Purpose |
|----------|-----------|--------|------|---------|
| 100 | Inbound | `192.168.0.0/16` | 80, 443 | Data proxy + Micro VM calls (both types) |

### Same DNS forwarding chain

All resources in `vnet-foundry` — data proxy, Micro VM NICs, and `vm-diag` — share the same VNet-level DNS forwarding ruleset. The DNS Private Resolver outbound endpoint (`192.168.3.20`) applies SNAT from the `192.168.3.16/28` pool before forwarding to dnsmasq. From dnsmasq's perspective, every DNS query from every caller in `vnet-foundry` appears to come from `192.168.3.21-25`, regardless of whether it originated from the data proxy, a Micro VM NIC, or `vm-diag`. This is [documented behaviour](https://learn.microsoft.com/azure/dns/dns-private-resolver-overview) for Azure DNS Private Resolver.

The diagram below shows the resolution chain for all caller contexts. The data proxy, Micro VM NIC, and `vm-diag` all converge at the same outbound endpoint and dnsmasq sees an undifferentiated source from the SNAT pool.

![DNS resolution chain. All VNet callers (data proxy, Micro VM NIC, vm-diag) query Azure DNS 168.63.129.16. Forwarding ruleset routes tools.lab to DNS Outbound EP 192.168.3.20; SNAT pool 192.168.3.21-25 hides original caller at dnsmasq. Private DNS zone resolves Foundry endpoint to PESubnet IP. Workstation outside VNet receives getaddrinfo failure — NXDOMAIN for tools.lab.](assets/04-dns-resolution-contexts.png)

*[SVG](assets/04-dns-resolution-contexts.svg) · [Excalidraw source](assets/04-dns-resolution-contexts.excalidraw) · [Mermaid source](assets/04-dns-resolution-contexts.mmd)*

### Same peering and routing model

The bidirectional VNet peering adds `10.1.0.0/16` via `VNetPeering` to the effective routes on `AgentSubnet`. Both the data proxy and Micro VM NIC use the same route — no separate routing per agent type.

---

## 5. Differences: What Changes Per Agent Type

### Programmability and SDK surface

`azure-ai-projects 2.3.0` `AgentsOperations` manages **hosted agent lifecycle only** (`create_version`, `create_session`, `enable`, `disable`). There is no `create_agent()` or Assistants API (`threads`/`runs`) in this SDK version. Foundry portal prompt agents with HTTP Connection resources **cannot be created programmatically** via `azure-ai-projects 2.3.0`.

Consequence for the lab: the prompt-agent data-proxy path (Path 2) could not be re-run programmatically. The client-side function calling path (`get_openai_client()` without `agent_name`) is not the data-proxy path — it executes tool calls on the caller's machine. Data-proxy evidence is inherited from the sibling lab (2026-08-14) and is explicitly marked as baseline throughout this post.

### Invocation URL and protocol

| Agent type | Invocation URL | Protocol |
|-----------|---------------|----------|
| Prompt agent | `<endpoint>/openai/v1/threads` then `/runs` | Assistants API — stateful |
| Hosted agent | `<endpoint>/api/projects/<project>/agents/<name>/endpoint/protocols/openai/responses` | OpenAI Responses API — stateless |

The SDK routes to the hosted agent by patching `base_url`:

```python
oai = client.get_openai_client(agent_name="echo-probe-agent")
# base_url: <endpoint>/agents/<name>/endpoint/protocols/openai
resp = oai.responses.create(
    model="echo-probe-agent",  # must equal agent name, not a model deployment name
    input="probe both endpoints",
    stream=False,
)
```

Without `agent_name`, `get_openai_client()` routes to `/openai/v1/` — no agent routing.

### Deployment egress for hosted agents

Hosted agents require a source-code deployment step. At Micro VM startup, Foundry pulls the base container image from `mcr.microsoft.com` regardless of whether `remote_build` or `bundled` dependency mode is used — NSG rules 125 and 126 are required for both modes ([docs](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent-code)). Deployment takes 3-5 minutes; the rules must be in place before the first deploy attempt.

### Cold-start latency

**Prompt agent:** Data proxy is always-on. Tool calls have sub-second setup overhead.

**Hosted agent:** Stateless Responses API invocations may spawn a fresh Micro VM. Cold-start latency ranged from 36 s (warm) to 124 s (cold) across 7 invocations. The Sessions API (`AgentsOperations.create_session()`) offers a persistent Micro VM sandbox to avoid cold start, at the cost of keeping the Micro VM running between calls.

### Ephemeral source IP

**Data proxy** (prompt agent): Observed `192.168.0.49`, `192.168.0.239` from the sibling lab — *baseline only*. Pool size and allocation mechanism are undocumented.

**Micro VM NIC** (hosted agent): Source IP changes per invocation — observed `192.168.0.238`, `.28`, `.110`, `.92`, `.142`, `.165`, `.124` across 7 invocations. Cannot be pinned. NSG rules and application-layer allowlists must use the AgentSubnet CIDR (`192.168.0.0/24`), not individual IPs.

Both draw from the same AgentSubnet `/24` pool. At the tool server, the distinction is visible only as a different source IP value — not as a different subnet or VLAN.

### Diagnostics

**Prompt agent:** No SSH access to the data proxy. No container logs. Debugging limited to tool server access logs and Foundry portal run status. Unreachability from the data proxy produces a vague tool error with no network stack trace.

**Hosted agent:** Your code runs in the Micro VM. Add `print()` statements, structured logging, explicit exception capture. Foundry surfaces stdout/stderr in deployment logs. Exception messages from failed `requests.get()` calls are reported verbatim in the LLM response.

---

## 6. Empirical Evidence

### H2 confirmed: Micro VM NIC egress (hosted agent direct code)

Seven invocations of `echo-probe-agent` via the Responses API (3 REST direct, 3 SDK, 1 SSE streaming). All 7 returned HTTP 200 from both `echo.tools.lab` and `ctrl.tools.lab`:

| Run | Method | src_ip (echo) | src_ip (ctrl) | Latency |
|-----|--------|---------------|---------------|---------|
| 1 | REST direct | 192.168.0.238 | 192.168.0.238 | ~38 s |
| 2 | REST direct | 192.168.0.28 | 192.168.0.28 | ~53 s |
| 3 | REST direct | 192.168.0.110 | 192.168.0.110 | ~59 s |
| 4 | SDK (`AIProjectClient`) | 192.168.0.92 | 192.168.0.92 | 124 s |
| 5 | SDK (`AIProjectClient`) | 192.168.0.142 | 192.168.0.142 | 37 s |
| 6 | SDK (`AIProjectClient`) | 192.168.0.165 | 192.168.0.165 | 51 s |
| 7 | REST SSE streaming | 192.168.0.124 | 192.168.0.124 | 41 s (213 SSE events) |

Key observations: both `echo` and `ctrl` probes in a single invocation share the same source IP (one NIC per run). Source IP changes per invocation — ephemeral allocation. All IPs are in `192.168.0.0/24` (AgentSubnet), the same `/24` as the data proxy.

### H1 baseline: data proxy egress (prompt agent tool call)

Not re-run in this lab (SDK limitation above). Evidence from sibling lab (2026-08-14): data proxy `src_ip` was `192.168.0.49` and `192.168.0.239` — same `/24` as the Micro VM NICs. Mechanism is not re-run; no raw invocation record from the data proxy exists in this lab.

### H3 confirmed: DNS is context-transparent

Dnsmasq query log from `vm-tools-echo` (2026-08-21). All queries arrive from the `DNSOutboundSubnet` SNAT pool (`192.168.3.21-25`), regardless of originating caller:

```
# Hosted agent Micro VM NIC -- invocations 1, 2, 3
Aug 21 06:12:35 dnsmasq[622]: query[A] echo.tools.lab from 192.168.3.23
Aug 21 06:12:35 dnsmasq[622]: query[A] ctrl.tools.lab from 192.168.3.22
Aug 21 06:13:54 dnsmasq[622]: query[A] echo.tools.lab from 192.168.3.24
Aug 21 06:13:54 dnsmasq[622]: query[A] ctrl.tools.lab from 192.168.3.21

# vm-diag curl test (MgmtSubnet 192.168.2.4)
Aug 21 06:24:15 dnsmasq[622]: query[A] echo.tools.lab from 192.168.3.24
Aug 21 06:24:15 dnsmasq[622]: query[A] ctrl.tools.lab from 192.168.3.21
```

The SNAT pool hides the original caller identity — expected, documented behaviour. To get per-agent DNS attribution, enable Azure Monitor Diagnostic Settings on the DNS Private Resolver to capture the pre-SNAT originating client IP.

### NSG negative test

A temporary deny rule (priority 100, source `192.168.0.0/16`, ports 80/443 inbound) was added to `nsg-tools`. With the rule active:

- **Hosted agent tool calls:** Both `probe_echo` and `probe_ctrl` returned `"Error: Function failed."` — no network context in the error.
- **DNS still succeeded:** Dnsmasq logs show DNS queries arriving from `192.168.3.21-25` and being answered correctly. The TCP block did not affect DNS traffic from `192.168.3.16/28`, allowed by a separate rule (source `192.168.3.16/28`, port 53).

Diagnostic lesson: when an agent tool call fails with a generic error, DNS resolution and TCP reachability are independent failure modes. Check both. The dnsmasq log is the evidence source for DNS; the agent error string alone is not sufficient to identify the blocking layer. The NSG rule was restored before subsequent runs.

### Client-side function calling DNS failure

From a workstation outside the VNet, executing model tool calls locally:

```
ConnectionError: Failed to resolve 'echo.tools.lab' ([Errno 11001] getaddrinfo failed)
ConnectionError: Failed to resolve 'ctrl.tools.lab' ([Errno 11001] getaddrinfo failed)
```

`tools.lab` is not registered in public DNS. The DNS Private Resolver forwarding ruleset and dnsmasq are VNet-internal. Any caller outside the VNet cannot resolve these names — private tool targets require a VNet-internal egress path.

---

## 7. Code Walkthrough

### Why official Foundry SDK and not LangChain

The test script uses `azure-ai-projects 2.3.0` (`AIProjectClient`), not LangChain or Semantic Kernel. LangChain's `AzureAIChatCompletionsModel` and Semantic Kernel's `AzureAIInferenceChatCompletion` both abstract the routing layer — the SDK switches base URLs and auth headers behind the scenes. For network-layer evidence collection, you need to know exactly which HTTP request was made. `AIProjectClient` is Microsoft-owned, officially supported, and its `get_openai_client(agent_name=...)` base URL patch is documented and inspectable. Third-party frameworks add abstraction overhead that obscures that audit trail.

### Hosted agent: `main.py`

The agent uses the Microsoft Agent Framework (MAF) — `agent_framework_openai 1.12.0` — which is the **internal server-side runtime** running inside the Micro VM. External callers do not import MAF; they use `AIProjectClient.get_openai_client(agent_name=...)`.

Two tool functions probe the network. FQDNs are used instead of hard-coded IPs because the FQDN appears verbatim in the target's `request_url` field (lab evidence for DNS resolution), and FQDNs prove the DNS chain works end-to-end from the Micro VM NIC:

```python
_ECHO_URL = "http://echo.tools.lab/api/echo"
_CTRL_URL = "http://ctrl.tools.lab/api/echo"
_TIMEOUT = (5, 10)  # (connect_timeout, read_timeout) seconds

def probe_echo() -> dict:
    resp = requests.get(_ECHO_URL, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()
    # Returns: {"label": "echo", "server_ip": "10.1.100.4",
    #           "src_ip": "192.168.0.y", "request_url": "http://echo.tools.lab/api/echo"}
```

Exceptions are intentionally **not caught** — a `ConnectionError` or `Timeout` is itself a meaningful network result. The system prompt instructs the LLM to report exception messages verbatim:

```python
agent = Agent(
    client=client,
    instructions=(
        "You are echo-probe-agent. When asked to probe the echo endpoints, call "
        "probe_echo() and probe_ctrl() and return ALL fields: label, server_ip, "
        "src_ip, and request_url. Do not omit or summarise -- exact values are "
        "required for lab evidence. If a tool call raises an exception, report "
        "the exception message verbatim."
    ),
    tools=[probe_echo, probe_ctrl],
    default_options={"store": False},  # stateless; no conversation history
)
server = ResponsesHostServer(agent)
server.run()  # blocks until SIGTERM from Foundry on scale-in
```

### External caller: `tests/probe_network.py`

The invocation side routes to the hosted agent via `get_openai_client(agent_name=...)`:

```python
client = AIProjectClient(
    endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
    credential=credential,
    allow_preview=True,  # required for hosted-agent routing in azure-ai-projects 2.x
)
oai = client.get_openai_client(agent_name="echo-probe-agent")
# base_url: <endpoint>/agents/echo-probe-agent/endpoint/protocols/openai

resp = oai.responses.create(
    model="echo-probe-agent",  # must equal agent name, not a model deployment name
    input="probe both endpoints and return all fields",
    stream=False,
)
```

For the client-side function calling **control path**, the same client without `agent_name` routes to the standard model endpoint where tool calls execute on the caller:

```python
oai_std = client.get_openai_client()  # base_url: <endpoint>/openai/v1/
resp = oai_std.responses.create(
    model="gpt-5-mini",
    input="probe both endpoints",
    tools=[{"type": "function", "function": probe_echo_def}],
)
# Tool calls execute here, on the caller machine.
# From workstation: DNS fails -- tools.lab not resolvable outside VNet.
```

The invocation diagram maps the full client-to-agent flow, including RBAC and private DNS. Notice the split between the public path and the private path via private endpoint:

![Client invocation paths. Public path: workstation uses public DNS to reach Foundry endpoint directly. Private path: vm-diag (192.168.2.4) resolves via private DNS zone to PE IP (PESubnet 192.168.1.x), then HTTPS to private endpoint. Deploy surface: VS Code Foundry Toolkit or azd ai agent deploy uploads source-ZIP. Foundry spawns Micro VM in AgentSubnet (192.168.0.y). Micro VM calls echo.tools.lab and ctrl.tools.lab via VNet peering. Foundry Agent Consumer RBAC required on invoking identity.](assets/06-programmatic-invocation.png)

*[SVG](assets/06-programmatic-invocation.svg) · [Excalidraw source](assets/06-programmatic-invocation.excalidraw) · [Mermaid source](assets/06-programmatic-invocation.mmd)*

---

## 8. Diagnostic Lessons

**1. NSG negative test: DNS and TCP are independent failure modes.** When the TCP deny rule was active on `nsg-tools`, the hosted agent returned a generic `"Function failed."` The dnsmasq log showed DNS resolution still working — the DNS source (`192.168.3.16/28`) was covered by a separate allow rule. When you see a tool-call failure, verify DNS resolution independently before assuming a routing or application problem.

**2. DNS Private Resolver SNAT hides agent type.** Your custom DNS server sees source IPs from the resolver's SNAT pool (`192.168.3.21-25`), not from the original agent's NIC. You cannot distinguish a Micro VM query from a `vm-diag` query by DNS source IP alone. To get per-agent DNS attribution, enable Azure Monitor Diagnostic Settings on the DNS Private Resolver to capture the pre-SNAT originating client IP.

**3. Ephemeral Micro VM source IPs cannot be allowlisted as individual addresses.** Hosted-agent tool-call source IPs change per invocation. NSG rules, Azure Firewall rules, and application-layer allowlists must use the AgentSubnet CIDR (`192.168.0.0/24`), not individual IPs.

**4. Client-side function calling from outside the VNet fails silently on DNS.** When the tool target uses a private DNS name, the failure is a DNS resolution error — not a TCP connection refused. If you start debugging at the tool server, you will see no traffic. Look at the caller side first: `getaddrinfo` failure means the DNS zone is not reachable from the caller's network.

---

## 9. Design Checklist

**Required for both agent types:**
- [ ] `AgentSubnet` delegated to `Microsoft.App/environments` in your VNet
- [ ] Bidirectional VNet peering between the Foundry VNet and any tool-target VNet
- [ ] `AgentSubnet` outbound NSG: allow TCP 80/443 to tool-target subnet CIDRs
- [ ] Tool-target subnet inbound NSG: allow TCP 80/443 from `AgentSubnet` CIDR
- [ ] DNS Private Resolver forwarding ruleset linked to the Foundry VNet (for custom DNS names)
- [ ] Private endpoint for `<account>.services.ai.azure.com` in PESubnet (if public access disabled)
- [ ] Private DNS zone `privatelink.services.ai.azure.com` linked to the Foundry VNet

**Required for hosted agents only:**
- [ ] `AgentSubnet` outbound NSG: allow TCP 443 to `MicrosoftContainerRegistry` (required regardless of deploy mode)
- [ ] `AgentSubnet` outbound NSG: allow TCP 443 to `AzureActiveDirectory`
- [ ] **Foundry Agent Consumer** RBAC role for the invoking identity at project scope
- [ ] Source-code ZIP with `bundled` dependencies (recommended) or `remote_build`

**Do not:**
- [ ] Allowlist individual source IPs for Micro VM tool calls — use the AgentSubnet CIDR
- [ ] Create a private DNS zone with the same name as any forwarding ruleset rule — private zones take precedence and break the forwarding chain

---

## References

See [references.md](references.md) for the full annotated reference list.

**Source lab (public):** [erjosito/net-lab-builder — foundry-agent-prompt-vs-hosted-networking](https://github.com/erjosito/net-lab-builder/tree/main/labs/foundry-agent-prompt-vs-hosted-networking)

