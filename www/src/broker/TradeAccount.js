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


        this.state={tradeAccounts: new Map()};
        
        // this.state.tradeAccounts.set('trdacc', "{'trdacc':'acc1'}")
        // this.state.tradeAccounts.set('trdacc', "{'trdacc':'acc2'}")
    }

    onConnect(){
        // Subscribe to rabbit queue
        console.log('Subscribing to '+ this.tradeAccountQueue);
        this.stompClient.subscribe(this.tradeAccountQueue, this.onTradeAccount.bind(this),{});       
    }

    /**
     * Got trade account info
     */
    onTradeAccount(msg) {
        // {'msgid': 21022, 'trdacc': 'NL0011100043', 'firmid': 'NC0011100000', 'classList': ['QJSIM'], 'mainMarginClasses': ['QJSIM', 'SPBFUT'], 'limitsInLots': 0, 'limitKinds': ['0', '1', '2']}
        console.log('Got trade account msg '+ msg.body)
        var tradeAccountMap = this.state.tradeAccounts;
        var msgData = JSON.parse(msg.body.replace(/'/g, '"'));

         tradeAccountMap.set(msgData["trdacc"], msgData);

        this.setState({tradeAccounts: tradeAccountMap});
    }

    render() {
        // var body = "{'msgid': 21022, 'trdacc': 'NL0011100043', 'firmid': 'NC0011100000', 'classList': ['QJSIM'], 'mainMarginClasses': ['QJSIM', 'SPBFUT'], 'limitsInLots': 0, 'limitKinds': ['0', '1', '2']}"
        // var msgData = JSON.parse(body.replace(/'/g, '"'));
        // this.state.tradeAccounts.set(msgData.trdacc,msgData);


        // var body = "{'msgid': 21022, 'trdacc': '2NL0011100043', 'firorders.itemsmid': 'NC0011100000', 'classList': ['QJSIM'], 'mainMarginClasses': ['QJSIM', 'SPBFUT'], 'limitsInLots': 0, 'limitKinds': ['0', '1', '2']}"
        // var msgData = JSON.parse(body.replace(/'/g, '"'));
        // this.state.tradeAccounts.set(msgData.trdacc,msgData);


        var lst = Array.from(this.state.tradeAccounts.values());
        return (
        <div className="trdacc" class="trdacc panel">
            <header>Accounts</header>
            <ul className="acc-list">
            {Array.from(lst).map(v=> <li>{v.trdacc}</li>)}
            </ul>
                
          </div>
        );
      }
}
export default TradeAccount;