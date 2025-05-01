import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const serverUrl = process.env.MCP_SERVER_URL || "http://localhost:8080";

const transport = new StreamableHTTPClientTransport(new URL(serverUrl + "/mcp"));

const client = new Client(
    {
        name: "example-client",
        version: "1.0.0"
    }
);

async function main(): Promise<void> {
    await client.connect(transport);

    // Get list of available tools
    const tools = await client.listTools();
    console.log("Available tools:", tools);

    // Call the calculate tool
    // const toolResult = await client.callTool({ 
    //   "name": "calculate", 
    //   "arguments": { "a": 5, "b": 55, "operation": "add" } 
    // });
    // console.log("Calculation result:", toolResult.content);

    // Call the getNewsHeadline tool
    const newsResult = await client.callTool({
      "name": "getNewsHeadline",
      "arguments": { "url": "https://aws.amazon.com/blogs/aws/" }
    });
    console.log("News headline:", newsResult.content);
}

main().catch((error: unknown) => {
    console.error('Error running MCP client:', error);
    process.exit(1);
});