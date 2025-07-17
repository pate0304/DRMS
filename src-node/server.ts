#!/usr/bin/env node
/**
 * DRMS - Documentation RAG MCP Server (Node.js/TypeScript)
 * Main MCP server implementation for real-time documentation search and retrieval.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
  TextContent,
  CallToolRequest,
  ListToolsRequest,
} from '@modelcontextprotocol/sdk/types.js';

import { VectorStore } from './core/vector-store.js';
import { DocumentationScraper } from './scraper/doc-scraper.js';
import { getSettings } from './config/settings.js';

class DRMSServer {
  private server: Server;
  private vectorStore: VectorStore | null = null;
  private scraper: DocumentationScraper | null = null;
  private settings = getSettings();

  constructor() {
    this.server = new Server(
      {
        name: 'drms-node',
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
            description: 'Search documentation for libraries and frameworks',
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
                doc_type: {
                  type: 'string',
                  enum: ['documentation', 'api_reference', 'code_examples', 'tutorials'],
                  description: 'Type of documentation to search',
                },
                max_results: {
                  type: 'number',
                  default: 5,
                  description: 'Maximum number of results to return',
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'discover_library',
            description: 'Automatically discover and index a new library\'s documentation',
            inputSchema: {
              type: 'object',
              properties: {
                library_name: {
                  type: 'string',
                  description: 'Name of the library to discover',
                },
                documentation_url: {
                  type: 'string',
                  description: 'Optional: Direct URL to documentation',
                },
                force_reindex: {
                  type: 'boolean',
                  default: false,
                  description: 'Force reindexing even if library exists',
                },
              },
              required: ['library_name'],
            },
          },
          {
            name: 'get_library_info',
            description: 'Get information about indexed libraries',
            inputSchema: {
              type: 'object',
              properties: {
                library: {
                  type: 'string',
                  description: 'Specific library name (optional)',
                },
              },
            },
          },
          {
            name: 'search_code_examples',
            description: 'Search for specific code examples and patterns',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Description of the code example needed',
                },
                language: {
                  type: 'string',
                  description: 'Programming language (optional)',
                },
                library: {
                  type: 'string',
                  description: 'Specific library/framework (optional)',
                },
              },
              required: ['query'],
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
            return await this.searchDocumentation(args);
          case 'discover_library':
            return await this.discoverLibrary(args);
          case 'get_library_info':
            return await this.getLibraryInfo(args);
          case 'search_code_examples':
            return await this.searchCodeExamples(args);
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

  public async initialize(): Promise<void> {
    try {
      console.log('Initializing DRMS Node.js server...');

      // Initialize vector store
      this.vectorStore = new VectorStore();
      await this.vectorStore.initialize();

      // Initialize scraper
      this.scraper = new DocumentationScraper(this.vectorStore);

      // Load pre-populated libraries
      await this.loadPopularLibraries();

      console.log('DRMS Node.js server initialized successfully');
    } catch (error) {
      console.error('Failed to initialize DRMS server:', error);
      throw error;
    }
  }

  private async loadPopularLibraries(): Promise<void> {
    const popularLibraries = [
      { name: 'react', url: 'https://react.dev/' },
      { name: 'vue', url: 'https://vuejs.org/guide/' },
      { name: 'nextjs', url: 'https://nextjs.org/docs' },
      { name: 'fastapi', url: 'https://fastapi.tiangolo.com/' },
      { name: 'express', url: 'https://expressjs.com/' },
      { name: 'django', url: 'https://docs.djangoproject.com/' },
      { name: 'flask', url: 'https://flask.palletsprojects.com/' },
      { name: 'axios', url: 'https://axios-http.com/docs/' },
      { name: 'lodash', url: 'https://lodash.com/docs/' },
      { name: 'typescript', url: 'https://www.typescriptlang.org/docs/' },
    ];

    console.log('Loading popular libraries...');

    for (const library of popularLibraries) {
      try {
        // Check if library already exists
        if (this.vectorStore) {
          const stats = await this.vectorStore.getCollectionStats();
          const libraryExists = Object.values(stats).some(
            stat => 'documentCount' in stat && stat.documentCount > 0
          );

          if (!libraryExists && this.scraper) {
            console.log(`Pre-loading ${library.name}...`);
            await this.scraper.scrapeLibrary(library.name, library.url);
          }
        }
      } catch (error) {
        console.warn(`Failed to pre-load ${library.name}:`, error);
      }
    }

    console.log('Popular libraries loading completed');
  }

  private async searchDocumentation(args: any): Promise<{ content: TextContent[] }> {
    const query = args.query;
    const library = args.library;
    const docType = args.doc_type || 'documentation';
    const maxResults = args.max_results || 5;

    if (!this.vectorStore) {
      throw new Error('Vector store not initialized');
    }

    // Add library filter if specified
    const filterMetadata: Record<string, any> = {};
    if (library) {
      filterMetadata.library = library;
    }

    // Search vector store
    let results = await this.vectorStore.searchDocuments(
      query,
      docType,
      maxResults,
      Object.keys(filterMetadata).length > 0 ? filterMetadata : undefined
    );

    if (results.length === 0 && library && this.scraper) {
      // Try to discover the library if not found
      await this.autoDiscoverLibrary(library);
      // Retry search after discovery
      results = await this.vectorStore.searchDocuments(
        query,
        docType,
        maxResults,
        filterMetadata
      );
    }

    // Format results
    let response: string;
    if (results.length > 0) {
      const formattedResults = results.map((result, i) => {
        const metadata = result.metadata;
        const libName = metadata.library || 'Unknown';
        const url = metadata.url || '';
        const similarity = result.similarity;

        return [
          `**Result ${i + 1}** (Similarity: ${similarity.toFixed(2)})`,
          `**Library:** ${libName}`,
          `**URL:** ${url}`,
          `**Content:**\n${result.content}`,
          '='.repeat(50),
        ].join('\n');
      });

      response = `Found ${results.length} documentation results for: '${query}'\n\n${formattedResults.join('\n\n')}`;
    } else {
      response = `No documentation found for query: '${query}'`;
      if (library) {
        response += ` in library: '${library}'`;
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: response,
        } as TextContent,
      ],
    };
  }

  private async discoverLibrary(args: any): Promise<{ content: TextContent[] }> {
    const libraryName = args.library_name;
    const docUrl = args.documentation_url;
    const forceReindex = args.force_reindex || false;

    if (!this.scraper) {
      throw new Error('Scraper not initialized');
    }

    try {
      const result = await this.scraper.scrapeLibrary(libraryName, docUrl, forceReindex);

      let response: string;
      if (result) {
        response = [
          `Successfully discovered and indexed '${libraryName}' documentation!`,
          `Indexed ${result.pagesCount} pages`,
          `Added ${result.chunksCount} documentation chunks`,
        ].join('\n');
      } else {
        response = `Failed to discover library '${libraryName}'. Please check the library name or provide a documentation URL.`;
      }

      return {
        content: [
          {
            type: 'text',
            text: response,
          } as TextContent,
        ],
      };
    } catch (error) {
      const response = `Error discovering library '${libraryName}': ${error instanceof Error ? error.message : String(error)}`;
      return {
        content: [
          {
            type: 'text',
            text: response,
          } as TextContent,
        ],
      };
    }
  }

  private async getLibraryInfo(args: any): Promise<{ content: TextContent[] }> {
    const library = args.library;

    if (!this.vectorStore) {
      throw new Error('Vector store not initialized');
    }

    const stats = await this.vectorStore.getCollectionStats();

    let response: string;
    if (library) {
      // Search for specific library info
      const results = await this.vectorStore.searchDocuments(
        `${library} documentation`,
        'documentation',
        1,
        { library }
      );

      if (results.length > 0) {
        const metadata = results[0].metadata;
        response = [
          `**Library:** ${library}`,
          `**Description:** ${metadata.description || 'N/A'}`,
          `**Version:** ${metadata.version || 'N/A'}`,
          `**URL:** ${metadata.url || 'N/A'}`,
          `**Last Updated:** ${metadata.last_updated || 'N/A'}`,
        ].join('\n');
      } else {
        response = `Library '${library}' not found in index.`;
      }
    } else {
      // Return general statistics
      const statLines = ['**DRMS Library Statistics:**\n'];
      for (const [collectionName, collectionStats] of Object.entries(stats)) {
        if ('documentCount' in collectionStats) {
          statLines.push(`**${collectionName.charAt(0).toUpperCase() + collectionName.slice(1)}:** ${collectionStats.documentCount} documents`);
        }
      }
      response = statLines.join('\n');
    }

    return {
      content: [
        {
          type: 'text',
          text: response,
        } as TextContent,
      ],
    };
  }

  private async searchCodeExamples(args: any): Promise<{ content: TextContent[] }> {
    const query = args.query;
    const language = args.language;
    const library = args.library;

    if (!this.vectorStore) {
      throw new Error('Vector store not initialized');
    }

    // Build enhanced query for code examples
    let enhancedQuery = `code example ${query}`;
    if (language) {
      enhancedQuery += ` ${language}`;
    }
    if (library) {
      enhancedQuery += ` ${library}`;
    }

    // Search in examples collection
    const filterMetadata: Record<string, any> = {};
    if (library) {
      filterMetadata.library = library;
    }
    if (language) {
      filterMetadata.language = language;
    }

    let results = await this.vectorStore.searchDocuments(
      enhancedQuery,
      'code_examples',
      3,
      Object.keys(filterMetadata).length > 0 ? filterMetadata : undefined
    );

    // Also search in general docs for code patterns if no examples found
    if (results.length === 0) {
      results = await this.vectorStore.searchDocuments(
        enhancedQuery,
        'documentation',
        3,
        Object.keys(filterMetadata).length > 0 ? filterMetadata : undefined
      );
    }

    let response: string;
    if (results.length > 0) {
      const formattedResults = results.map((result, i) => {
        const metadata = result.metadata;
        const libName = metadata.library || 'Unknown';
        const lang = metadata.language || '';

        return [
          `**Example ${i + 1}**`,
          `**Library:** ${libName}`,
          `**Language:** ${lang}`,
          `**Code:**\n\`\`\`${lang.toLowerCase()}\n${result.content}\n\`\`\``,
          '='.repeat(40),
        ].join('\n');
      });

      response = `Found ${results.length} code examples for: '${query}'\n\n${formattedResults.join('\n\n')}`;
    } else {
      response = `No code examples found for: '${query}'`;
    }

    return {
      content: [
        {
          type: 'text',
          text: response,
        } as TextContent,
      ],
    };
  }

  private async autoDiscoverLibrary(libraryName: string): Promise<void> {
    if (!this.scraper) {
      return;
    }

    try {
      console.log(`Auto-discovering library: ${libraryName}`);
      await this.scraper.scrapeLibrary(libraryName);
    } catch (error) {
      console.warn(`Auto-discovery failed for ${libraryName}:`, error);
    }
  }

  public async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.log('DRMS Node.js MCP server running on stdio');
  }
}

async function main(): Promise<void> {
  const drmsServer = new DRMSServer();

  try {
    // Initialize server
    await drmsServer.initialize();

    // Run server
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