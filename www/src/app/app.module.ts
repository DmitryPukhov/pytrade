import {
  InjectableRxStompConfig,
  RxStompService,
  rxStompServiceFactory,
} from '@stomp/ng2-stompjs';

import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { rxStompConfig } from './rx-stomp.config';

import { AppComponent } from './app.component';
import { TradeAccountComponent } from './trade-account/trade-account.component';
import { GraphComponent } from './graph/graph.component';


@NgModule({
  declarations: [
    AppComponent,
    TradeAccountComponent,
    GraphComponent
  ],
  imports: [
    BrowserModule
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
