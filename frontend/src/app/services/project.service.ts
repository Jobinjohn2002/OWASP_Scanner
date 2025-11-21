import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin, map } from 'rxjs';

@Injectable({
  providedIn: 'root'
})

export class ProjectService {

  private API = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  getProjects() {
    return this.http.get<any>(`${this.API}/projects`).pipe(
      map(res => res.projects || [])
    );
  }

  getDevelopers(project: string) {
    return this.http.get<any>(
      `${this.API}/projects/${encodeURIComponent(project)}/developers`
    );
  }

  getTotalPushes(project: string) {
    return this.http.get<any>(
      `${this.API}/projects/${encodeURIComponent(project)}/total-pushes`
    );
  }

  getBlockedPushes(project: string) {
    return this.http.get<any>(
      `${this.API}/projects/${encodeURIComponent(project)}/blocked-pushes`
    );
  }

  getProjectOverview(project: string) {
    return forkJoin({
      developers: this.getDevelopers(project),
      totalPushes: this.getTotalPushes(project),
      blockedPushes: this.getBlockedPushes(project)
    });
  }

  getBlocksPerDeveloper(project: string) {
    return this.http.get<any>(
      `${this.API}/projects/${encodeURIComponent(project)}/blocks-per-developer`
    );
  }

  getStatusPercentage(project: string) {
    return this.http.get<any>(
      `${this.API}/projects/${encodeURIComponent(project)}/status-percentage`
    );
  }

  getRecentActivities(project: string) {
    return this.http.get<any>(
      `${this.API}/projects/${encodeURIComponent(project)}/recent-activities`
    );
  }

}