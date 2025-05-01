import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express from "express";
import { z } from "zod";
import { JSDOM } from "jsdom";

// Create MCP server
const server = new McpServer({
  name: "Example MCP Server",
  version: "1.0.0"
});


function parseAWSBlogHTML(html: string): BlogPost[] {
  // Create a DOM using jsdom
  const dom = new JSDOM(html);
  const doc = dom.window.document;
  
  // Find all blog post elements
  const blogPostElements = doc.querySelectorAll('article.blog-post');
  const blogPosts: BlogPost[] = [];
  
  blogPostElements.forEach((postElement: { querySelector: (arg0: string) => any; }) => {
    // Extract title
    const titleElement = postElement.querySelector('.blog-post-title a');
    const title = titleElement ? titleElement.textContent?.trim() : '';
    
    // Extract URL
    const url = titleElement ? titleElement.getAttribute('href') : '';
    
    // Extract image URL
    const imageElement = postElement.querySelector('img.wp-post-image');
    const imageUrl = imageElement ? imageElement.getAttribute('src') : '';
    
    // Extract author
    const authorElement = postElement.querySelector('footer span[property="author"] [property="name"]');
    const author = authorElement ? authorElement.textContent?.trim() : '';
    
    // Extract date
    const dateElement = postElement.querySelector('time[property="datePublished"]');
    const dateText = dateElement ? dateElement.textContent?.trim() : '';
    const dateISO = dateElement ? dateElement.getAttribute('datetime') : '';
    
    // Extract categories
    const categoriesElement = postElement.querySelector('.blog-post-categories');
    const categories: string[] = [];
    
    if (categoriesElement) {
      const categoryLinks = categoriesElement.querySelectorAll('a');
      categoryLinks.forEach((link: { textContent: string; }) => {
        const category = link.textContent?.trim();
        if (category) categories.push(category);
      });
    }
    
    // Extract excerpt
    const excerptElement = postElement.querySelector('.blog-post-excerpt');
    const excerpt = excerptElement ? excerptElement.textContent?.trim() : '';
    
    blogPosts.push({
      title,
      url,
      imageUrl,
      author,
      dateText,
      dateISO,
      categories,
      excerpt
    });
  });
  
  return blogPosts;
}

// Interface for the blog post data structure
interface BlogPost {
  title: string | undefined;
  url: string | null;
  imageUrl: string | null;
  author: string | undefined;
  dateText: string | undefined;
  dateISO: string | null;
  categories: string[];
  excerpt: string | undefined;
}


// Create Express application
const app = express();
app.use(express.json());

// Add a tool - implementing a simple calculator
server.tool(
  "calculate",
  { a: z.number(), b: z.number(), operation: z.enum(["add", "subtract", "multiply", "divide"]) },
  async ({ a, b, operation }) => {
    let result;
    switch (operation) {
      case "add": result = a + b; break;
      case "subtract": result = a - b; break;
      case "multiply": result = a * b; break;
      case "divide": result = a / b; break;
    }
    return {
      content: [{ type: "text", text: `Result: ${result}` }]
    };
  }
);

// Add a tool - retrieve AWS News Blog headline
server.tool(
  "getNewsHeadline",
  { url: z.string().url() },
  async ({ url }) => {
    const response = await fetch(url);
    const html = await response.text();
    const match = html.match(/<title>(.*?)<\/title>/);
    const title = match ? match[1] : "No title found";
    const blogPosts = parseAWSBlogHTML(html);
    return {
      content: [{ type: "text", text: `Headline Title: ${title}
      ${blogPosts.map((post, index) => `
      ${index + 1}. ${post.title}
      (${post.dateText})
      '${post.url}'
      ${post.excerpt}
      `)}` }]
    };
  }
);


// Configure Streamable HTTP transport (sessionless)
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined, // Disable session management
});

// Set up routes
app.post('/mcp', async (req, res) => {
  try {
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req, res) => {
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

app.delete('/mcp', async (req, res) => {
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

// Start the server
const PORT = process.env.PORT || 8080;
server.connect(transport).then(() => {
  app.listen(PORT, () => {
    console.log(`MCP Server listening on port ${PORT}`);
  });
}).catch(error => {
  console.error('Failed to set up the server:', error);
  process.exit(1);
});