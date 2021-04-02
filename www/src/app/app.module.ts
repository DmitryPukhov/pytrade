import {
  InjectableRxStompConfig,
  RxStompService,
  rxStompServiceFactory,
} from '@stomp/ng2-stompjs';

import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { rxStompConfig } from './rx-stomp.config';

import { AppComponent } from './app.component';
import { TradeAccountComponent } from './trade-account/trade-account.component';
import { GraphComponent } from './graph/graph.component';
import * as PlotlyJS from 'plotly.js/dist/plotly.js';
import { PlotlyModule } from 'angular-plotly.js';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
PlotlyModule.plotlyjs = PlotlyJS;

@NgModule({
  declarations: [
    AppComponent,
    TradeAccountComponent,
    GraphComponent
  ],
  imports: [
    BrowserModule, CommonModule, PlotlyModule, BrowserAnimationsModule
  ],
  providers: [
    {
      provide: InjectableRxStompConfig,
      useValue: rxStompConfig,
    },
    {
      provide: RxStompService,
      useFactory: rxStompServiceFactory,
      deps: [InjectableRxStompConfig],
    },
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
