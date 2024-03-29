import React,{Component} from 'react'


/**
 * Opened orders information
 */
class Orders extends Component{
 
    constructor(props)  {
        super(props);

        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;
        this.queueName='pytrade.broker.orders';
        this.state={orders: new Map()};
    }

    onConnect(){
        // Subscribe to rabbit queue
        console.log('Subscribing to '+ this.queueName);
        this.stompClient.subscribe(this.queueName, this.onOrders.bind(this),{});       
    }

    /**
     * Got orders info
     */
    onOrders(msg) {
        console.log('Got orders msg '+ msg.body)
        var orders = this.state.orders
        var msgData = JSON.parse(msg.body.replace(/'/g, '"'));
        orders.set(msgData['number'],msgData)
        this.setState({orders: orders});
    }

    render() {
        //2021-04-16 19:56:38,164.164 DEBUG WebQuikBroker - on_orders: On orders. msg={'msgid': 21001, 'qdate': 20210416, 'qtime': 195529, 'ccode': 'QJSIM', 'scode': 'SBER', 'sell': 0, 'account': 'NL0011100043', 'price': 28250, 'qty': 1, 'volume': 282500, 'balance': 0, 'yield': 0, 'accr': 0, 'refer': '10058//', 'type': 24, 'firm': 'NC0011100000', 'ucode': '10058', 'number': '5830057748', 'status': 2, 'price_currency': '', 'settle_currency': ''}
        // class Order:
    // number: str
    // dt: datetime
    // class_code: str
    // sec_code: str
    // is_sell: bool
    // account: str
    // price: float
    // quantity: int
    // volume: float
    // status: str
        return (
        <div className="orders"  class="orders panel">
            <header>Orders</header>
            <table className="positions">
                <tr>
                    <th>number</th>
                    <th>dt</th>
                    <th>asset</th>
                    <th>type</th>
                    <th>account</th>
                    <th>price</th>
                    <th>quantity</th>
                    <th>volume</th>
                    <th>status</th>
                </tr>
                    {Array.from(this.state.orders.values()).map(v=> <tr>
                        <td>{v.number}</td>
                        <td>{v.dt}</td>
                        <td>{v.class_code}/{v.sec_code}</td>
                        <td>{v.is_sell ? "sell": "buy"}</td>
                        <td>{v.account}</td>
                        <td>{v.price}</td>
                        <td>{v.quantity}</td>
                        <td>{v.volume}</td>
                        <td>{v.status}</td>
                        </tr>)}
            </table>
          </div>
    
            );
      }
}
export default Orders;