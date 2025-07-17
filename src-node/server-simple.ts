#!/usr/bin/env node
/**
 * DRMS - Simple Node.js MCP Server for testing
 * Simplified version without ChromaDB for initial testing
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
  TextContent,
  CallToolRequest,
} from '@modelcontextprotocol/sdk/types.js';

class SimpleDRMSServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'drms-node-simple',
        version: '1.2.8',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_documentation',
            description: 'Search documentation for libraries and frameworks (simple demo)',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query for documentation',
                },
                library: {
                  type: 'string',
                  description: 'Specific library/framework to search (optional)',
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'get_library_info',
            description: 'Get information about supported libraries',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
        ] as Tool[],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request: CallToolRequest) => {
      try {
        const { name, arguments: args } = request.params;

        switch (name) {
          case 'search_documentation':
            return this.searchDocumentation(args);
          case 'get_library_info':
            return this.getLibraryInfo(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error handling tool ${request.params.name}:`, error);
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            } as TextContent,
          ],
        };
      }
    });
  }

  private async searchDocumentation(args: any): Promise<{ content: TextContent[] }> {
    const query = args.query;
    const library = args.library;

    // Simulate documentation search
    const mockResults = [
      {
        library: library || 'React',
        title: 'React Hooks Documentation',
        content: `# React Hooks

React Hooks let you use state and other React features without writing a class.

## useState

The useState Hook lets you add React state to function components:

\`\`\`javascript
import React, { useState } from 'react';

function Example() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
}
\`\`\`

This matches your query: "${query}"`,
        url: 'https://react.dev/reference/react/useState',
        similarity: 0.95
      }
    ];

    const formattedResults = mockResults.map((result, i) => {
      return [
        `**Result ${i + 1}** (Similarity: ${result.similarity.toFixed(2)})`,
        `**Library:** ${result.library}`,
        `**URL:** ${result.url}`,
        `**Content:**\n${result.content}`,
        '='.repeat(50),
      ].join('\n');
    });

    const response = `Found ${mockResults.length} documentation results for: '${query}'\n\n${formattedResults.join('\n\n')}`;

    return {
      content: [
        {
          type: 'text',
          text: response,
        } as TextContent,
      ],
    };
  }

  private async getLibraryInfo(args: any): Promise<{ content: TextContent[] }> {
    const supportedLibraries = [
      'React', 'Vue', 'Angular', 'Next.js', 'Express', 'FastAPI', 
      'Django', 'Flask', 'TypeScript', 'Node.js'
    ];

    const response = [
      '**DRMS Node.js - Supported Libraries:**\n',
      ...supportedLibraries.map(lib => `- ${lib}`),
      '\n**Status:** Node.js MCP Server is running successfully! 🎉',
      '**Features:**',
      '- Real-time documentation search',
      '- Code example extraction', 
      '- Multi-language support',
      '- Automatic library discovery'
    ].join('\n');

    return {
      content: [
        {
          type: 'text',
          text: response,
        } as TextContent,
      ],
    };
  }

  public async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.log('DRMS Node.js Simple MCP server running on stdio');
  }
}

async function main(): Promise<void> {
  const drmsServer = new SimpleDRMSServer();

  try {
    console.log('Starting DRMS Node.js Simple MCP server...');
    await drmsServer.run();
  } catch (error) {
    console.error('DRMS server failed:', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('DRMS server stopped by user');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('DRMS server terminated');
  process.exit(0);
});

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}