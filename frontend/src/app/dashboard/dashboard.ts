import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';




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
  styleUrls: ['./dashboard.scss']
})
export class DashBoardComponent implements OnInit {
    constructor(private router: Router) {}


  // Dummy data for now; later you'll replace this with backend call
  projects: Project[] = [
    {
      id: '1',
      name: 'Project Phoenix',
      developers: 24,
      pushesScanned: 1204,
      blockedPushes: 15,
    },
    {
      id: '2',
      name: 'Project Nova',
      developers: 15,
      pushesScanned: 873,
      blockedPushes: 88,
    },
    {
      id: '3',
      name: 'Quantum Leap',
      developers: 31,
      pushesScanned: 2510,
      blockedPushes: 21,
    },
    {
      id: '4',
      name: 'Project Apollo',
      developers: 8,
      pushesScanned: 432,
      blockedPushes: 156,
    },
    {
      id: '5',
      name: 'Data Weaver',
      developers: 19,
      pushesScanned: 980,
      blockedPushes: 11,
    }
  ];

  viewMode: 'card' | 'list' = 'list';
  searchQuery = '';

  currentPage = 1;
  resultsPerPage = 5;

  ngOnInit(): void {
    // Later: call backend here to load real projects
  }

  // All projects filtered by search text
  get filteredProjects(): Project[] {
    if (!this.searchQuery.trim()) {
      return this.projects;
    }
    const query = this.searchQuery.toLowerCase();
    return this.projects.filter(p =>
      p.name.toLowerCase().includes(query)
    );
  }

  // Total results AFTER filtering
  get totalResults(): number {
    return this.filteredProjects.length;
  }

  // Total pages based on filtered results
  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalResults / this.resultsPerPage));
  }

  // Current page slice
  get paginatedProjects(): Project[] {
    const start = (this.currentPage - 1) * this.resultsPerPage;
    const end = start + this.resultsPerPage;
    return this.filteredProjects.slice(start, end);
  }

  // For displaying "Showing X to Y of Z"
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

  setViewMode(mode: 'card' | 'list'): void {
    this.viewMode = mode;
  }

  onSearchChange(): void {
    // Whenever search changes, reset to first page
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
