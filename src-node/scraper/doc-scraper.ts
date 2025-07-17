/**
 * Documentation scraper for automatically discovering and indexing library documentation.
 */

import axios, { AxiosInstance } from 'axios';
import * as cheerio from 'cheerio';
import { createHash } from 'crypto';
import { promises as fs } from 'fs';
import { join } from 'path';
import pLimit from 'p-limit';
import { URL } from 'url';
import { getSettings } from '../config/settings.js';
import { VectorStore, Document } from '../core/vector-store.js';

export interface PageData {
  url: string;
  title: string;
  content: string;
  codeBlocks: string[];
  chunks: ChunkData[];
  library: string;
}

export interface ChunkData {
  content: string;
  url: string;
  library: string;
  chunkId: string;
}

export interface ScrapedData {
  library: string;
  baseUrl: string;
  pages: PageData[];
  scrapedAt: number;
}

export interface ScrapeResult {
  library: string;
  url: string;
  pagesCount: number;
  chunksCount: number;
  lastUpdated: number;
}

export class DocumentationScraper {
  private axiosInstance: AxiosInstance;
  private settings = getSettings();
  private vectorStore?: VectorStore;
  private concurrencyLimit = pLimit(this.settings.maxConcurrentRequests);

  // Common documentation URL patterns
  private readonly docPatterns = [
    'https://{}.readthedocs.io/',
    'https://docs.{}.com/',
    'https://{}.org/docs/',
    'https://{}.org/documentation/',
    'https://github.com/{}/wiki',
    'https://{}.dev/',
    'https://{}.js.org/',
  ];

  // Known documentation sites for popular libraries
  private readonly knownDocs = {
    react: 'https://react.dev/',
    vue: 'https://vuejs.org/guide/',
    angular: 'https://angular.io/docs',
    svelte: 'https://svelte.dev/docs',
    nextjs: 'https://nextjs.org/docs',
    nuxt: 'https://nuxt.com/docs',
    fastapi: 'https://fastapi.tiangolo.com/',
    django: 'https://docs.djangoproject.com/',
    flask: 'https://flask.palletsprojects.com/',
    express: 'https://expressjs.com/',
    nodejs: 'https://nodejs.org/docs/',
    requests: 'https://requests.readthedocs.io/',
    pandas: 'https://pandas.pydata.org/docs/',
    numpy: 'https://numpy.org/doc/',
    scipy: 'https://docs.scipy.org/',
    matplotlib: 'https://matplotlib.org/stable/',
    sklearn: 'https://scikit-learn.org/stable/documentation.html',
    tensorflow: 'https://www.tensorflow.org/api_docs',
    pytorch: 'https://pytorch.org/docs/',
    opencv: 'https://docs.opencv.org/',
    aws: 'https://docs.aws.amazon.com/',
    gcp: 'https://cloud.google.com/docs',
    azure: 'https://docs.microsoft.com/azure/',
    kubernetes: 'https://kubernetes.io/docs/',
    docker: 'https://docs.docker.com/',
    redis: 'https://redis.io/documentation',
    mongodb: 'https://docs.mongodb.com/',
    postgresql: 'https://www.postgresql.org/docs/',
    mysql: 'https://dev.mysql.com/doc/',
    tailwind: 'https://tailwindcss.com/docs',
    bootstrap: 'https://getbootstrap.com/docs/',
    'material-ui': 'https://mui.com/',
    'ant-design': 'https://ant.design/docs/',
    lodash: 'https://lodash.com/docs/',
    axios: 'https://axios-http.com/docs/',
    jest: 'https://jestjs.io/docs/',
    cypress: 'https://docs.cypress.io/',
    webpack: 'https://webpack.js.org/concepts/',
    vite: 'https://vitejs.dev/guide/',
    typescript: 'https://www.typescriptlang.org/docs/',
  };

  constructor(vectorStore?: VectorStore) {
    this.vectorStore = vectorStore;
    this.axiosInstance = axios.create({
      timeout: this.settings.requestTimeout,
      headers: {
        'User-Agent': 'DRMS Documentation Scraper Node.js 1.0'
      }
    });
  }

  private getCachePath(libraryName: string): string {
    const safeName = libraryName.replace(/[^\w\-_.]/g, '_');
    return join(this.settings.cacheDir, `${safeName}_docs.json`);
  }

  private async discoverDocumentationUrl(libraryName: string): Promise<string | null> {
    // Check known documentation sites first
    const lowerName = libraryName.toLowerCase();
    if (this.knownDocs[lowerName as keyof typeof this.knownDocs]) {
      return this.knownDocs[lowerName as keyof typeof this.knownDocs];
    }

    // Try common patterns
    for (const pattern of this.docPatterns) {
      try {
        const url = pattern.replace('{}', lowerName);
        if (await this.checkUrlExists(url)) {
          console.log(`Found documentation at: ${url}`);
          return url;
        }
      } catch {
        continue;
      }
    }

    // Try searching GitHub for the library
    const githubUrl = await this.searchGithubDocs(libraryName);
    if (githubUrl) {
      return githubUrl;
    }

    console.warn(`Could not discover documentation URL for ${libraryName}`);
    return null;
  }

  private async checkUrlExists(url: string): Promise<boolean> {
    try {
      const response = await this.axiosInstance.head(url);
      return response.status === 200;
    } catch {
      return false;
    }
  }

  private async searchGithubDocs(libraryName: string): Promise<string | null> {
    try {
      const githubPatterns = [
        `https://github.com/${libraryName}/${libraryName}`,
        `https://github.com/${libraryName}`,
        `https://${libraryName}.github.io/`,
      ];

      for (const pattern of githubPatterns) {
        if (await this.checkUrlExists(pattern)) {
          return pattern;
        }
      }
    } catch (error) {
      console.debug(`GitHub search failed for ${libraryName}:`, error);
    }

    return null;
  }

  public async scrapeLibrary(
    libraryName: string,
    documentationUrl?: string,
    forceReindex: boolean = false
  ): Promise<ScrapeResult | null> {
    try {
      console.log(`Starting to scrape ${libraryName}`);

      // Check cache first
      const cachePath = this.getCachePath(libraryName);
      if (!forceReindex) {
        try {
          await fs.access(cachePath);
          console.log(`Using cached documentation for ${libraryName}`);
          const cachedData = JSON.parse(await fs.readFile(cachePath, 'utf-8')) as ScrapedData;

          // Add to vector store if not already there
          if (this.vectorStore) {
            await this.addToVectorStore(cachedData, libraryName);
          }

          return {
            library: libraryName,
            url: cachedData.baseUrl,
            pagesCount: cachedData.pages.length,
            chunksCount: cachedData.pages.reduce((sum, page) => sum + page.chunks.length, 0),
            lastUpdated: cachedData.scrapedAt
          };
        } catch {
          // Cache doesn't exist, continue with scraping
        }
      }

      // Discover documentation URL if not provided
      if (!documentationUrl) {
        const discoveredUrl = await this.discoverDocumentationUrl(libraryName);
        if (!discoveredUrl) {
          throw new Error(`Could not find documentation for ${libraryName}`);
        }
        documentationUrl = discoveredUrl;
      }

      // Scrape the documentation
      const scrapedData = await this.scrapeSite(documentationUrl, libraryName);

      if (!scrapedData) {
        throw new Error(`Failed to scrape documentation from ${documentationUrl}`);
      }

      // Cache the results
      await fs.writeFile(cachePath, JSON.stringify(scrapedData, null, 2));

      // Add to vector store
      if (this.vectorStore) {
        await this.addToVectorStore(scrapedData, libraryName);
      }

      console.log(`Successfully scraped ${libraryName}: ${scrapedData.pages.length} pages`);

      return {
        library: libraryName,
        url: documentationUrl,
        pagesCount: scrapedData.pages.length,
        chunksCount: scrapedData.pages.reduce((sum, page) => sum + page.chunks.length, 0),
        lastUpdated: scrapedData.scrapedAt
      };
    } catch (error) {
      console.error(`Error scraping ${libraryName}:`, error);
      return null;
    }
  }

  private async scrapeSite(baseUrl: string, libraryName: string): Promise<ScrapedData | null> {
    const visitedUrls = new Set<string>();
    const pagesData: PageData[] = [];
    const maxPages = this.settings.maxPagesPerLibrary;

    const urlsToVisit = [baseUrl];

    while (urlsToVisit.length > 0 && pagesData.length < maxPages) {
      const currentUrl = urlsToVisit.shift()!;

      if (visitedUrls.has(currentUrl)) {
        continue;
      }

      try {
        const pageData = await this.concurrencyLimit(() => this.scrapePage(currentUrl, libraryName));
        
        if (pageData) {
          pagesData.push(pageData);
          visitedUrls.add(currentUrl);

          // Find additional URLs to scrape
          if (pagesData.length < maxPages) {
            const newUrls = await this.findRelatedUrls(currentUrl, baseUrl);
            for (const url of newUrls) {
              if (!visitedUrls.has(url) && !urlsToVisit.includes(url)) {
                urlsToVisit.push(url);
              }
            }
          }
        }

        // Add delay between requests
        if (this.settings.scrapingDelay > 0) {
          await new Promise(resolve => setTimeout(resolve, this.settings.scrapingDelay * 1000));
        }
      } catch (error) {
        console.warn(`Failed to scrape ${currentUrl}:`, error);
        continue;
      }
    }

    return {
      library: libraryName,
      baseUrl,
      pages: pagesData,
      scrapedAt: Date.now()
    };
  }

  private async scrapePage(url: string, libraryName: string): Promise<PageData | null> {
    try {
      const response = await this.axiosInstance.get(url);
      if (response.status !== 200) {
        return null;
      }

      const $ = cheerio.load(response.data);

      // Extract title
      const titleText = $('title').text().trim() || url;

      // Remove script and style elements
      $('script, style').remove();

      // Extract main content (try common content selectors)
      const contentSelectors = [
        'main', '.content', '.documentation', '.docs',
        '.main-content', '#content', 'article', '.page-content'
      ];

      let contentElement = $('body');
      for (const selector of contentSelectors) {
        const element = $(selector);
        if (element.length > 0) {
          contentElement = element as any;
          break;
        }
      }

      // Extract text content
      const textContent = contentElement.text();
      const cleanContent = this.cleanText(textContent);

      if (cleanContent.trim().length < 100) {
        return null; // Skip pages with minimal content
      }

      // Extract code blocks
      const codeBlocks: string[] = [];
      contentElement.find('code, pre').each((_, element) => {
        const codeText = $(element).text().trim();
        if (codeText.length > 10) {
          codeBlocks.push(codeText);
        }
      });

      // Chunk the content for better searchability
      const chunks = this.chunkContent(cleanContent, url, libraryName);

      return {
        url,
        title: titleText,
        content: cleanContent,
        codeBlocks,
        chunks,
        library: libraryName
      };
    } catch (error) {
      console.warn(`Error scraping page ${url}:`, error);
      return null;
    }
  }

  private cleanText(text: string): string {
    // Remove extra whitespace
    text = text.replace(/\s+/g, ' ');
    // Remove special characters that might interfere
    text = text.replace(/[^\w\s\.\,\!\?\:\;\(\)\-\=\+\*\/\\\[\]\{\}\"\'`]/g, '');
    return text.trim();
  }

  private chunkContent(content: string, url: string, libraryName: string): ChunkData[] {
    // Simple sentence-based chunking
    const sentences = content.split(/[.!?]+/);
    const chunks: ChunkData[] = [];
    let currentChunk = '';
    const maxChunkSize = this.settings.chunkSize;

    for (const sentence of sentences) {
      const trimmedSentence = sentence.trim();
      if (!trimmedSentence) {
        continue;
      }

      if (currentChunk.length + trimmedSentence.length > maxChunkSize) {
        if (currentChunk) {
          chunks.push({
            content: currentChunk.trim(),
            url,
            library: libraryName,
            chunkId: `${libraryName}_${chunks.length}`
          });
        }
        currentChunk = trimmedSentence;
      } else {
        currentChunk += (currentChunk ? ' ' : '') + trimmedSentence;
      }
    }

    // Add the last chunk
    if (currentChunk) {
      chunks.push({
        content: currentChunk.trim(),
        url,
        library: libraryName,
        chunkId: `${libraryName}_${chunks.length}`
      });
    }

    return chunks;
  }

  private async findRelatedUrls(currentUrl: string, baseUrl: string): Promise<string[]> {
    try {
      const response = await this.axiosInstance.get(currentUrl);
      if (response.status !== 200) {
        return [];
      }

      const $ = cheerio.load(response.data);
      const urls: string[] = [];
      const baseDomain = new URL(baseUrl).hostname;

      $('a[href]').each((_, element) => {
        const href = $(element).attr('href');
        if (!href) return;

        let fullUrl: string;
        if (href.startsWith('/')) {
          fullUrl = new URL(href, baseUrl).href;
        } else if (href.startsWith('http')) {
          fullUrl = href;
        } else {
          fullUrl = new URL(href, currentUrl).href;
        }

        // Only include URLs from the same domain and documentation-related paths
        try {
          const urlObj = new URL(fullUrl);
          if (urlObj.hostname === baseDomain && this.isDocumentationUrl(fullUrl)) {
            urls.push(fullUrl);
          }
        } catch {
          // Invalid URL, skip
        }
      });

      return urls.slice(0, 10); // Limit number of URLs per page
    } catch (error) {
      console.debug(`Error finding related URLs for ${currentUrl}:`, error);
      return [];
    }
  }

  private isDocumentationUrl(url: string): boolean {
    const docIndicators = [
      'doc', 'guide', 'tutorial', 'api', 'reference',
      'manual', 'help', 'wiki', 'learn', 'getting-started'
    ];

    const urlLower = url.toLowerCase();
    return docIndicators.some(indicator => urlLower.includes(indicator));
  }

  private async addToVectorStore(scrapedData: ScrapedData, libraryName: string): Promise<void> {
    if (!this.vectorStore) {
      return;
    }

    const documents: Document[] = [];

    for (const page of scrapedData.pages) {
      for (const chunk of page.chunks) {
        const docId = createHash('md5')
          .update(`${libraryName}_${chunk.url}_${chunk.chunkId}`)
          .digest('hex');

        documents.push({
          id: docId,
          content: chunk.content,
          metadata: {
            library: libraryName,
            url: chunk.url,
            title: page.title,
            type: 'documentation'
          }
        });
      }

      // Also add code blocks as examples
      for (let i = 0; i < page.codeBlocks.length; i++) {
        const docId = createHash('md5')
          .update(`${libraryName}_code_${page.url}_${i}`)
          .digest('hex');

        documents.push({
          id: docId,
          content: page.codeBlocks[i],
          metadata: {
            library: libraryName,
            url: page.url,
            title: page.title,
            type: 'code_example'
          }
        });
      }
    }

    // Add documents to appropriate collections
    if (documents.length > 0) {
      const docs = documents.filter(doc => doc.metadata.type === 'documentation');
      const examples = documents.filter(doc => doc.metadata.type === 'code_example');

      if (docs.length > 0) {
        await this.vectorStore.addDocuments(docs, 'documentation');
      }
      if (examples.length > 0) {
        await this.vectorStore.addDocuments(examples, 'code_examples');
      }

      console.log(`Added ${docs.length} docs and ${examples.length} examples to vector store`);
    }
  }
}