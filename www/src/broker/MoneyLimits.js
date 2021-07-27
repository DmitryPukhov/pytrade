import React,{Component} from 'react'


/**
 * Money limits (positions on assets) from Quik
 */
class MoneyLimits extends Component{
 
    constructor(props)  {
        super(props);

        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;
        this.queueName='pytrade.broker.money.limits';
   
        // Money limit msg sample: {'msgid': 21004, 'mid': 13800, 'valut': 'SUR', 'tag': 'RTOD', 'cbal': 300000, 'clim': 0, 'obal': 300000, 'olim': 0, 'block': 0, 'ucode': '10815', 'status': 1, 'firmid': 'MB1000100000', 'limit_kind': 0, 'qty_scale': 2}
        this.state={moneyLimits: []};
    }

    onConnect(){
        // Subscribe to rabbit queue
        console.log('Subscribing to '+ this.queueName);
        this.stompClient.subscribe(this.queueName, this.onMoneyLimits.bind(this),{});       
    }

    /**
     * Got info
     */
    onMoneyLimits(msg) {
        console.log('Got msg '+ msg.body)

        // Update stock limit map with new position
        var moneyLimits = this.state.moneyLimits
        moneyLimits.push(JSON.parse(msg.body.replace(/'/g, '"')));
        this.setState({"moneyLimits": moneyLimits});

    }

    render() {
        // {'msgid': 21004, 'mid': 13800, 'valut': 'SUR', 'tag': 'RTOD', 'cbal': 300000, 'clim': 0, 'obal': 300000, 'olim': 0, 'block': 0, 'ucode': '10815', 'status': 1, 'firmid': 'MB1000100000', 'limit_kind': 0, 'qty_scale': 2}
        return (
        <div className="moneylimits"  class="moneylimits panel">
            <header>Money limits</header>
            <table className="positions">
                <tr>
                    <th>asset</th><th>count</th><th>price</th>
                    </tr>
                    {Array.from(this.state.moneyLimits.values()).map(v=> <tr>
                        <td>{v.scode}</td><td>{v.cbal}</td><td>{v.avg}</td>
                        </tr>)}
            </table>
          </div>
        );
      }
    }
export default StockLimits;