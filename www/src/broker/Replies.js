import React,{Component} from 'react'


/**
 * Reply messages from broker.
 */
class Replies extends Component{
 
    constructor(props)  {
        super(props);

        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;
        this.queueName='pytrade.broker.msg.reply';
        this.state={msgs: []};
    }

    onConnect(){
        // Subscribe to rabbit queue
        console.log('Subscribing to '+ this.queueName);
        this.stompClient.subscribe(this.queueName, this.onMsg.bind(this),{});       
    }

    /**
     * Got new reply message
     */
    onMsg(msg) {
        console.log('Got reply msg '+ msg.body)
        var msgs = this.state.msgs
        var msgBody = msg.body.replace(/'/g, '"');
        msgs.push(msgBody)
        this.setState({msgs: msgs});
    }

    render() {
        return (
        <div className="replies"  class="replies panel">
            <header>Reply messages</header>
                    {Array.from(this.state.msgs).map(msg => <div>
                        {msg}
                        </div>)}
        </div>
            );
      }
}
export default Replies;