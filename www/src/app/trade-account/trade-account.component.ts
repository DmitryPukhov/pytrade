//"use strict";
import { chainedInstruction } from '@angular/compiler/src/render3/view/util';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { RxStompService } from '@stomp/ng2-stompjs';
import { Message } from '@stomp/stompjs';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-trade-account',
  templateUrl: './trade-account.component.html',
  styleUrls: ['./trade-account.component.css']
})

/**
 * Account information
 */
export class TradeAccountComponent  implements OnInit, OnDestroy {
  public receivedMessages: string[] = [];
  private topicSubscription: Subscription;
  // Rabbit queue name
  private accountQueue = 'pytrade.broker.trade.account'

  constructor(private rxStompService: RxStompService) {}

  ngOnInit() {
    // Subscribe to rabbit messages
    this.topicSubscription = this.rxStompService
      .watch(this.accountQueue)
      .subscribe((message: Message) => {
        this.receivedMessages.push(message.body);
      },
      (error: Error) => {
        console.log(new Date(), error)
      });
  }

  ngOnDestroy() {
    this.topicSubscription.unsubscribe();
  }

  onSendMessage() {
    // Send test message to rabbit
    const message = `Message generated at ${new Date()}`;
    this.rxStompService.publish({ destination: this.accountQueue, body: message });
  }
}
