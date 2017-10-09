CCEX Python Wrapper
===================

Client for CCex API written in Python Currently supports all
ticker/public/private endpoints.

Installation
------------

Via pip:

    pip install ccex_api

Usage
-----

    ccex = CCexAPI()
    ccex.tickers.tickers_coinnames()
    ccex.public.get_market_summaries()

    # credentials are required for private endpoints access
    ccex = CCexAPI('api_key', 'api_secret')
    ccex.private.get_balances()

Offer a coffee or a beer
------------------------

If you enjoyed this free software, and want to thank me, you can offer
me something for a coffee, a beer, or more, I would be happy :)

| Bitcoin : 13K5w1SXX7HTiKKQ1tQPerBKw1V6i65rsA
| Ethereum : 0x2e693665b99d0b631c60ae0b9b7735d43c27e9cb
| Dash : XwuAZapWHt5VU86ZBb5N2SDHK3t9XJUtGu
| Doge : DDf9jQkC17vWJkG6VsKPLo2oTnw4qY8XWd