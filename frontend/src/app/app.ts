import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NgApexchartsModule} from 'ng-apexcharts';
// import { DashBoardComponent } from './dashboard/dashboard';
// import { ProjectDetailsComponent } from './project/project';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet,NgApexchartsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('frontend');
}
