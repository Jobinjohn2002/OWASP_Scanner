import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';

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
  health: 'Healthy' | 'Warning' | 'Critical';
  developers: number;
  pushesScanned: number;
  blockedPushes: number;
  lastScanned: string;
}

interface Activity {
  developer: string;
  issue: string;
  commit: string;
  time: string;
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

  /* -------------------------
     PROJECT LIST (Dummy Data)
  ------------------------- */
  projects: Project[] = [
    { id: '1', name: 'Project Phoenix', health: 'Healthy', developers: 24, pushesScanned: 1204, blockedPushes: 15, lastScanned: '2 hours ago' },
    { id: '2', name: 'Project Nova', health: 'Warning', developers: 15, pushesScanned: 873, blockedPushes: 88, lastScanned: '5 hours ago' },
    { id: '3', name: 'Quantum Leap', health: 'Healthy', developers: 31, pushesScanned: 2510, blockedPushes: 21, lastScanned: '1 day ago' },
    { id: '4', name: 'Project Apollo', health: 'Critical', developers: 8, pushesScanned: 432, blockedPushes: 156, lastScanned: '3 days ago' },
    { id: '5', name: 'Data Weaver', health: 'Healthy', developers: 19, pushesScanned: 980, blockedPushes: 11, lastScanned: '1 week ago' }
  ];

  /* -------------------------
      RECENT ACTIVITY TABLE
  ------------------------- */
  recentActivity: Activity[] = [
    { developer: 'Nandha', issue: 'Hardcoded Secret', commit: 'abc1234', time: '10 mins ago' },
    { developer: 'Kavin', issue: 'SQL Injection', commit: 'def5678', time: '35 mins ago' },
    { developer: 'Priya', issue: 'Weak Regex', commit: 'ghi9012', time: '2 hours ago' },
    { developer: 'Meena', issue: 'Unsafe eval()', commit: 'jkl3456', time: '4 hours ago' }
  ];

  /* ---------------------------------
      🔵 BAR CHART (Blocks per Dev)
  ---------------------------------- */

  barSeries: ApexAxisChartSeries = [
    {
      name: "Blocked Issues",
      data: [10, 25, 5, 16, 8, 12] // dummy — replace with backend later
    }
  ];

  barChartOptions: ApexChart = {
    type: "bar",
    height: 300,
    width:800
  };

  barXAxis: ApexXAxis = {
    categories: ["Dev A", "Dev B", "Dev C", "Dev D", "Dev E", "Dev F"]
  };

  /* ---------------------------------
      🔴 PIE CHART (Issue Distribution)
  ---------------------------------- */

  pieSeries: ApexNonAxisChartSeries = [40, 30, 15, 10, 5];

  pieLabels: string[] = [
    "Hardcoded Secrets",
    "SQL Injection",
    "Weak Regex",
    "Unsafe Function",
    "Other"
  ];

  pieChartOptions: ApexChart = {
    type: "pie",
    height: 400,
    width:400
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {

    this.projectId = this.route.snapshot.paramMap.get('id');

    if (this.projectId) {
      this.selectedProject =
        this.projects.find(p => p.id === this.projectId) ?? null;
    }

    if (!this.selectedProject) {
      this.router.navigate([""]);
    }
  }

  getHealthClass(health: string): string {
    return `health-${health.toLowerCase()}`;
  }

  goBackToProjects(): void {
    this.router.navigate([""]);
  }

}
