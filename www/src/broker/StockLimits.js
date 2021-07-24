import React,{Component} from 'react'


/**
 * Stock limits (positions on assets) from Quik
 */
class StockLimits extends Component{
 
    constructor(props)  {
        super(props);

        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;
        this.queueName='pytrade.broker.stock.limits';
   
        //this.state={stockLimits: new Map([['11',{'scode':'scodeval', 'cbal':100,'vavg':123}]])};
        this.state={stockLimits: new Map([])};
    }

    onConnect(){
        // Subscribe to rabbit queue
        console.log('Subscribing to '+ this.queueName);
        this.stompClient.subscribe(this.queueName, this.onStockLimits.bind(this),{});       
    }

    /**
     * Got info
     */
    onStockLimits(msg) {
        console.log('Got msg '+ msg.body)

        // Update stock limit map with new position
        var stockLimitMap = this.state.stockLimits
        var msgData = JSON.parse(msg.body.replace(/'/g, '"'));
        stockLimitMap.set(msgData["scode"], msgData);
        this.setState({stockLimits: stockLimitMap});

    }

    render() {
        var lst = Array.from(this.state.stockLimits.values());
        return (
        <div className="stocklimits"  class="stocklimits panel">
            <header>Stock limits</header>
            <table className="positions">
                <tr>
                    <th>asset</th><th>count</th><th>price</th>
                    </tr>
                    {Array.from(this.state.stockLimits.values()).map(v=> <tr>
                        <td>{v.scode}</td><td>{v.cbal}</td><td>{v.avg}</td>
                        </tr>)}
            </table>
          </div>
        );
      }
    }
export default StockLimits;