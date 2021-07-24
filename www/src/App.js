import logo from './logo.svg';
import './App.css';
import {stompConfig} from './stompConfig'
import Stomp from 'stompjs'
import PriceChart from './pricechart/PriceChart.js';
import TradeAccount from './broker/TradeAccount.js';
import Orders from './broker/Orders.js';
import StockLimits from './broker/StockLimits.js';
import BuySell from './broker/BuySell';
import RawMsg from './broker/RawMsg'

import React,{Component} from 'react'



class App extends React.Component {

  constructor(props)  {
    super(props);
    this.rawMsg = React.createRef()
    this.priceChart = React.createRef();
    this.tradeAccount = React.createRef();
    this.orders = React.createRef();
    this.stockLimits = React.createRef();
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
      this.tradeAccount.current.onConnect.bind(this.tradeAccount.current)();
      this.stockLimits.current.onConnect.bind(this.stockLimits.current)();
  }

  onError(e){
      console.log('Connection error: '+e)
  }


  render(){
      return (
          <div className="App">
            <header className="App-header">Pytrade dev tools</header>
            <main>
                <RawMsg ref={this.rawMsg} stompClient={this.stompClient}></RawMsg>
                <TradeAccount ref={this.tradeAccount} stompClient={this.stompClient}></TradeAccount>
                <StockLimits ref={this.stockLimits} stompClient={this.stompClient}></StockLimits>

                <PriceChart ref={this.priceChart} stompClient={this.stompClient}></PriceChart>
                <BuySell ref = {this.buySell} stompClient={this.stompClient}></BuySell> 
            </main>

          </div>
        );
  }
}

export default App;
