import logo from './logo.svg';
import './App.css';
import {stompConfig} from './stompConfig'
import Stomp from 'stompjs'
import PriceChart from './pricechart/PriceChart.js';
import TradeAccount from './broker/TradeAccount.js';
import Orders from './broker/Orders.js';
import BuySell from './broker/BuySell';

import React,{Component} from 'react'



class App extends React.Component {

  constructor(props)  {
    super(props);
    this.priceChart = React.createRef();
    this.tradeAcount = React.createRef();
    this.orders = React.createRef();
    this.buySell = React.createRef();
    // Initialize stomp
    this.stompConfig = stompConfig;
    console.log('Creating stomp client over web socket: '  + this.stompConfig.brokerURL)
    this.stompClient = Stomp.over(new WebSocket(this.stompConfig.brokerURL))
  }

  componentDidMount() {
    // Connect to rabbit
    console.log('Connecting to rabbit')
    this.stompClient.connect(this.stompConfig.connectHeaders, this.onConnect.bind(this), this.onError)
  }

  componentWillUnmount() {
      // Disconnect from rabbit on exit
      console.log('Disconnecting')
      this.stompClient.disconnect();
  }      


  onConnect(){
      console.log('Connected');
      // Call child components' handlers
      this.priceChart.current.onConnect.bind(this.priceChart.current)();
      this.tradeAcount.current.onConnect.bind(this.tradeAcount.current)();
  }

  onError(e){
      console.log('Connection error: '+e)
  }


  render(){
      return (
          <div className="App">
            <header className="App-header">Pytrade dev tools</header>
            <main>
              <TradeAccount ref={this.tradeAcount} stompClient={this.stompClient}></TradeAccount>
              <Orders ref={this.orders} stompClient={this.stompClient}></Orders>
              <BuySell ref = {this.buySell} stompClient={this.stompClient}></BuySell>
              <PriceChart ref={this.priceChart} stompClient={this.stompClient}></PriceChart>

            </main>

          </div>
        );
  }
}

export default App;
