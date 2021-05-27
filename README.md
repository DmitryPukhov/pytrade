# pytrade
Trading robots written in Python. Connects directly to web quik server to read data and make orders. 

## Current status
Feed implemented. Simple buy/sell orders are implemented. Stop and market orders are under development.
Dev web ui is in progress.

## Prerequisites
Demo or live account with web quik https://arqatech.com/en/products/quik/terminals/user-applications/webquik/ from any broker. 
I use demo account at [junior.webquik.ru](https://junior.webquik.ru/).

## Setting up
Copy **pytrade/cfg/app-defaults.yaml** to a new local config **pytrade/cfg/app.yaml**
Configure **conn**, **account**, **passwd**  and **client_code** variables in your **pytrade/cfg/app.yaml**

## Running
docker-compose up

Open dev tools in browser: [http://localhost:3000](http://localhost:3000)
Price chart should appear in real time.

## Using in your robots
### Option 1. Interop mode (default). 
If *is_interop=True* in app.yaml, feed sends the prices to rabbit mq. Broker also receives buy/sell orders from rabbit. Any external system can read prices and make orders through rabbit.
### Option 2. Python library mode. 
*is_interop=False* in app.yaml, no integration through rabbitmq, just use pytrade as a lib from other python app. 
 
