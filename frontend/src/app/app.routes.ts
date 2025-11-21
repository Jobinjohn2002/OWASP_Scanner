import { Routes } from '@angular/router';
import { DashBoardComponent } from './dashboard/dashboard';
import { ProjectDetailsComponent } from './project/project';

export const routes: Routes = [
{path:"", component:DashBoardComponent},
{ path: 'project-details/:id', component: ProjectDetailsComponent }
];
