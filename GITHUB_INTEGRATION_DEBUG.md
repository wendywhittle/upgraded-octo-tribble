GitHub integration appears to have a schema/runtime mismatch.

The GitHub tool is present in the available tool schema and exposes repository functions including get_repo, fetch_file, create_file, and update_file.

However, when an actual GitHub operation is invoked, the runtime immediately returns:

“The GitHub tool has been disabled. Do not send any more messages to GitHub.”

This occurs even for a basic get_repo request, before the repository itself appears to be evaluated.

Repository:
wendywhittle/upgraded-octo-tribble

The behavior suggests the GitHub capability is being registered/discoverable at the schema layer but disabled at the execution/runtime layer.

Potential causes worth investigating:

* stale tool/connector state
* feature-flag mismatch
* capability state not synchronized with the tool schema
* session-level tool gating
* connection/permission state propagation
* rollout or runtime configuration issue

This does not currently look like a repository-level permissions problem, because the invocation appears to be rejected before GitHub processes the repository request.

Expected: A discovered GitHub function should either execute or return a GitHub authentication/authorization/repository error.

Actual: The runtime reports the entire GitHub tool as disabled despite exposing the GitHub functions in the active schema.

Please investigate the boundary between tool registration and tool execution.
