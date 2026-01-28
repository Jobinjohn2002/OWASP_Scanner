import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ProjectService } from '../services/project.service';
import { map, forkJoin } from 'rxjs';

interface Project {
  id: string;
  name: string;
  developers: number;
  pushesScanned: number;
  blockedPushes: number;
}

@Component({
  selector: 'app-projects-overview',
  imports:[CommonModule,FormsModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss'],
  standalone: true
})
export class DashBoardComponent implements OnInit {
  projects: Project[] = [];
  viewMode: 'list' = 'list';
  searchQuery = '';
  currentPage = 1;
  resultsPerPage = 10; // Changed from 5 to 10
  
  // Loading state
  isLoading = true;
  loadingError: string | null = null;

  constructor(private router: Router, private projectService: ProjectService) {
    console.log("Dashboard component loaded!");
  }

  ngOnInit(): void {
    this.loadProjects();
  }

  loadProjects() {
    console.log("Loading projects...");
    this.isLoading = true;
    this.loadingError = null;

    this.projectService.getProjects().subscribe({
      next: (projectNames: string[]) => {
        console.log("Projects received from backend:", projectNames);

        if (!projectNames || projectNames.length === 0) {
          console.warn("Backend returned EMPTY project list.");
          this.isLoading = false;
          return;
        }

        const calls = projectNames.map((name: string) =>
          this.projectService.getProjectOverview(name).pipe(
            map(data => ({
              id: name,
              name,
              developers: data.developers?.developer_count ?? 0,
              pushesScanned: data.totalPushes?.total_pushes ?? 0,
              blockedPushes: data.blockedPushes?.blocked_pushes ?? 0
            } as Project))
          )
        );

        forkJoin(calls).subscribe({
          next: (finalProjects: Project[]) => {
            console.log("FINAL PROJECT LIST:", finalProjects);
            this.projects = finalProjects;
            this.isLoading = false;
          },
          error: (err) => {
            console.error("ERROR INSIDE forkJoin:", err);
            this.loadingError = "Failed to load project details";
            this.isLoading = false;
          }
        });
      },
      error: (err) => {
        console.error("ERROR GETTING PROJECT NAMES:", err);
        this.loadingError = "Failed to load projects";
        this.isLoading = false;
      }
    });
  }

  get filteredProjects(): Project[] {
    if (!this.searchQuery.trim()) {
      return this.projects;
    }
    const query = this.searchQuery.toLowerCase();
    return this.projects.filter(p =>
      p.name.toLowerCase().includes(query)
    );
  }

  get totalResults(): number {
    return this.filteredProjects.length;
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalResults / this.resultsPerPage));
  }

  get paginatedProjects(): Project[] {
    const start = (this.currentPage - 1) * this.resultsPerPage;
    const end = start + this.resultsPerPage;
    return this.filteredProjects.slice(start, end);
  }

  get startIndex(): number {
    if (this.totalResults === 0) {
      return 0;
    }
    return (this.currentPage - 1) * this.resultsPerPage;
  }

  get endIndex(): number {
    if (this.totalResults === 0) {
      return 0;
    }
    return Math.min(this.startIndex + this.resultsPerPage, this.totalResults);
  }

  // Create skeleton array for loading state
  get skeletonRows(): number[] {
    return Array(this.resultsPerPage).fill(0);
  }

  setViewMode(mode: 'list'): void {
    this.viewMode = mode;
  }

  onSearchChange(): void {
    this.currentPage = 1;
  }

  viewDetails(project: Project) {
    this.router.navigate(['project-details', project.id]);
  }

  addNewProject(): void {
    console.log('Add new project');
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  }
}