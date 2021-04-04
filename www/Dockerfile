# This defines our starting point
FROM node:13.12.0-alpine
# alpine images doesn't have bash installed out of box. Install it here.
RUN apk update && apk add bash

WORKDIR /www

# add `/app/node_modules/.bin` to $PATH
ENV PATH /www/node_modules/.bin:$PATH

# install node dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm install
RUN npm install react-scripts@3.4.1 -g

# Stomp over websocket to get data from rabbit
# Not sure all these are required ))
RUN npm install websocket stomp stomp-websocket stompjs

RUN npm install react-plotly.js

COPY . .
# start app
CMD ["npm", "start"]
