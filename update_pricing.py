# I was orginally going to do this using subclassing as all the API's I have found so far require unauthenticated GET
# (I'm assuming these are returned from a cache or something)
#
# Ended up just using a Python dispatch table which worked probably better. I don't think Python is particularly good
# with interfaces, i.e. every single provider gives you a URL to GET unauthenticated and returns JSON but there is no
# consistency to it. I'm still weighing my options for databases. I'm leaning toward SQLite because there is no write
# contention and I'm going to do the rest of the site in Django/Postgres don't want to cause problems there.
#
# I chose the three API providers as I was  somewhat familiar with them, I found it interesting that  all gave
# different quotes although with the price of Bitcoin now, even
# the $7.30 between Coindesk and Coinbase is something like 0.0005%. I can't imagine how many hours have been wasted
# (well to our benefit not the prop traders trying to arbitrage this so efficiently, doing the work of the efficient
# market analysis. I think this is a really good thing for Bitcoin as more than a speculative investment/trading
# opportunity. As someone has been in this world since I put tons of money into $3 Bitcoins before the Law and Order
# episode on "Mr. Bitcoin" I've found that even when I try to build something and it fails, I at least learn a lot in
# the process. When you try to do as economists consider 'rent-seeking' you either get rich or waste your life. These
# days hedge funds is a sales jobs as much as anything else and these guys would probably make more money selling
# SaaS contracts. Look at that debacle with shorting Herbalife it's not the seventies anymore, you gotta make something
# useful and sell it. But yeah I was attempting to sell a Mac App when I first developed this system. Figured it would
# appeal to the audience. I make steady but uninspiring sales (I think the service model is the way forward) and
# absolutely no purchases using Bitcoin. Now with the kids using Cashapp, and the techies using Coinbase perhaps the
# time has come.

import requests
import json
import logging
import datetime

CURRENCY_CODE = "USD"

COINBASE_API_ENDPOINT = "https://api.coinbase.com/v2/prices/spot?currency=USD"
COINDESK_API_ENDPOINT = "https://api.coindesk.com/v1/bpi/currentprice.json"
BLOCKCHAIN_INFO_API_ENDPOINT = "https://blockchain.info/ticker"


class BitcoinPricing:
    def __init__(self):
        self.price_data = []
        self.average_price = -1
        self.api_returns = 0

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger = logging.Logger("GetAPIPricing")
        logger.addHandler(ch)
        # TODO: add file handler

        # Using Python dispatch table

        dispatch_table = {0: pull_coindesk_api_endpoint,
                          1: pull_coinbase_api_endpoint,
                          2: pull_blockchain_info}

        logger.info("Pulling values from public APIs...")

        keys = list(dispatch_table.keys())

        for x in range(0, len(keys)):
            output = dispatch_table[x](logger)
            if output:
                self.api_returns += 1
                self.price_data.append(output)

        if self.api_returns > 0:
            self.average_price = 0.0
            for each in self.price_data:
                self.average_price += each.price
            self.average_price = float(self.average_price) / float(self.api_returns)

    def convert_usd_to_btc(self, usd):
        return float(usd) / float(self.average_price)


class PriceData:
    def __init__(self, provider, currency_code, api_endpoint, price, timestamp):
        self.provider = provider
        self.api_endpoint = api_endpoint
        self.currency_code = currency_code
        self.price = price
        self.timestamp = timestamp

    def __str__(self):
        return "API Provider: {0}\nAPI Endpoint: {1}\nTimestamp: {2}\nBTC Price: {3} ({4})".format(self.provider,
                                                                                                   self.api_endpoint,
                                                                                                   self.timestamp,
                                                                                                   self.price,
                                                                                                   self.currency_code)


def pull_blockchain_info(logger):
    try:
        response = requests.get(BLOCKCHAIN_INFO_API_ENDPOINT)
        try:
            json_data = json.loads(response.text)
        except json.JSONDecodeError:
            return None

        if json_data:
            try:
                price = json_data['USD']['15m']
                logger.info("Successfully pulled pricing data.")
                return PriceData("Blockchain.info", "USD", BLOCKCHAIN_INFO_API_ENDPOINT, price,
                                 datetime.datetime.utcnow().isoformat())
            except KeyError:
                return None
    except requests.exceptions.ConnectionError:
        logger.error("requests module threw ConnectionError on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None
    except requests.exceptions.HTTPError:
        logger.error("requests module threw HTTPError on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None
    except requests.exceptions.RequestException:
        logger.error("requests module threw RequestException on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None


def pull_coindesk_api_endpoint(logger):
    try:
        response = requests.get(COINDESK_API_ENDPOINT)
        try:
            json_data = json.loads(response.text)
        except json.JSONDecodeError:
            return None
        if json_data:
            try:
                price = json_data['bpi']['USD']['rate'].replace(',', '')
                logger.info("Successfully pulled pricing data.")
                return PriceData("CoinDesk", "USD", COINDESK_API_ENDPOINT, float(price),
                                 datetime.datetime.utcnow().isoformat())
            except KeyError:
                return None
        else:
            return None
    except requests.exceptions.ConnectionError:
        logger.error("requests module threw ConnectionError on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None
    except requests.exceptions.HTTPError:
        logger.error("requests module threw HTTPError on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None
    except requests.exceptions.RequestException:
        logger.error("requests module threw RequestException on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None


def pull_coinbase_api_endpoint(logger):
    try:
        response = requests.get(COINBASE_API_ENDPOINT)
        try:
            json_data = json.loads(response.text)
        except json.JSONDecodeError:
            return None
        if json_data:
            currency_code = json_data['data']['currency']
            price = float(json_data['data']['amount'])
            logger.info("Successfully pulled pricing data.")
            return PriceData("Coinbase", currency_code, COINBASE_API_ENDPOINT, price,
                             datetime.datetime.utcnow().isoformat())
        else:
            return None
    except requests.exceptions.ConnectionError:
        logger.error("requests module threw ConnectionError on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None
    except requests.exceptions.HTTPError:
        logger.error("requests module threw HTTPError on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None
    except requests.exceptions.RequestException:
        logger.error("requests module threw RequestException on API endpoint: {0}".format(COINBASE_API_ENDPOINT))
        return None


if __name__ == "__main__":
    bitcoin_pricing = BitcoinPricing()
    if bitcoin_pricing.api_returns > 0:
        print("Average BTC Price: {0}".format(bitcoin_pricing.average_price))
        print("$10 USD in BTC: {0}".format(bitcoin_pricing.convert_usd_to_btc(10)))
        print("$100 USD in BTC: {0}".format(bitcoin_pricing.convert_usd_to_btc(100)))
        print("$1000 USD in BTC: {0}".format(bitcoin_pricing.convert_usd_to_btc(1000)))
