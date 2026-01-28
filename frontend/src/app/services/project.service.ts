import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, forkJoin } from 'rxjs';
import { map, tap, shareReplay } from 'rxjs';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

@Injectable({
  providedIn: 'root'
})
export class ProjectService {

  private baseUrl = 'http://49.249.121.94:86';
  // private baseUrl = 'http://localhost:7200'; 
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  
  // In-memory cache
  private cache = new Map<string, CacheEntry<any>>();
  
  // Observable cache for ongoing requests
  private ongoingRequests = new Map<string, Observable<any>>();

  constructor(private http: HttpClient) {}

  /**
   * Check if cache entry is still valid
   */
  private isCacheValid(cacheKey: string): boolean {
    const entry = this.cache.get(cacheKey);
    if (!entry) return false;
    
    const now = Date.now();
    return (now - entry.timestamp) < this.CACHE_DURATION;
  }

  /**
   * Get data from cache
   */
  private getFromCache<T>(cacheKey: string): T | null {
    if (this.isCacheValid(cacheKey)) {
      console.log(`✅ Cache HIT: ${cacheKey}`);
      return this.cache.get(cacheKey)!.data;
    }
    console.log(`❌ Cache MISS: ${cacheKey}`);
    return null;
  }

  /**
   * Save data to cache
   */
  private saveToCache<T>(cacheKey: string, data: T): void {
    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now()
    });
    console.log(`💾 Cached: ${cacheKey}`);
  }

  /**
   * Generic method to handle caching for HTTP requests
   */
  private cachedRequest<T>(cacheKey: string, request: Observable<T>): Observable<T> {
    // Check cache first
    const cachedData = this.getFromCache<T>(cacheKey);
    if (cachedData) {
      return of(cachedData);
    }

    // Check if there's an ongoing request for the same data
    if (this.ongoingRequests.has(cacheKey)) {
      console.log(`🔄 Reusing ongoing request: ${cacheKey}`);
      return this.ongoingRequests.get(cacheKey)!;
    }

    // Create new request with caching
    const sharedRequest = request.pipe(
      tap(data => {
        this.saveToCache(cacheKey, data);
        this.ongoingRequests.delete(cacheKey);
      }),
      shareReplay(1) // Share the result among multiple subscribers
    );

    this.ongoingRequests.set(cacheKey, sharedRequest);
    return sharedRequest;
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    this.cache.clear();
    this.ongoingRequests.clear();
    console.log('🗑️ Cache cleared');
  }

  /**
   * Clear cache for specific project
   */
  clearProjectCache(projectName: string): void {
    const keysToDelete: string[] = [];
    this.cache.forEach((_, key) => {
      if (key.includes(projectName)) {
        keysToDelete.push(key);
      }
    });
    keysToDelete.forEach(key => this.cache.delete(key));
    console.log(`🗑️ Cleared cache for project: ${projectName}`);
  }

  // ============================================
  // PUBLIC baseUrl METHODS (with caching)
  // ============================================

  getProjects(): Observable<string[]> {
    const cacheKey = 'projects';
    return this.cachedRequest(
      cacheKey,
      this.http.get<any>(`${this.baseUrl}/projects`).pipe(
        map(res => res.projects || [])
      )
    );
  }

  getDevelopers(project: string): Observable<any> {
    const cacheKey = `developers-${project}`;
    return this.cachedRequest(
      cacheKey,
      this.http.get<any>(
        `${this.baseUrl}/projects/${encodeURIComponent(project)}/developers`
      )
    );
  }

  getTotalPushes(project: string): Observable<any> {
    const cacheKey = `total-pushes-${project}`;
    return this.cachedRequest(
      cacheKey,
      this.http.get<any>(
        `${this.baseUrl}/projects/${encodeURIComponent(project)}/total-pushes`
      )
    );
  }

  getBlockedPushes(project: string): Observable<any> {
    const cacheKey = `blocked-pushes-${project}`;
    return this.cachedRequest(
      cacheKey,
      this.http.get<any>(
        `${this.baseUrl}/projects/${encodeURIComponent(project)}/blocked-pushes`
      )
    );
  }

  getProjectOverview(project: string): Observable<any> {
    const cacheKey = `overview-${project}`;
    
    // Check if overview is cached
    const cachedData = this.getFromCache<any>(cacheKey);
    if (cachedData) {
      return of(cachedData);
    }

    // If not cached, make the forkJoin request
    return forkJoin({
      developers: this.getDevelopers(project),
      totalPushes: this.getTotalPushes(project),
      blockedPushes: this.getBlockedPushes(project)
    }).pipe(
      tap(data => this.saveToCache(cacheKey, data))
    );
  }

  getBlocksPerDeveloper(project: string): Observable<any> {
    const cacheKey = `blocks-per-dev-${project}`;
    return this.cachedRequest(
      cacheKey,
      this.http.get<any>(
        `${this.baseUrl}/projects/${encodeURIComponent(project)}/blocks-per-developer`
      )
    );
  }

  getStatusPercentage(project: string): Observable<any> {
    const cacheKey = `status-pct-${project}`;
    return this.cachedRequest(
      cacheKey,
      this.http.get<any>(
        `${this.baseUrl}/projects/${encodeURIComponent(project)}/status-percentage`
      )
    );
  }

  getRecentActivities(project: string): Observable<any> {
    // Recent activities have shorter cache duration (1 minute)
    const cacheKey = `recent-activities-${project}`;
    const cachedData = this.cache.get(cacheKey);
    
    if (cachedData && (Date.now() - cachedData.timestamp) < 60000) {
      console.log(`✅ Cache HIT: ${cacheKey}`);
      return of(cachedData.data);
    }

    console.log(`❌ Cache MISS: ${cacheKey}`);
    return this.http.get<any>(
      `${this.baseUrl}/projects/${encodeURIComponent(project)}/recent-activities`
    ).pipe(
      tap(data => {
        this.cache.set(cacheKey, { data, timestamp: Date.now() });
        console.log(`💾 Cached: ${cacheKey}`);
      })
    );
  }

  /**
   * Get cache statistics (useful for debugging)
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }

  getProjectInsights(projectName: string) {
  return this.http.get<any>(
    `${this.baseUrl}/projects/${projectName}/insights`
  );
}

}