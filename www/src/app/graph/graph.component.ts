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
  public chartDiv = "chartDiv"
  public graph = {
    data: [
        { x: [], 
          open: [],
          high: [],
          low: [],
          close: [],
          y:[],
          // Candlestick chart does not look well on test data where o=c=h=l etc
          //type: 'candlestick'
          type: 'timeseries'
         }
    ],
    layout: { title: 'Price',
      xaxis:  { autorange: true},
      yaxis:  { autorange: true}
  }
};


  public candlesMsgs: string[] = [];
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

      // Refresh prices
      // If time is the same, replace the last point in the char
      var candles = this.graph.data[0]
      var times = candles.x
      var lastTime = times[times.length-1]
      if(lastTime == ohlcv.d){
       candles.x.pop()
       candles.open.pop()
       candles.high.pop()
       candles.low.pop()
       candles.close.pop()
       candles.y.pop()
    }

    candles.x.push(ohlcv.d)
    candles.open.push(ohlcv.o)
    candles.high.push(ohlcv.h)
    candles.low.push(ohlcv.l)
    candles.close.push(ohlcv.c)
    candles.y.push(ohlcv.c)

      // Hack to update plotly
    var candlesElement = this.plotly.getInstanceByDivId(this.chartDiv)
    this.plotly.update(candlesElement, [], this.graph.layout)
    this.plotly.update(candlesElement, this.graph.data, this.graph.layout)

      //this.cdRef.detectChanges();
  }

}
