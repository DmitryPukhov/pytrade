import React,{Component} from 'react'


/**
 * Trade account information
 */
class TradeAccount extends Component{
 
    constructor(props)  {
        super(props);

        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;

        this.tradeAccountQueue='pytrade.broker.trade.account';
        this.state={tradeAccount:''};
    }

    onConnect(){
        // Subscribe to rabbit queue
        console.log('Subscribing to '+ this.tradeAccountQueue);
        this.stompClient.subscribe(this.tradeAccountQueue, this.onTradeAccount.bind(this));       
    }

    /**
     * Got trade account info
     */
    onTradeAccount(msg) {
        this.setState({tradeAccount: msg.body});
    }

    render() {
        return (
        <div className="trade-account">
            <div>Trade account:{this.state.tradeAccount}</div>
          </div>
        );
      }
}
export default TradeAccount;