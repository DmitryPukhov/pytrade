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

Open dev tools in browser: [http://localhost:3000](http://localhost:3000) - price chart should appear in real time.
Open rabbitmq at [http://localhost:15672/](http://localhost:15672/), use rabbitmq default login and password: quest/quest

## Using in your robots

### Option 1. Single mode. 
Only Python lives here, no integration with external systems.
Set *is_interop: False*, in *app.yaml*. Add your strategy python class to strategy folder and set *strategy=<Your strategy class name>* in *app.yaml* Run and debug in your preferrable IDE using *App.py* entry point

### Option 2. Interop mode - manage pytrade from external system
Integration with external systems through rabbitmq If *is_interop: True* in app.yaml, pytrade sends the prices and receives buy/sell instructions to/from rabbit mq.  Any external system can read prices and make orders through rabbit. 

## Capturing the Feed to file system
Set *is_feed2csv: True* in *app.yaml* and pytrade will save all received data into *data* folder in csv format.