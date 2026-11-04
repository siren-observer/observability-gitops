# RE8CH dynamic tools for GitOps agents

This page is the repository entry point for the authenticated Re8ch plugin. It describes **how to discover and invoke** tools; it is not a snapshot of available tools or a grant of access. Tool names, schemas, backend health, and authorization can change between sessions and organizations.

## Before a platform operation

1. Read this repository's `AGENTS.md` and follow its GitOps ownership and PR rules. Identify the authenticated organization. Re8ch Admin is the infrastructure organization; Re8ch is the application tenant. Membership in one does not imply membership in the other.
2. Use the Re8ch plugin's `tenant_self_service_capabilities` for ordinary tenant resources and Ready namespaces. For reviewed procedures outside those resource tools, search `dynamic_skill_search` and load the relevant result. Loading a workflow does not execute a command.
3. Inspect the current Re8ch model-callable tool list. For a CLI operation, use a separately exposed tool with an explicit `argv` input schema. Copy that tool's current schema and provide only its documented arguments. Backend tool counts, authorization flags, and workflow examples do not publish an operation to this list.
4. Read the complete result and audit reference. A successful transport response alone does not prove the operation succeeded. If the required tool is absent, its backend is unavailable, or authorization fails, report that exact condition. Do not substitute local kubeconfig, SSH credentials, another organization identity, or an unlisted backend tool.

For example, if `platform_kubectl_exec` is present in the current tool list, an authorized administrator can pass `argv` such as `["get", "deployments", "-n", "NAMESPACE"]` using that tool's schema. Use bounded, named reads for inspection. A returned tool does not authorize a particular cluster write: apply this repository's ownership, review, and rollout rules to every mutation. For creates and material changes, use the platform plan-before-write workflow where published.

## Keeping this guidance current

The current plugin tool list is the model-callable inventory. Inspect it for every new task and again if a selected tool changes or fails; do not pin generated counts or input schemas in Git. When the publication contract or GitOps ownership rules change, update this page and `AGENTS.md` through a signed pull request. Platform tool registration and authorization remain server-side; editing this file cannot enable a tool.
