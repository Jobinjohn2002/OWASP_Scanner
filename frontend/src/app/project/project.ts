import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ProjectService } from '../services/project.service';

import {
  NgApexchartsModule,
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexNonAxisChartSeries
} from "ng-apexcharts";

interface Project {
  id: string;
  name: string;
  developers: number;
  pushesScanned: number;
  blockedPushes: number;
  lastScanned: string;
}

interface Activity {
  user_name: string;
  status: string;
  timestamp: string;
}

@Component({
  selector: 'app-project-details',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule],
  templateUrl: './project.html',
  styleUrls: ['./project.scss']
})
export class ProjectDetailsComponent implements OnInit {

  projectId: string | null = null;
  selectedProject: Project | null = null;

  barSeries: ApexAxisChartSeries = [{ name: "Blocked Issues", data: [] }];
  barXAxis: ApexXAxis = { categories: [] };

  barChartOptions: ApexChart = {
  type: "bar",
  height: 300,
  width: 700
};

  pieSeries: number[] = [];
  pieLabels: string[] = [];

  pieChartOptions: ApexChart = {
  type: "donut",
  height:700,
  width: 550
};

  recentActivity: Activity[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private projectService: ProjectService
  ) {}

  ngOnInit(): void {
    const rawId = this.route.snapshot.paramMap.get('id');
  this.projectId = rawId?decodeURIComponent(rawId) : null;

  console.log("RAW ROUTE ID =", rawId);
    console.log("DECODED PROJECT ID =", this.projectId);

  if (!this.projectId) {
    this.router.navigate([""]);
    return;
  }

  this.loadProjectDetails(this.projectId);
}

loadProjectDetails(projectName: string) {
  this.projectService.getProjectOverview(projectName).subscribe({
    next: (data) => {
      this.selectedProject = {
        id: projectName,
        name: projectName,
        developers: data.developers?.developer_count ?? 0,
        pushesScanned: data.totalPushes?.total_pushes ?? 0,
        blockedPushes: data.blockedPushes?.blocked_pushes ?? 0,
        lastScanned: 'Just now'
      };
    },
    error: (err) => {
      console.error("Error loading project details:", err);
      this.router.navigate([""]);
    }
  });

  this.projectService.getBlocksPerDeveloper(projectName).subscribe({
      next: (res) => {
        const rows = res.blocks_per_developer || [];
        this.barXAxis.categories = rows.map((r: any) => r.user_name);
        this.barSeries = [{ name: "Blocked Issues", data: rows.map((r: any) => r.blocked_count) }];
      },
      error: (err) => {
        console.warn("Blocks per developer failed:", err);
        this.barXAxis = { categories: [] };
        this.barSeries = [{ name: "Blocked Issues", data: [] }];
      }
    });

    this.projectService.getStatusPercentage(projectName).subscribe({
      next: (res) => {
        const pct = res.status_percentage || {};
        this.pieLabels = Object.keys(pct);
        this.pieSeries = Object.values(pct).map(v => Number(v));;
      },
      error: (err) => {
        console.warn("Status percentage failed:", err);
        this.pieLabels = [];
        this.pieSeries = [];
      }
    });

    this.projectService.getRecentActivities(projectName).subscribe({
      next: (res) => {
        this.recentActivity = res.recent_activities || [];
      },
      error: (err) => {
        console.warn("Recent activities failed:", err);
        this.recentActivity = [];
      }
    });
}

  goBackToProjects(): void {
    this.router.navigate([""]);
  }

}
