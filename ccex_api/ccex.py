#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
"""

import sys
import hmac
import requests

from time import time


class CCexAPIError(Exception):
    """
    CCex API default error.
    """

    def __init__(self, *args, **kwargs):
        self.traceback = sys.exc_info()
        super(CCexAPIError, self).__init__(*args)


class CCexAPIRequestError(CCexAPIError):
    """
    CCex API request error.
    """
    def __init__(self, prep_req, exc):
        self.request = prep_req
        super(CCexAPIRequestError, self).__init__(
            'Fail to query CCex API: {}'.format(repr(exc))
        )


class CCexAPIResponseFormatError(CCexAPIError):
    """
    CCex API response deserialization error.
    """
    def __init__(self, response, exc):
        self.response = response
        super(CCexAPIResponseFormatError, self).__init__(
            'Fail to parse CCex response: {}'.format(repr(exc))
        )


class CCexAPIResponseError(CCexAPIError):
    """
    CCex API response error.
    """
    def __init__(self, response, data):
        self.response = response
        self.data = data
        super(CCexAPIResponseError, self).__init__(
            'CCex API returned an error: {}'.format(data.get('message', 'Unknown error'))
        )


class CCexAPI(object):
    """
    CCex API main class.

    Examples::

            ccex = CCexAPI()
            ccex.tickers.tickers_coinnames()
            ccex.public.get_market_summaries()

            ccex = CCexAPI('api_key', 'api_secret')
            ccex.public.get_market_summaries()
            ccex.private.get_balances()

    """
    API_URL = 'https://c-cex.com/t'

    def __init__(self, api_key=None, api_secret=None):
        """
        `CCexAPI` offers three attribute representing group of endpoints.
        The `private` attribute will only be created when credentials are present.

        See Also:
        Args:
            api_key (str, optional): Your API key
            api_secret (str, optional): Your API private secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'CCEX_API_WRAPPER'})

        if self.__class__ == CCexAPI():
            self.tickers = CCexAPITickers(api_key, api_secret)
            """ Tickers endpoints"""
            self.public = CCexAPIPublic(api_key, api_secret)
            """ Public endpoints"""
            if api_key and api_secret:
                self.private = CCexAPIPrivate(api_key, api_secret)
                """ Private endpoints"""

    def _call(self, call, path, params=None, headers=None, authenticated=False):
        try:
            url = '{url}/{path}'.format(url=self.API_URL, path=path)
            if not params:
                params = {}

            params['a'] = call

            authenticate = False
            if authenticated:
                if self.api_key and self.api_secret:
                    authenticate = True

                    params['apikey'] = self.api_key
                    params['nonce'] = int(time())
                else:
                    raise CCexAPIError('This call requires an API key and secret')

            req = requests.Request(
                method='GET',
                url=url,
                params=params,
                headers=headers)
            prep_req = req.prepare()

            if authenticate:
                signature = hmac.new(
                    self.api_secret.encode('utf-8'),
                    prep_req.url.encode('utf-8'),
                    'sha512'
                ).hexdigest()
                prep_req.headers['apisign'] = signature

            try:
                res = self.session.send(prep_req)
            except Exception as exc:
                raise CCexAPIRequestError(prep_req, exc)

            if 'Maintenance' in res.text:
                raise CCexAPIResponseError(res, {'message': res.text})

            try:
                data = res.json()
            except Exception as exc:
                raise CCexAPIResponseFormatError(res, exc)

            # for tickers
            if url.endswith('json'):
                return data

            # for api methods
            if data.get('success') is not True:
                raise CCexAPIResponseError(res, data)

            return data.get('result')

        except CCexAPIError:
            raise
        except Exception as exc:
            raise CCexAPIError('Unexpected error during CCex API call: {}'.format(repr(exc)))


class CCexAPITickers(CCexAPI):
    """
    Tickers endpoints
    """
    def tickers_coin_names(self):
        """
        Full names for all coin tickers.

        See Also:
            https://c-cex.com/t/coinnames.json

        Returns:
            dict(str, str): mapping of abbreviations and coin names

        Example::

            {
                "usd": "USD",
                "btc": "Bitcoin",
                "1337": "1337",
                ...
                "zny": "BitZeny"
            }

        """
        return self._call(
            call='ticker',
            path='coinnames.json'
        )

    def tickers_pairs(self):
        """
        List of available trading pairs.

        See Also:
            https://c-cex.com/t/pairs.json

        Returns:
            list(str): listing of pairs names

        Example::

            ["usd-btc", "1337-btc", ... "zny-doge"]

        """
        return self._call(
            call='ticker',
            path='coinnames.json'
        )['pairs']

    def tickers_pair_market_data(self, coin1, coin2):
        """
        Online market data for given trading pair.

        See Also:
            https://c-cex.com/t/dash-btc.json

        Args:
            coin1: first coin name in the pair
            coin2: second coin name in the pair

        Returns:
            dict: various data about the market

        Example::

            {
                "high": 0.016,
                "low": 0.01560006,
                "avg": 0.01580003,
                "lastbuy": 0.01560009,
                "lastsell": 0.016,
                "buy": 0.01560012,
                "sell": 0.016999,
                "lastprice": 0.01560009,
                "buysupport": 35.84405079,
                "updated": 1459411200
            }

        """
        return self._call(
            call='ticker',
            path='{coin1}-{coin2}.json'.format(coin1=coin1, coin2=coin2)
        ).get('ticker')

    def tickers_all_pairs_market_data(self):
        """
        All online trading pairs market data.

        See Also:
            https://c-cex.com/t/prices.json

        Returns:
            dict: various data about the market

        Example::

            {
                "1337-btc": {
                    "high": 0,
                    "low": 0,
                    "avg": 0,
                    "lastbuy": 0.00000007,
                    "lastsell": 0.00000008,
                    "buy": 0.00000007,
                    "sell": 0.00000008,
                    "lastprice": 0.00000008,
                    "updated": 1459411200
                },
                "acp-btc": {
                    "high": 0,
                    "low": 0,
                    "avg": 0,
                    "lastbuy": 0.00000403,
                    "lastsell": 0.000005,
                    "buy": 0.00000413,
                    "sell": 0.00000661,
                    "lastprice": 0.00000403,
                    "updated": 1459411200
                }, ...
            }

        """
        return self._call(
            call='ticker',
            path='prices.json'
        )

    def tickers_volume_coin(self, coin):
        """
        Online volume report for last 24 hours at a given coin market

        See Also:
            https://c-cex.com/t/volume_btc.json

        Args:
            coin: coin name

        Returns:
            dict: various data about the market

        Example::

            {
                "usd": {
                    "last": 0.00240391,
                    "vol": 0.08700954
                },
                "1337": {
                    "last": 0.00000008,
                    "vol": 0.05472871
                }, ... }
            }

        """
        return self._call(
            call='ticker',
            path='volume_{coin}.json'.format(coin=coin)
        ).get('ticker')


# noinspection PyUnusedLocal
class CCexAPIPublic(CCexAPI):
    """
    Public endpoints
    """
    def _public_call(self):
        """
        Hackish way of not rewriting real call name and params ...
        They are extracted from the caller's function.
        """
        # noinspection PyProtectedMember
        caller = sys._getframe().f_back
        call = caller.f_code.co_name.replace('_', '')
        params = dict((k.replace('_', ''), v) for k, v in caller.f_locals.items() if k != 'self')

        return self._call(
            call=call,
            path='api_pub.html',
            params=params
        )

    def get_markets(self):
        """
        Get the open and available trading markets along with other meta data.

        See Also:
            https://c-cex.com/?id=api#getmarkets

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "MarketCurrency": "USD",
                "BaseCurrency": "BTC",
                "MarketCurrencyLong": "USD",
                "BaseCurrencyLong": "Bitcoin",
                "MinTradeSize": 0.01000000,
                "MarketName": "USD-BTC",
                "IsActive": true,
                "Created": "2014-01-01T00:00:00"
            }, {
                "MarketCurrency": "1337",
                "BaseCurrency": "BTC",
                "MarketCurrencyLong": "1337",
                "BaseCurrencyLong": "Bitcoin",
                "MinTradeSize": 0.01000000,
                "MarketName": "1337-BTC",
                "IsActive": true,
                "Created": "2014-01-01T00:00:00"
            }, ... ]

        """
        return self._public_call()

    def get_orderbook(self, market, type_, depth=50):
        """
        Retrieve the orderbook for a given market.

        See Also:
            https://c-cex.com/?id=api#getorderbook

        Args:
            market (str): Market name (ex: USD-BTC)
            type_ (str): Type of orders to return: "buy", "sell" or "both"
            depth (int): Depth of an order book to retrieve. Default is 50, max is 100

        Returns:
            dict: various data about the market

        Example::

            {
                "buy": [{
                    "Quantity": 0.01029604,
                    "Rate": 430.00010000
                }, {
                    "Quantity": 0.10000000,
                    "Rate": 423.00000000
                }]
            }

        """
        return self._public_call()

    def get_full_orderbook(self, depth=50):
        """
        Retrieve the orderbook for all markets.

        See Also:
            https://c-cex.com/?id=api#getfullorderbook

        Args:
            depth (int): Depth of an order book to retrieve. Default is 50, max is 100

        Returns:
            dict: various data about the market

        Example::

            {
                "buy": [{
                    "Market":"btc-btlc",
                    "Quantity": 0.01029604,
                    "Rate": 430.00010000
                }, {
                    "Market":"btc-btlc",
                    "Quantity": 0.10000000,
                    "Rate": 423.00000000
                }]
            }

        """
        return self._public_call()

    def get_market_summaries(self):
        """
        Get the last 24 hour summary of all active markets.

        See Also:
            https://c-cex.com/?id=api#getmarketsummaries


        Returns:
            list(dict): various data about the market

        Example::

            [{
                "MarketName": "USD-BTC",
                "High": 0.00000000,
                "Low": 0.00000000,
                "Volume": 121.99200025,
                "Last": 0.00226757,
                "BaseVolume": 0.27662540,
                "TimeStamp": "1451462400",
                "Bid": 0.00226757,
                "Ask": 0.00235294,
                "OpenBuyOrders": 100,
                "OpenSellOrders": 100,
                "PrevDay": 0.00235294,
                "Created": "1451462400",
                "DisplayMarketName": null
            }, {
                "MarketName": "1337-BTC",
                "High": 0.00000000,
                "Low": 0.00000000,
                "Volume": 0.00000000,
                "Last": 0.00000006,
                "BaseVolume": 0.00000000,
                "TimeStamp": "1451462400",
                "Bid": 0.00000006,
                "Ask": 0.00000009,
                "OpenBuyOrders": 100,
                "OpenSellOrders": 100,
                "PrevDay": 0.00000009,
                "Created": "1451462400",
                "DisplayMarketName": null
            }, ... ]

        """
        return self._public_call()

    def get_market_history(self, market, count=50):
        """
        Latest trades that have occured for a specific market.

        See Also:
            https://c-cex.com/?id=api#getmarkethistory

        Args:
            market (str): Market name (ex: USD-BTC)
            count (int): Number of entries to return. Range 1-100, default is 50

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "Id": 1248410,
                "TimeStamp": "2015-12-28 20:44:45",
                "Quantity": 0.01355442,
                "Price": 441.00000000,
                "Total": 5.97750000,
                "FillType": "FILL",
                "OrderType": "BUY"
            }, {
                "Id": 1248409,
                "TimeStamp": "2015-12-28 20:44:45",
                "Quantity": 0.02500000,
                "Price": 440.90000000,
                "Total": 11.02250000,
                "FillType": "FILL",
                "OrderType": "BUY"
            }]

        """
        return self._public_call()

    def get_full_market_history(self, count=50):
        """
        Latest trades that have occured for all markets.

        See Also:
            https://c-cex.com/?id=api#getfullmarkethistory

        Args:
            count (:obj:`int`, optional): Number of entries to return. Range 1-100, default is 50

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "Market":"usd-yog",
                "Id": 1248410,
                "TimeStamp": "2015-12-28 20:44:45",
                "Quantity": 0.01355442,
                "Price": 441.00000000,
                "Total": 5.97750000,
                "FillType": "FILL",
                "OrderType": "BUY"
            }, {
                "Market":"usd-yog",
                "Id": 1248409,
                "TimeStamp": "2015-12-28 20:44:45",
                "Quantity": 0.02500000,
                "Price": 440.90000000,
                "Total": 11.02250000,
                "FillType": "FILL",
                "OrderType": "BUY"
            }]

        """
        return self._public_call()

    def get_balance_distribution(self, currency_name):
        """
        Exchange's wallet balance distribution for specific currency.

        See Also:
            https://c-cex.com/?id=api#getbalancedistribution

        Args:
            currency_name (str): Name of currency (ex: GRC)

        Returns:
            dict: various data about the market

        Example::

            {
                "Distribution": [
                    {"Balance": 622267.16657259},
                    {"Balance": 451260.06171487},
                    ...
                ]
            }

        """
        return self._public_call()


# noinspection PyUnusedLocal
class CCexAPIPrivate(CCexAPI):
    """
    Private endpoints
    """
    def __init__(self, api_key, api_secret):
        super(CCexAPIPrivate, self).__init__(api_key, api_secret)

    def _private_call(self):
        """
        Hackish way of not rewriting real call name and params ...
        They are extracted from the caller's function.
        """
        # noinspection PyProtectedMember
        caller = sys._getframe().f_back
        call = caller.f_code.co_name.replace('_', '')
        params = dict((k.replace('_', ''), v) for k, v in caller.f_locals.items() if k != 'self')

        return self._call(
            call=call,
            path='api.html',
            params=params,
            authenticated=True
        )

    def buy_limit(self, market, quantity, rate):
        """
        Place a buy limit order in a specific market. Make sure you have the proper permissions set on your API keys.

        See Also:
            https://c-cex.com/?id=api#buylimit

        Args:
            market (str): Market name (ex: USD-BTC)
            quantity (float): Amount to purchase
            rate (float): Rate at which to place the order

        Returns:
            str: uuid
        """
        return self._private_call().get('uuid')

    def sell_limit(self, market, quantity, rate):
        """
        Place a sell limit order in a specific market. Make sure you have the proper permissions set on your API keys.

        See Also:
            https://c-cex.com/?id=api#selllimit

        Args:
            market (str): Market name (ex: USD-BTC)
            quantity (float): Amount to purchase
            rate (float): Rate at which to place the order

        Returns:
            str: uuid
        """
        return self._private_call().get('uuid')

    def cancel(self, uuid):
        """
        Cancel a buy or sell order.

        See Also:
            https://c-cex.com/?id=api#cancel

        Args:
            uuid (str): uuid of buy or sell order
        """
        return self._private_call()

    def get_balance(self, currency):
        """
        Retrieve the balance from your account for a specific currency.

        See Also:
            https://c-cex.com/?id=api#getbalance

        Args:
            currency (str): Currency name (ex: BTC)

        Returns:
            dict: various data about the market

        Example::

            {
                "Currency" : "BTC",
                "Balance" : 20,
                "Available" : 3.78231923,
                "Pending" : 0.00000000,
                "CryptoAddress" : "1Euo2hfrw9cSWZGstPcRwDaHtcvL8iyJXP",
                "Requested" : false,
                "Uuid" : null
            }

        """
        return self._private_call()

    def get_balances(self):
        """
        Retrieve all balances from your account.

        See Also:
            https://c-cex.com/?id=api#getbalances

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "Currency": "USD",
                "Balance": 0.00000000,
                "Available": 0,
                "Pending": 0.00000000,
                "CryptoAddress": ""
            }, {
                "Currency": "BTC",
                "Balance": 53.04269984,
                "Available": 3.41248203,
                "Pending": 0.00000000,
                "CryptoAddress": "1Euo2hfrw9cSWZGstPcRwDaHtcvL8iyJXP"
            }, ... ]

        """
        return self._private_call()

    def get_order(self, uuid):
        """
        Retrieve a single order by uuid.

        See Also:
            https://c-cex.com/?id=api#getorder

        Args:
            uuid (str): uuid of buy or sell order

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "AccountId": null,
                "OrderUuid": "2137716",
                "Exchange": "NVC-BTC",
                "Type": "LIMIT_SELL",
                "Quantity": 228.70070713,
                "QuantityRemaining": 228.70070713,
                "Limit": 0.00289999,
                "Reserved": 228.70070713,
                "ReserveRemaining": 228.70070713,
                "CommissionReserved": 0.00000000,
                "CommissionReserveRemaining": 0.00000000,
                "CommissionPaid": 0.00000000,
                "Price": 0.00000000,
                "PricePerUnit": null,
                "Opened": "2015-12-28 23:20:04",
                "Closed": null,
                "IsOpen": true,
                "Sentinel": "2137716",
                "CancelInitiated": false,
                "ImmediateOrCancel": false,
                "IsConditional": false,
                "Condition": "NONE",
                "ConditionTarget": null
            }]

        """
        return self._private_call()

    def get_open_orders(self, market=None):
        """
        Get all orders that you currently have opened. A specific market can be requested.

        See Also:
            https://c-cex.com/?id=api#getopenorders

        Args:
            market (str): Market name (ex: USD-BTC)

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "Uuid": null,
                "OrderUuid": "2227714",
                "Exchange": "NVC-BTC",
                "OrderType": "LIMIT_SELL",
                "Quantity": 200,
                "QuantityRemaining": 200,
                "Limit": 0.00215000,
                "CommissionPaid": 0.00000000,
                "Price": 0.00000000,
                "PricePerUnit": null,
                "Opened": "2015-11-28 23:19:22",
                "Closed": null,
                "CancelInitiated": false,
                "ImmediateOrCancel": false,
                "IsConditional": false,
                "Condition": "NONE",
                "ConditionTarget": null
            }, {
                "Uuid": null,
                "OrderUuid": "2071587",
                "Exchange": "LTC-BTC",
                "OrderType": "LIMIT_BUY",
                "Quantity": 999.99999999,
                "QuantityRemaining": 999.99999999,
                "Limit": 0.00300000,
                "CommissionPaid": 0.00000000,
                "Price": 0.00000000,
                "PricePerUnit": null,
                "Opened": "2015-11-16 02:25:29",
                "Closed": null,
                "CancelInitiated": false,
                "ImmediateOrCancel": false,
                "IsConditional": false,
                "Condition": "NONE",
                "ConditionTarget": null
            }, ... ]

        """
        return self._private_call()

    def get_order_history(self, market=None, count=None):
        """
        Retrieve your order history.

        See Also:
            https://c-cex.com/?id=api#getorderhistory

        Args:
            market (str): Market name (ex: USD-BTC). If ommited, will return for all markets
            count (int): Number of records to return

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "OrderUuid": "2228451",
                "Exchange": "GRC-BTC",
                "TimeStamp": "2015-11-29 01:55:54",
                "OrderType": "LIMIT_BUY",
                "Limit": 0.00002096,
                "Quantity": 0.00020960,
                "QuantityRemaining": 0.00000000,
                "Commission": 0.00000042,
                "Price": 0,
                "PricePerUnit": 0.00002096,
                "IsConditional": false,
                "Condition": null,
                "ConditionTarget": null,
                "ImmediateOrCancel": false
            }, {
                "OrderUuid": "2202320",
                "Exchange": "BTC-DASH",
                "TimeStamp": "2015-11-25 11:06:23",
                "OrderType": "LIMIT_SELL",
                "Limit": 0.00630000,
                "Quantity": 183.48472577,
                "QuantityRemaining": 178.82359683,
                "Commission": 0.36696945,
                "Price": 1.15595377,
                "PricePerUnit": 0.00630000,
                "IsConditional": false,
                "Condition": null,
                "ConditionTarget": null,
                "ImmediateOrCancel": false
            }]

        """
        return self._private_call()

    def my_trades(self, market_id):
        """
        Retrieve detailed trading history.

        See Also:
            https://c-cex.com/?id=api#mytrades

        Args:
            market_id (str): Market name (ex: GRC-BTC)

        Returns:
            list(dict): various data about the market

        Example::

            [{
                "tradeid": "248725grc",
                "tradetype": "Sell",
                "datetime": "2015-10-28 03:18:29",
                "marketid": "GRC-BTC",
                "tradeprice": "0.00002900",
                "quantity": "30000.00000000",
                "fee": "0.00174000",
                "total": "0.87000000",
                "initiate_ordertype": "Buy",
                "order_id": "7324857"
            }, {
                "tradeid": "248724grc",
                "tradetype": "Sell",
                "datetime": "2015-10-28 03:18:20",
                "marketid": "GRC-BTC",
                "tradeprice": "0.00002900",
                "quantity": "20000.00000000",
                "fee": "0.00116000",
                "total": "0.58000000",
                "initiate_ordertype": "Buy",
                "order_id": "7324856"
            }]
        """
        return self._private_call()


__all__ = [CCexAPI, CCexAPITickers, CCexAPIPublic, CCexAPIPrivate,
       CCexAPIError, CCexAPIRequestError, CCexAPIResponseError, CCexAPIResponseFormatError]