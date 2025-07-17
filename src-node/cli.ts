#!/usr/bin/env node
/**
 * DRMS CLI - Command line interface for the Node.js implementation
 */

import { Command } from 'commander';
import { VectorStore } from './core/vector-store.js';
import { DocumentationScraper } from './scraper/doc-scraper.js';
import { getSettings, getSettingsManager } from './config/settings.js';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { join } from 'path';

const program = new Command();

program
  .name('drms-node')
  .description('DRMS - Documentation RAG MCP Server (Node.js)')
  .version('1.2.8');

// Start MCP server
program
  .command('start')
  .description('Start the MCP server')
  .action(async () => {
    console.log('Starting DRMS Node.js MCP server...');
    try {
      // Import and run the server
      const { spawn } = await import('child_process');
      const serverProcess = spawn('node', [join(__dirname, 'server.js')], {
        stdio: 'inherit'
      });

      serverProcess.on('error', (error) => {
        console.error('Failed to start server:', error);
        process.exit(1);
      });

      serverProcess.on('exit', (code) => {
        console.log(`Server exited with code ${code}`);
        process.exit(code || 0);
      });
    } catch (error) {
      console.error('Error starting server:', error);
      process.exit(1);
    }
  });

// Search documentation from CLI
program
  .command('search')
  .description('Search documentation from command line')
  .argument('<query>', 'Search query')
  .option('-l, --library <library>', 'Specific library to search')
  .option('-t, --type <type>', 'Documentation type (docs, api, examples, tutorials)', 'docs')
  .option('-n, --max-results <number>', 'Maximum results to return', '5')
  .action(async (query: string, options) => {
    try {
      console.log(`Searching for: ${query}`);
      
      const vectorStore = new VectorStore();
      await vectorStore.initialize();

      const results = await vectorStore.searchDocuments(
        query,
        options.type,
        parseInt(options.maxResults),
        options.library ? { library: options.library } : undefined
      );

      if (results.length > 0) {
        console.log(`\nFound ${results.length} results:\n`);
        results.forEach((result, i) => {
          console.log(`${i + 1}. ${result.metadata.library || 'Unknown'}`);
          console.log(`   Similarity: ${result.similarity.toFixed(2)}`);
          console.log(`   URL: ${result.metadata.url || 'N/A'}`);
          console.log(`   Content: ${result.content.substring(0, 200)}...`);
          console.log('');
        });
      } else {
        console.log('No results found.');
      }

      await vectorStore.close();
    } catch (error) {
      console.error('Search failed:', error);
      process.exit(1);
    }
  });

// Discover and index a library
program
  .command('discover')
  .description('Discover and index a library\'s documentation')
  .argument('<library>', 'Library name to discover')
  .option('-u, --url <url>', 'Direct documentation URL')
  .option('-f, --force', 'Force reindexing', false)
  .action(async (library: string, options) => {
    try {
      console.log(`Discovering library: ${library}`);

      const vectorStore = new VectorStore();
      await vectorStore.initialize();

      const scraper = new DocumentationScraper(vectorStore);
      const result = await scraper.scrapeLibrary(library, options.url, options.force);

      if (result) {
        console.log('Success!');
        console.log(`- Pages indexed: ${result.pagesCount}`);
        console.log(`- Content chunks: ${result.chunksCount}`);
        console.log(`- Documentation URL: ${result.url}`);
      } else {
        console.log('Failed to discover library documentation.');
      }

      await vectorStore.close();
    } catch (error) {
      console.error('Discovery failed:', error);
      process.exit(1);
    }
  });

// Show library information
program
  .command('info')
  .description('Show information about indexed libraries')
  .option('-l, --library <library>', 'Specific library to show info for')
  .action(async (options) => {
    try {
      const vectorStore = new VectorStore();
      await vectorStore.initialize();

      if (options.library) {
        // Show specific library info
        const results = await vectorStore.searchDocuments(
          `${options.library} documentation`,
          'documentation',
          1,
          { library: options.library }
        );

        if (results.length > 0) {
          const metadata = results[0].metadata;
          console.log(`Library: ${options.library}`);
          console.log(`URL: ${metadata.url || 'N/A'}`);
          console.log(`Title: ${metadata.title || 'N/A'}`);
          console.log(`Type: ${metadata.type || 'N/A'}`);
        } else {
          console.log(`Library '${options.library}' not found in index.`);
        }
      } else {
        // Show general statistics
        const stats = await vectorStore.getCollectionStats();
        console.log('DRMS Library Statistics:\n');
        
        for (const [collectionName, collectionStats] of Object.entries(stats)) {
          if ('documentCount' in collectionStats) {
            console.log(`${collectionName}: ${collectionStats.documentCount} documents`);
          } else {
            console.log(`${collectionName}: Error - ${collectionStats.error}`);
          }
        }
      }

      await vectorStore.close();
    } catch (error) {
      console.error('Info command failed:', error);
      process.exit(1);
    }
  });

// Configuration command
program
  .command('config')
  .description('Show or update configuration')
  .option('--show', 'Show current configuration')
  .option('--set <key=value>', 'Set configuration value')
  .action(async (options) => {
    try {
      const settingsManager = getSettingsManager();

      if (options.show) {
        console.log('Current DRMS Configuration:');
        console.log(JSON.stringify(settingsManager.toJSON(), null, 2));
      } else if (options.set) {
        const [key, value] = options.set.split('=');
        if (!key || value === undefined) {
          console.error('Invalid format. Use --set key=value');
          process.exit(1);
        }

        // Parse value based on type
        let parsedValue: any = value;
        if (value === 'true') parsedValue = true;
        else if (value === 'false') parsedValue = false;
        else if (!isNaN(Number(value))) parsedValue = Number(value);

        settingsManager.updateSettings({ [key]: parsedValue });
        console.log(`Updated ${key} = ${parsedValue}`);
      } else {
        console.log('Use --show to display configuration or --set key=value to update settings');
      }
    } catch (error) {
      console.error('Config command failed:', error);
      process.exit(1);
    }
  });

// Health check
program
  .command('doctor')
  .description('Run health check and diagnostics')
  .action(async () => {
    console.log('Running DRMS health check...\n');

    try {
      // Check settings
      const settings = getSettings();
      console.log('✅ Configuration loaded successfully');

      // Check vector store
      const vectorStore = new VectorStore();
      await vectorStore.initialize();
      console.log('✅ Vector store connection successful');

      const stats = await vectorStore.getCollectionStats();
      console.log(`✅ Found ${Object.keys(stats).length} collections`);

      // Check if any libraries are indexed
      const totalDocs = Object.values(stats).reduce((sum, stat) => {
        return sum + ('documentCount' in stat ? stat.documentCount : 0);
      }, 0);

      if (totalDocs > 0) {
        console.log(`✅ ${totalDocs} documents indexed`);
      } else {
        console.log('⚠️  No documents indexed yet');
      }

      // Check OpenAI configuration if enabled
      if (settings.useOpenaiEmbeddings) {
        if (settings.openaiApiKey) {
          console.log('✅ OpenAI embeddings configured');
        } else {
          console.log('❌ OpenAI embeddings enabled but no API key found');
        }
      } else {
        console.log('✅ Using local embeddings');
      }

      await vectorStore.close();
      console.log('\n🎉 Health check completed successfully!');

    } catch (error) {
      console.error('❌ Health check failed:', error);
      process.exit(1);
    }
  });

// Generate IDE configuration
program
  .command('generate-config')
  .description('Generate MCP configuration for IDEs')
  .option('--ide <ide>', 'IDE type (windsurf, cursor, claude)', 'windsurf')
  .action(async (options) => {
    try {
      const currentDir = process.cwd();
      const serverPath = join(currentDir, 'dist', 'server.js');

      let config: any;

      switch (options.ide.toLowerCase()) {
        case 'windsurf':
          config = {
            mcpServers: {
              'drms-node': {
                command: 'node',
                args: [serverPath],
                cwd: currentDir,
                env: {
                  NODE_ENV: 'production'
                }
              }
            }
          };
          break;

        case 'cursor':
          config = {
            mcpServers: {
              'drms-node': {
                command: 'node',
                args: [serverPath]
              }
            }
          };
          break;

        case 'claude':
          config = {
            mcpServers: {
              'drms-node': {
                command: 'node',
                args: [serverPath]
              }
            }
          };
          break;

        default:
          console.error('Unsupported IDE. Use: windsurf, cursor, or claude');
          process.exit(1);
      }

      console.log(`Configuration for ${options.ide}:`);
      console.log(JSON.stringify(config, null, 2));

      // Save to file
      const configFile = `drms-${options.ide}-config.json`;
      await fs.writeFile(configFile, JSON.stringify(config, null, 2));
      console.log(`\nConfiguration saved to: ${configFile}`);

    } catch (error) {
      console.error('Config generation failed:', error);
      process.exit(1);
    }
  });

program.parse();