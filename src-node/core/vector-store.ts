/**
 * Vector Store implementation using ChromaDB for document embeddings and search.
 */

import { ChromaClient, OpenAIEmbeddingFunction } from 'chromadb';
import { OpenAI } from 'openai';
import { pipeline, env } from '@xenova/transformers';
import { getSettings } from '../config/settings.js';

// Configure transformers to use local models
env.allowLocalModels = true;
env.allowRemoteModels = true;

export interface Document {
  id: string;
  content: string;
  metadata: Record<string, any>;
}

export interface SearchResult {
  content: string;
  metadata: Record<string, any>;
  similarity: number;
  id: string;
}

export interface CollectionStats {
  documentCount: number;
  collectionName: string;
}

export class VectorStore {
  private client!: ChromaClient;
  private collections: Record<string, any> = {};
  private embeddingFunction: any;
  private transformerPipeline: any;
  private settings = getSettings();

  constructor() {
    this.initializeClient();
    this.initializeEmbeddingFunction();
  }

  private initializeClient(): void {
    this.client = new ChromaClient({
      path: this.settings.vectorDbPath
    });
  }

  private async initializeEmbeddingFunction(): Promise<void> {
    if (this.settings.useOpenaiEmbeddings && this.settings.openaiApiKey) {
      // Use OpenAI embeddings
      this.embeddingFunction = new OpenAIEmbeddingFunction({
        openai_api_key: this.settings.openaiApiKey,
        openai_model: 'text-embedding-ada-002'
      });
    } else {
      // Use default embedding function (no need for DefaultEmbeddingFunction import)
      this.embeddingFunction = undefined;
      // Initialize the transformer pipeline for local embeddings
      try {
        this.transformerPipeline = await pipeline('feature-extraction', this.settings.embeddingModel);
      } catch (error) {
        console.warn('Failed to load local embedding model, falling back to default:', error);
      }
    }
  }

  public async initialize(): Promise<void> {
    try {
      // Create collections for different types of documentation
      const collectionNames = ['documentation', 'api_reference', 'code_examples', 'tutorials'];
      
      for (const name of collectionNames) {
        try {
          this.collections[name] = await this.client.getCollection({
            name,
            embeddingFunction: this.embeddingFunction
          });
        } catch {
          // Collection doesn't exist, create it
          this.collections[name] = await this.client.createCollection({
            name,
            embeddingFunction: this.embeddingFunction,
            metadata: { 'hnsw:space': 'cosine' }
          });
        }
      }

      console.log(`VectorStore initialized with ${Object.keys(this.collections).length} collections`);
    } catch (error) {
      console.error('Failed to initialize VectorStore:', error);
      throw error;
    }
  }

  private async generateEmbeddings(texts: string[]): Promise<number[][]> {
    if (this.settings.useOpenaiEmbeddings && this.settings.openaiApiKey) {
      // OpenAI embeddings are handled by the embedding function
      return [];
    } else if (this.transformerPipeline) {
      // Use local transformer pipeline
      const embeddings = await Promise.all(
        texts.map(async (text) => {
          const result = await this.transformerPipeline(text, { pooling: 'mean', normalize: true });
          return Array.from(result.data as Float32Array);
        })
      );
      return embeddings;
    } else {
      // Fallback to default embedding function
      return [];
    }
  }

  public async addDocuments(
    documents: Document[],
    collectionType: string = 'documentation'
  ): Promise<boolean> {
    try {
      const collection = this.collections[collectionType];
      if (!collection) {
        console.error(`Unknown collection type: ${collectionType}`);
        return false;
      }

      const texts = documents.map(doc => doc.content);
      const ids = documents.map(doc => doc.id);
      const metadatas = documents.map(doc => doc.metadata);

      // Generate embeddings if using local model
      let embeddings: number[][] | undefined;
      if (!this.settings.useOpenaiEmbeddings) {
        embeddings = await this.generateEmbeddings(texts);
      }

      await collection.add({
        ids,
        documents: texts,
        metadatas,
        embeddings: embeddings?.length ? embeddings : undefined
      });

      console.log(`Added ${documents.length} documents to ${collectionType} collection`);
      return true;
    } catch (error) {
      console.error('Error adding documents:', error);
      return false;
    }
  }

  public async searchDocuments(
    query: string,
    collectionType: string = 'documentation',
    nResults: number = 5,
    filterMetadata?: Record<string, any>
  ): Promise<SearchResult[]> {
    try {
      const collection = this.collections[collectionType];
      if (!collection) {
        console.error(`Unknown collection type: ${collectionType}`);
        return [];
      }

      // Generate query embedding if using local model
      let queryEmbedding: number[] | undefined;
      if (!this.settings.useOpenaiEmbeddings && this.transformerPipeline) {
        const result = await this.transformerPipeline(query, { pooling: 'mean', normalize: true });
        queryEmbedding = Array.from(result.data);
      }

      const results = await collection.query({
        queryTexts: queryEmbedding ? undefined : [query],
        queryEmbeddings: queryEmbedding ? [queryEmbedding] : undefined,
        nResults,
        where: filterMetadata,
        include: ['documents', 'metadatas', 'distances']
      });

      // Format results
      const formattedResults: SearchResult[] = [];
      if (results.documents && results.documents[0]) {
        for (let i = 0; i < results.documents[0].length; i++) {
          formattedResults.push({
            content: results.documents[0][i] || '',
            metadata: results.metadatas?.[0]?.[i] || {},
            similarity: 1 - (results.distances?.[0]?.[i] || 0), // Convert distance to similarity
            id: results.ids?.[0]?.[i] || `result_${i}`
          });
        }
      }

      console.log(`Found ${formattedResults.length} results for query: ${query.substring(0, 50)}...`);
      return formattedResults;
    } catch (error) {
      console.error('Error searching documents:', error);
      return [];
    }
  }

  public async searchMultiCollection(
    query: string,
    nResults: number = 3
  ): Promise<Record<string, SearchResult[]>> {
    const results: Record<string, SearchResult[]> = {};

    for (const collectionName of Object.keys(this.collections)) {
      results[collectionName] = await this.searchDocuments(
        query,
        collectionName,
        nResults
      );
    }

    return results;
  }

  public async getCollectionStats(): Promise<Record<string, CollectionStats | { error: string }>> {
    const stats: Record<string, CollectionStats | { error: string }> = {};

    for (const [name, collection] of Object.entries(this.collections)) {
      try {
        const count = await collection.count();
        stats[name] = {
          documentCount: count,
          collectionName: name
        };
      } catch (error) {
        stats[name] = { error: String(error) };
      }
    }

    return stats;
  }

  public async deleteDocuments(
    docIds: string[],
    collectionType: string = 'documentation'
  ): Promise<boolean> {
    try {
      const collection = this.collections[collectionType];
      if (!collection) {
        return false;
      }

      await collection.delete({
        ids: docIds
      });

      console.log(`Deleted ${docIds.length} documents from ${collectionType}`);
      return true;
    } catch (error) {
      console.error('Error deleting documents:', error);
      return false;
    }
  }

  public async updateDocument(
    docId: string,
    content: string,
    metadata: Record<string, any>,
    collectionType: string = 'documentation'
  ): Promise<boolean> {
    try {
      // Delete old version
      await this.deleteDocuments([docId], collectionType);

      // Add new version
      return await this.addDocuments([{
        id: docId,
        content,
        metadata
      }], collectionType);
    } catch (error) {
      console.error(`Error updating document ${docId}:`, error);
      return false;
    }
  }

  public getCollectionNames(): string[] {
    return Object.keys(this.collections);
  }

  public async close(): Promise<void> {
    // ChromaDB doesn't require explicit closing in the current API
    console.log('VectorStore closed');
  }
}