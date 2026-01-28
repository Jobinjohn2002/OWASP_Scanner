import { Component, OnInit } from '@angular/core';
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

interface Insights {
  overview: any;
  security_metrics: any;
  trend_analysis: any;
  team_analytics: any;
  vulnerability_breakdown: any;
  temporal_patterns: any;
  user_activity_analysis: any[];  // Changed from branch_analysis
  risk_assessment: any;
  recommendations: any[];
  alerts: any[];
  quick_stats: any;
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

  // Loading states
  isLoading = true;
  isLoadingCharts = true;
  loadingError: string | null = null;

  // Tabs
  activeTab: 'overview' | 'insights' = 'overview';

  // Insights
  insights: Insights | null = null;
  isLoadingInsights = false;

  // Chart data
  barSeries: ApexAxisChartSeries = [{ name: "Blocked Issues", data: [] }];
  barXAxis: ApexXAxis = { categories: [] };

  barChartOptions: ApexChart = {
    type: "bar",
    height: 300,
    width: '100%',
    foreColor: '#f1f5f9',
    toolbar: { show: false }
  };

  barTooltip = {
    theme: 'dark',
    style: {
      fontSize: '14px',
      background: '#1e293b'
    }
  };

  pieSeries: number[] = [];
  pieLabels: string[] = [];

  pieLegend: ApexLegend = {
    show: true,
    position: "right",
    horizontalAlign: "center",
    fontSize: "11px",
    labels: { colors: "#f1f5f9" },
    itemMargin: {
      horizontal: 5,
      vertical: 4
    },
    formatter: (name: string) => {
      return name.length > 30 ? name.substring(0, 30) + "..." : name;
    }
  };

  pieChartOptions: ApexChart = {
    type: "donut",
    height: 300,
    width: "100%",
    foreColor: "#f1f5f9",
    toolbar: { show: false },
    offsetX: 0,
  };

  piePlot: any = {
    pie: {
      donut: {
        size: "70%",
      }
    }
  };

  recentActivity: Activity[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private projectService: ProjectService
  ) { }

  ngOnInit(): void {
    const rawId = this.route.snapshot.paramMap.get('id');
    this.projectId = rawId ? decodeURIComponent(rawId) : null;

    console.log("RAW ROUTE ID =", rawId);
    console.log("DECODED PROJECT ID =", this.projectId);

    if (!this.projectId) {
      this.router.navigate([""]);
      return;
    }

    this.loadProjectDetails(this.projectId);
  }

  switchTab(tab: 'overview' | 'insights') {
    this.activeTab = tab;

    if (tab === 'insights' && !this.insights) {
      this.loadInsights();
    }
  }

  loadInsights() {
    if (!this.projectId) return;

    this.isLoadingInsights = true;

    this.projectService.getProjectInsights(this.projectId).subscribe({
      next: (data: Insights) => {
        this.insights = data;
        this.isLoadingInsights = false;
        console.log("Insights loaded:", data);
      },
      error: (err: any) => {
        console.error("Failed to load insights", err);
        this.isLoadingInsights = false;
      }
    });
  }

  loadProjectDetails(projectName: string) {
    this.isLoading = true;
    this.isLoadingCharts = true;
    this.loadingError = null;

    // Load basic project info first
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
        this.isLoading = false;

        // Load charts data after basic info is shown
        this.loadChartsData(projectName);
      },
      error: (err) => {
        console.error("Error loading project details:", err);
        this.loadingError = "Failed to load project details";
        this.isLoading = false;
        this.isLoadingCharts = false;
      }
    });
  }

  loadChartsData(projectName: string) {
    let chartsLoaded = 0;
    const totalCharts = 3;

    const checkAllLoaded = () => {
      chartsLoaded++;
      if (chartsLoaded >= totalCharts) {
        this.isLoadingCharts = false;
      }
    };

    // Load blocks per developer
    this.projectService.getBlocksPerDeveloper(projectName).subscribe({
      next: (res) => {
        const rows = res.blocks_per_developer || [];
        this.barXAxis = { categories: rows.map((r: any) => r.user_name) };
        this.barSeries = [{ name: "Blocked Issues", data: rows.map((r: any) => r.blocked_count) }];
        checkAllLoaded();
      },
      error: (err) => {
        console.warn("Blocks per developer failed:", err);
        this.barXAxis = { categories: [] };
        this.barSeries = [{ name: "Blocked Issues", data: [] }];
        checkAllLoaded();
      }
    });

    // Load status percentage
    this.projectService.getStatusPercentage(projectName).subscribe({
      next: (res) => {
        const pct = res.status_percentage || {};
        this.pieLabels = Object.keys(pct);
        this.pieSeries = Object.values(pct).map(v => Number(v));
        checkAllLoaded();
      },
      error: (err) => {
        console.warn("Status percentage failed:", err);
        this.pieLabels = [];
        this.pieSeries = [];
        checkAllLoaded();
      }
    });

    // Load recent activities
    this.projectService.getRecentActivities(projectName).subscribe({
      next: (res) => {
        this.recentActivity = res.recent_activities || [];
        checkAllLoaded();
      },
      error: (err) => {
        console.warn("Recent activities failed:", err);
        this.recentActivity = [];
        checkAllLoaded();
      }
    });
  }

  goBackToProjects(): void {
    this.router.navigate([""]);
  }

  // Helper methods for insights display
  getRiskClass(level: string): string {
    const classes: { [key: string]: string } = {
      'critical': 'risk-critical',
      'high': 'risk-high',
      'medium': 'risk-medium',
      'low': 'risk-low'
    };
    return classes[level] || 'risk-low';
  }

  getPriorityClass(priority: string): string {
    const classes: { [key: string]: string } = {
      'critical': 'priority-critical',
      'high': 'priority-high',
      'medium': 'priority-medium',
      'low': 'priority-low'
    };
    return classes[priority] || 'priority-low';
  }

  getAlertClass(level: string): string {
    const classes: { [key: string]: string } = {
      'critical': 'alert-critical',
      'warning': 'alert-warning',
      'info': 'alert-info'
    };
    return classes[level] || 'alert-info';
  }

  getTrendIcon(direction: string): string {
    const icons: { [key: string]: string } = {
      'increasing': '📈',
      'decreasing': '📉',
      'stable': '➡️'
    };
    return icons[direction] || '➡️';
  }

  getHealthIcon(score: string): string {
    const icons: { [key: string]: string } = {
      'Low': '🟢',
      'Medium': '🟡',
      'High': '🟠',
      'Critical': '🔴'
    };
    return icons[score] || '🟢';
  }
}