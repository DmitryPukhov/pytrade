# pytrade
Trading robots written in Python. Connects directly to web quik server to read data and make orders. 

## Current status
Feed implemented. Simple buy/sell orders are implemented. Stop and market orders are under development.
Dev web ui is in progress.

## Prerequisites
Demo or live account with web quik https://arqatech.com/en/products/quik/terminals/user-applications/webquik/ from any broker. 
I use demo account at [junior.webquik.ru](https://junior.webquik.ru/).

## Setting up
Configure **server**, **account** and **passwd** variables in **Config.py**

## Running
docker-compose up

Open dev tools in browser: [http://localhost:3000](http://localhost:3000)
Price chart should appear in real time.
 
