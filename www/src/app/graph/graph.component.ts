import { Component, OnDestroy, OnInit } from '@angular/core';
import { RxStompService } from '@stomp/ng2-stompjs';
import { Message } from '@stomp/stompjs';
import { Subscription } from 'rxjs';


@Component({
  selector: 'app-graph',
  templateUrl: './graph.component.html',
  styleUrls: ['./graph.component.css']
})
export class GraphComponent  implements OnInit, OnDestroy {
  public candles: string[] = [];
  private topicSubscription: Subscription;
  // Rabbit queue name
  private candlesQueue = 'pytrade.feed.candles'

  constructor(private rxStompService: RxStompService) {}

  ngOnInit() {
    // Subscribe to rabbit messages
    this.topicSubscription = this.rxStompService
      .watch(this.candlesQueue)
      .subscribe((message: Message) => {
        this.candles.push(message.body);
      },
      (error: Error) => {
        console.log(new Date(), error)
      });
  }

  ngOnDestroy() {
    this.topicSubscription.unsubscribe();
  }

}
