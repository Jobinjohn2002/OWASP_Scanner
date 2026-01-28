import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NgApexchartsModule} from 'ng-apexcharts';
import { Header } from './header/header';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet,NgApexchartsModule,Header],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('frontend');
}
