import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { RxStompService } from '@stomp/ng2-stompjs';
import { Message } from '@stomp/stompjs';
import { PlotlyComponent, PlotlyService } from 'angular-plotly.js';
import { Subscription } from 'rxjs';


@Component({
  selector: 'app-graph',
  templateUrl: './graph.component.html',
  styleUrls: ['./graph.component.css']
})
export class GraphComponent  implements OnInit, OnDestroy {
  public graph = {
    data: [
        { x: [], 
          open: [],
          high: [],
          low: [],
          close: [],
           type: 'candlestick' }
    ],
    layout: { title: 'Candles',
      xaxis:  { autorange: true},
      yaxis:  { autorange: true}
  }
};
public timeSeries = {
  data:[
    {x:[],
    y:[],
  type:'timeseries'}
  ]
}

  public graphSample = {
    data: [
        { x: [1, 2, 3], y: [2, 6, 3], type: 'scatter', mode: 'lines+points', marker: {color: 'red'} },
        { x: [1, 2, 3], y: [2, 5, 3], type: 'bar' },
    ],
    layout: { title: 'A Fancy Plot'}
};
  public candlesMsgs: string[] = ['empty'];
  private topicSubscription: Subscription;
  // Rabbit queue name
  private candlesQueue = 'pytrade.feed.candles'

  constructor(private rxStompService: RxStompService, public plotly: PlotlyService, private cdRef:ChangeDetectorRef) {}
  ngOnInit() {

    // Subscribe to rabbit messages
    this.topicSubscription = this.rxStompService
      .watch(this.candlesQueue)
      .subscribe((message: Message) => {
        this.candlesMsgs.push(message.body);
        this.onCandle(message.body)
      },
      (error: Error) => {
        console.log(new Date(), error)
      });
  }

  ngOnDestroy() {
    this.topicSubscription.unsubscribe();
  }

  onCandle(ohlcvString) {
    // Json like {'d': '2021-03-28 04:06:00', 'o': 28863, 'c': 28863, 'h': 28863, 'l': 28863, 'v': 20206}
      console.log(ohlcvString)
      var ohlcv = JSON.parse(ohlcvString.replace(/'/g, '"'))
      //this.graph.datapush(ohlcv.d, ohlcv.o, ohlcv.h, ohlcv.l, ohlcv.c);
      this.graph.data[0].x.push(ohlcv.d)
      this.graph.data[0].open.push(ohlcv.o)
      this.graph.data[0].high.push(ohlcv.h)
      this.graph.data[0].low.push(ohlcv.l)
      this.graph.data[0].close.push(ohlcv.c)

      this.timeSeries.data[0].x.push(ohlcv.d)
      this.timeSeries.data[0].y.push(ohlcv.c)
      this.cdRef.detectChanges();
     
  }

}
