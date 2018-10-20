# TigoCTM

### Version
2.0.0

### Installation

`pip install -r requirements.txt`

### Usage
Open your favorite Terminal and run these commands:

```sh
$ export FLASK_APP=app.py
$ flask run
```

Open a web browser and navigate to: `http://localhost:5000`.


### Blockchain ledger integration

Expects [GULD](https://github.com/TigoCTM/ledger-guld), [BTC](https://github.com/TigoCTM/ledger-bitcoin), [DASH](https://github.com/TigoCTM/ledger-dash), and [XCM](https://github.com/TigoCTM/ledger-XCM) guld branches to be available in the following location:

```
/home/<gulduser>/ledger/<commodity>/


### Tigo prices integration

Expects [Prices](https://github.com/TigoCTM/token-prices) branch to be available in the following location:

```
/home/<gulduser>/ledger/prices/