# References — foundry-agent-prompt-vs-hosted-networking post

## Source lab

- **Lab repository (public):** [erjosito/net-lab-builder](https://github.com/erjosito/net-lab-builder/tree/main/labs/foundry-agent-prompt-vs-hosted-networking)
  Direct link to `foundry-agent-prompt-vs-hosted-networking` lab folder containing all Mermaid diagrams, test scripts, raw output, and design documentation.

## Official Microsoft Learn documentation

- **Configure private networking for Azure AI Foundry**
  <https://learn.microsoft.com/azure/foundry/how-to/configure-private-link>
  Primary reference for Private Endpoint, Private DNS zone, and AgentSubnet delegation requirements.

- **Deploy a hosted agent from source code**
  <https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent-code>
  Documents `remote_build` vs `bundled` modes, MCR and AAD outbound requirements, and the Micro VM architecture.

- **Azure AI Foundry agents — hosted agents overview**
  <https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents-overview>
  Explains the Responses API protocol, agent lifecycle, and SDK invocation patterns.

- **RBAC roles for Azure AI Foundry**
  <https://learn.microsoft.com/azure/foundry/concepts/rbac-ai-foundry>
  Defines Foundry Agent Consumer, Foundry Project Manager, and other built-in roles used in agent invocation and deployment.

- **Azure DNS Private Resolver overview**
  <https://learn.microsoft.com/azure/dns/dns-private-resolver-overview>
  Documents forwarding rulesets, outbound endpoint SNAT behaviour, and VNet-level ruleset linking.

- **Azure DNS Private Resolver — endpoints and rulesets**
  <https://learn.microsoft.com/azure/dns/private-resolver-endpoints-rulesets>
  Details on how forwarding rulesets are linked at the VNet level and how the outbound endpoint performs SNAT.

- **OpenAI Responses API reference**
  <https://platform.openai.com/docs/api-reference/responses>
  Protocol reference for the stateless Responses API used by hosted agents.

- **azure-ai-projects Python SDK reference**
  <https://learn.microsoft.com/python/api/overview/azure/ai-projects-readme>
  `AIProjectClient`, `AgentsOperations`, `get_openai_client` API surface.

- **Azure managed identity and DefaultAzureCredential**
  <https://learn.microsoft.com/azure/developer/python/sdk/authentication-overview>
  Authentication chain used by hosted agents inside Micro VMs and by external callers.

## Related concepts

- **App Service VNet Integration** (analogous to AgentSubnet delegation):
  <https://learn.microsoft.com/azure/app-service/overview-vnet-integration>

- **Azure Container Apps environment networking** (analogous to Micro VM NIC injection):
  <https://learn.microsoft.com/azure/container-apps/networking>

- **Azure Private Link overview** (PE + private DNS zone pattern used by Foundry account endpoint):
  <https://learn.microsoft.com/azure/private-link/private-link-overview>

