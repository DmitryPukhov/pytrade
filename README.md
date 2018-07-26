# pytrade

Trading robots written in Python. Contain connector to broker client terminal to read data and make orders. 
My broker's terminal is [Quik](https://arqatech.com/en/products/quik/). 
Also  socket based interop library [QuikSocketTransfer](https://github.com/Arseniys1/QuikSocketTransfer) required.

## Prerequisites
Robot and broker's terminal can be the on the same or different machines. 

### Server 

* **Windows** OS or **Linux** with **Wine**. 
* [Quik](https://arqatech.com/en/products/quik/) - Quik trading terminal.
* [QuikSocketTransfer](https://github.com/Arseniys1/QuikSocketTransfer) added to Quik.
Disclamer: Quik works with Wine, but I didn't try QuikSocketTransfer library on it.


### Client
* Any OS
* Python 3

## Current working configuration:
``` 
* Server: Virtual machine, with Windows XP SP3, Quik and QuikSocketTransfer
* Client and host for server virtual machine: Ubuntu 18.04 with Python 3.7
```
