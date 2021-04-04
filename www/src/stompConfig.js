export const stompConfig = {
    // Typically login, passcode and vhost
    // Adjust these for your broker
    connectHeaders: {
      login: "guest",
      passcode: "guest"
    },

    // Broker URL, should start with ws:// or wss:// - adjust for your broker setup
    // Rabbit should have
    brokerURL: "ws://localhost:15674/ws",

    // Keep it off for production, it can be quit verbose
    // Skip this key to disable
    debug: function (str) {
      console.log('STOMP: ' + str);
    },

    // If disconnected, it will retry after 200ms
    reconnectDelay: 200,
  };
  export default stompConfig;