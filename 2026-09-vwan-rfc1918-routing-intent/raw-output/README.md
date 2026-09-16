# Raw evidence index

All files are sanitized CLI outputs from the live lab.

| Phase | File | Observation point |
|---|---|---|
| Before vHub attachment | `01-before-vhub-er-msee-primary.json` | Primary MSEE route table |
| Before vHub attachment | `01-before-vhub-er-msee-secondary.json` | Secondary MSEE route table |
| Before vHub attachment | `01-before-vhub-er-gcp-router.json` | GCP Cloud Router status |
| ER attached, Routing Intent off | `02-er-attached-ri-off-msee-primary.json` | Primary MSEE route table |
| ER attached, Routing Intent off | `02-er-attached-ri-off-msee-secondary.json` | Secondary MSEE route table |
| ER attached, Routing Intent off | `02-er-attached-ri-off-vhub-default.json` | vHub effective routes |
| ER attached, Routing Intent off | `02-er-attached-ri-off-er-connection.json` | ExpressRoute connection effective routes |
| Private Routing Intent on | `03-er-attached-ri-on-msee-primary.json` | Primary MSEE route table |
| Private Routing Intent on | `03-er-attached-ri-on-msee-secondary.json` | Secondary MSEE route table |
| Private Routing Intent on | `03-er-attached-ri-on-default-route-table.json` | `defaultRouteTable`, including the injected RFC1918 policy route |
| Private Routing Intent on | `03-er-attached-ri-on-spoke-connection.json` | Spoke connection pre-inspection effective routes |
| Private Routing Intent on | `03-er-attached-ri-on-firewall-effective.json` | Azure Firewall post-inspection effective routes |
| Private Routing Intent on | `03-er-attached-ri-on-er-connection.json` | ExpressRoute connection effective routes |
| Private Routing Intent on | `03-er-attached-ri-on-gcp-router.json` | GCP Cloud Router status |
| Data plane | `04-traffic-azure-to-gcp.txt` | ICMP and TCP from `172.21.1.10` to `10.20.0.10` |
| Data plane | `04-traffic-gcp-to-azure.txt` | ICMP and TCP from `10.20.0.10` to `172.21.1.10` |

