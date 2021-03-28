# This defines our starting point
FROM node:10 as build-step
RUN mkdir -p /www/src/app
WORKDIR /www
# Install common dependencies
RUN npm install -g @angular/cli
RUN npm i

# Install libs for rabbit
RUN npm install -g amqplib
RUN npm install -g net
RUN npm install -g tls
RUN npm install -g stream
RUN npm install -g buffer
RUN npm install -g promise
RUN npm install @stomp/ng2-stompjs
RUN npm install -g @stomp/stompjs websocket --save


COPY . .
#RUN npm install && ng serve --host 0.0.0.0 --port 4200 --live-reload -o &
#FROM nginx:1.17.1-alpine
#COPY --from=build-step /www /usr/share/nginx/html


