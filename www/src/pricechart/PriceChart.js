import './pricechart.css'
import React,{Component} from 'react'
import {stompConfig} from '../stompConfig'
import Stomp from 'stompjs'
import Plot from 'react-plotly.js'
import Plotly from 'react-plotly.js'


class PriceChart extends Component{
    graph = {
        data: [
            { x: [], 
              y:[],
              // Candlestick chart does not look well on test data where o=c=h=l etc
              type: 'scatter',
              line: {
                color: '#ff8300'
              }
             }
        ],
        layout: { title: 'Price',
          xaxis:  { autorange: true},
          yaxis:  { autorange: true}
      }
    };    

    constructor(props)  {
        super(props);
        this.plotly = React.createRef();

        // Get stomp client for rabbit connection
        this.stompClient = props.stompClient;

        this.candlesQueue='pytrade.feed.candles';
        this.state={lastCandle:{d:null,c:null}, data: this.graph.data, layout: this.graph.layout, candles: []};
    }

   /***
     * Got new candle event handler
     */
    onCandle(msg){
        console.log('Got message: '+msg);
        var ohlcv = JSON.parse(msg.body.replace(/'/g, '"'))
        ohlcv.millis = Date.parse(ohlcv.d);
        // Update last candle state
        if(ohlcv == null){
            // If badly parsed
            this.setState({lastCandle: {d:null,c:null}});
            return;
        } else {
            this.setState({lastCandle: {d:ohlcv.d, c:ohlcv.c}});
        }

        var candles = this.state.candles;

        // If time is the same, remove last candle. A new one will be added.
        var lastTime = candles.map(c => c.d)[candles.length-1];
        if(ohlcv.d === lastTime) {
            candles.pop();
        }

        // Add received candle and sort all by time
        candles.push(ohlcv);
        candles = candles.sort((c1,c2)=>{
            return c1.millis - c2.millis
        });

        // Update the state for chart
        this.state.data[0].x = candles.map(c=>c.d);
        this.state.data[0].y = candles.map(c=>c.c);
        var tmpData = this.state.data

        // To update plotly, we need to change then return it back
        this.setState({data: []});
        this.setState({data: tmpData});
    }

    onConnect(){
        // Subscribe to rabbit queue
        console.log('Subscribing to '+ this.candlesQueue);
        this.stompClient.subscribe(this.candlesQueue, this.onCandle.bind(this), {});       
    }

    render() {
        return (
        <div class="panel price-chart">
                <div class="last-candle">
                Last candle: {this.state.lastCandle.d}, price: {this.state.lastCandle.c}
                </div>
                <div class='price-chart'>
                    <Plot className='plot' ref = {this.plotly}   data={this.state.data} layout={this.state.layout}/>
                </div>
          </div>
        );
      }
}
export default PriceChart;