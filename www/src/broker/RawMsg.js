import React,{Component} from 'react'
import './Broker.css'

/**import './Broker.cimport './Broker.css'ss'
 * Sends raw message to broker
 */
class RawMsg extends Component{
 
    constructor(props)  {
        super(props);


        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;
        this.queueName='pytrade.broker.msg.raw';

        var rawMsg = {
            "transid":  Math.floor(Math.random()*1000000),
            "msgid": 12000, // Order msg id
            "action": "SIMPLE_STOP_ORDER",
            "MARKET_STOP_LIMIT": "YES",

            "ccode": "QJSIM",
            "scode": "SBER",
            "operation": "B",

            "quantity": 1,
            "clientcode": "10058",
            "account": "NL0011100043",
            "stopprice": 215
        }
        //rawMsg = {"msgid":12100,"clientcode":"10058","account":"NL0011100043", "number":"6059372033"}
        this.state={rawMsg: JSON.stringify(rawMsg)};
    }

    send(e) {
        console.log("Sending");
        this.stompClient.send(this.queueName, {'auto-delete':true}, this.state.rawMsg );
    }

    render() {

        return (
        <div classname="rawmsg" class="rawmsg panel">
            <header>Send raw message to broker</header>
            <div>
                <div class="param">
                    <label for="rawMsg">Raw msg:</label>
                    <textarea className="rawmsg" type="text" title="rawMsg" value={this.state.rawMsg} onChange={event=>this.setState({'rawMsg':event.target.value})}/>
                </div>
            </div>
            <div class="buttons">
                <button onClick={this.send.bind(this)} name="send">Send</button>
            </div>
          </div>
        );
      }
}
export default RawMsg;