import './BuySell.css'
import React,{Component} from 'react'


/**
 * Buy or sell order fill in and send
 */
class BuySell extends Component{
 
    constructor(props)  {
        super(props);

        // Asset to trade
        // todo: parameterise
        this.secClass =  'QJSIM';
        this.secCode= 'SBER';

        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;
        this.queueName='pytrade.broker.cmd.buysell';
        this.quantity=React.createRef();

        this.state={quantity: 1, price:0.0};
    }
    // updateQuantity(e) {
    //     this.setState({'quantity':e.target.value})
    // }

    buy(e) {
        console.log("Buy pressed");
        var msg = {"operation": "buy", "secClass": this.secClass, "secCode": this.secCode, "quantity": this.state.quantity, "price": Number(this.state.price)};
        this.stompClient.send(this.queueName, {'auto-delete':true}, JSON.stringify(msg), );
    }
    sell(e) {
        console.log("Sell pressed");
        var msg = {"operation": "sell", "secClass": this.secClass, "secCode": this.secCode, "quantity": this.state.quantity, "price": Number(this.state.price)};
        this.stompClient.send(this.queueName, {'auto-delete':true}, JSON.stringify(msg));
    }

    render() {

        return (
        <div className="buysell"  class="panel buysell">
            <header>Send order</header>
            <div class="asset">
                <div class="param">
                    <label for="assetCode">Asset:</label><label name="assetCode" class="assetCode">{this.secClass}/{this.secCode}</label>
                </div>
                <div class="param">
                    <label for="price">Price:</label>
                    <input className="price" title="Price" value={this.state.price} onChange={event=>this.setState({'price':event.target.value})}></input>
                </div>
                <div class="param">
                    <label for="quantity">Quantity:</label>
                    <input className="quantity" title="Quantity" value={this.state.quantity} onChange={event => this.setState({ 'quantity': event.target.value})}></input>
                </div>
            </div>
            <div class="buttons">
                <button onClick={this.buy.bind(this)} name="buyButton">Buy</button>
                <button onClick={this.sell.bind(this)}>Sell</button>
            </div>
          </div>
        );
      }
}
export default BuySell;