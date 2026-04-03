## ADDED Requirements

### Requirement: MCP Gateway proxies all tool calls through a safety layer
The tool runtime SHALL expose `execute_tool(tool_name, arguments) -> ToolResult`. Before executing any tool, the safety module MUST validate the tool name against the registered tool registry and validate arguments against the tool's declared JSON schema.

#### Scenario: Valid tool call executes and returns result
- **WHEN** `execute_tool("read_file", {"path": "/workspace/main.py"})` is called and the tool is registered
- **THEN** the tool executes and returns a `ToolResult` with `status="success"` and `output` containing the file contents

#### Scenario: Unregistered tool is rejected
- **WHEN** `execute_tool("unknown_tool", {})` is called
- **THEN** the tool runtime raises `ToolNotFoundError` without executing anything

#### Scenario: Invalid arguments are rejected before execution
- **WHEN** `execute_tool` is called with arguments that fail the tool's JSON schema validation
- **THEN** the tool runtime raises `ToolArgumentValidationError` without executing the tool

### Requirement: Tool registry is populated at startup
The tool runtime SHALL load all available MCP tool schemas at application startup via `registry.load_tools(mcp_server_url)`. The registry MUST be queryable for tool schemas by name.

#### Scenario: Registry provides tool schema
- **WHEN** `registry.get_tool_schema("search_files")` is called after startup
- **THEN** it returns the complete JSON schema for the tool's input parameters

### Requirement: The orchestrator governs when tools execute
The tool runtime MUST NOT initiate tool calls autonomously. It SHALL ONLY execute a tool when called by the orchestrator's tool loop node.

#### Scenario: Tool runtime does not self-invoke
- **WHEN** a tool result contains a reference to another tool
- **THEN** the tool runtime returns the result as-is and MUST NOT recursively call `execute_tool`

### Requirement: Tool results are bounded in size
The tool runtime SHALL truncate tool output payloads exceeding a configured `max_output_tokens` limit and append a truncation notice to the returned `ToolResult`.

#### Scenario: Large tool output is truncated
- **WHEN** a tool returns output exceeding `max_output_tokens`
- **THEN** `ToolResult.output` contains the first `max_output_tokens` worth of content and `ToolResult.truncated=True`
