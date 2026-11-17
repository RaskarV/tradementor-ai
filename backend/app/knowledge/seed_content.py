"""Starter curriculum: general concepts only, no market statistics and no live data.
Administrators should review it and add authoritative sources (SEBI, NSE, BSE education pages)."""

SEED_DOCS = {
"market-basics": """A stock is a small ownership share in a company. When many people want to buy a share, its price tends to rise; when many want to sell, it tends to fall. Prices are set continuously by buyers and sellers on an exchange.

In the primary market a company sells new shares for the first time, for example in an IPO. In the secondary market investors trade existing shares with each other. An index such as the Nifty 50 or the Sensex tracks a basket of large companies and is used as a rough gauge of the market.

Two order types matter first. A market order buys or sells immediately at the best available price. A limit order only trades at your chosen price or better, but may never be filled. Liquidity means how easily you can buy or sell without moving the price.""",
"nse-bse": """India has two major stock exchanges: the National Stock Exchange (NSE) and the Bombay Stock Exchange (BSE). The same company can often be traded on both. The NSE publishes the Nifty indices and the BSE publishes the Sensex.

The Securities and Exchange Board of India (SEBI) is the market regulator. Retail investors trade through a registered broker and need a demat account to hold shares electronically plus a trading account to place orders.

Trading hours, settlement cycles, margin rules and fees change over time. Always confirm current details on the official NSE, BSE and SEBI websites rather than relying on memory or a third-party summary.""",
"derivatives": """Derivatives are contracts whose value depends on an underlying asset such as a share or an index. The two common types are futures and options.

A futures contract is an obligation to buy or sell at a set price on a future date. Gains and losses build up daily and can be large relative to the money posted as margin.

An option gives the buyer the right, but not the obligation, to buy (a call) or sell (a put) at a strike price before expiry. The buyer pays a premium and can lose all of it. Option sellers receive the premium but can face very large losses. Contracts trade in fixed lot sizes and expire, so time works against option buyers. Leverage magnifies losses as well as gains, which is why derivatives are usually a poor place for a beginner to start.""",
"candlesticks": """A candlestick summarises price movement over one period such as a day. It shows four values: open, high, low and close. The thick part is the body, between open and close, and the thin lines are the wicks, showing the highest and lowest prices reached.

Named patterns such as a doji, hammer or engulfing candle describe how buyers and sellers behaved in that period. They are descriptions of the past, not predictions. The same pattern can lead to very different outcomes depending on where it appears, the trend before it, and volume. Treat a pattern as one clue to weigh, and plan what you will do if it turns out to be wrong.""",
"support-resistance": """Support is a price zone where falling prices have previously paused or turned up. Resistance is a zone where rising prices have previously stalled or turned down. They appear because many traders remember and react to the same prices.

They are zones, not exact lines, so drawing a thin line at one price gives false precision. The more often a zone has held, the more traders watch it, but a level that has held many times can still break. When price breaks through resistance, that area is often watched afterwards as possible support, and the reverse for broken support. None of this is certain; it is a way of organising where to look and where you would admit a trade idea was wrong.""",
"indicators": """Technical indicators are calculations on price and volume, such as moving averages, RSI and MACD. They turn raw prices into something easier to read, like trend direction or momentum.

Most indicators lag, because they are built from past data. Some measure trend, some momentum, some volatility, some volume. Using several indicators that measure the same thing adds clutter, not information. A sensible approach is to understand what one or two indicators actually calculate, test the idea on past charts, and be honest about how often it fails and how much a failure costs.""",
"moving-averages": """A moving average smooths price by averaging the last N periods, which makes the trend easier to see. A simple moving average (SMA) weights every period equally. An exponential moving average (EMA) weights recent prices more, so it reacts faster.

Traders often watch whether price is above or below a moving average to judge trend, or watch a fast average crossing a slow one. Because averages lag, crossovers tend to arrive after a move has started, and in sideways markets they produce repeated false signals, called whipsaws. Shorter averages react faster but give more false signals; longer ones are steadier but later.""",
"rsi-macd": """The Relative Strength Index (RSI) measures the speed of recent price changes on a scale from 0 to 100. By convention, readings above 70 are called overbought and below 30 oversold, but in a strong trend RSI can stay in those zones for a long time, so they are not automatic sell or buy signals.

MACD is built from two EMAs. The MACD line is the difference between a 12-period and a 26-period EMA in the usual settings, and the signal line is a 9-period EMA of that line. Crossovers and the distance between the lines are read as changes in momentum. Both tools lag price and can give false signals, so they work best as context alongside price structure and risk limits.""",
"stop-loss": """A stop-loss is a pre-decided exit price that limits how much a trade can cost you if it goes against you. Deciding it before entering removes the temptation to hope.

A useful stop is placed where your trade idea is proven wrong, such as beyond a recent swing low, not simply at a loss you would like to accept. A tighter stop is then paired with a smaller position, not the other way round. Stops are not perfect: prices can gap past them overnight and fast markets cause slippage, so the real loss can exceed the planned one. Moving a stop further away to avoid being stopped out defeats its purpose.""",
"position-sizing": """Position sizing decides how many units to trade so that a loss, if your stop-loss is hit, stays within an amount you chose in advance.

Risk amount = account capital x risk percentage / 100. Risk per unit = the distance between entry and stop-loss. Quantity = risk amount / risk per unit.

Example for learning: with capital of Rs 50,000 and a chosen risk of 2%, the risk amount is Rs 1,000. If the entry is Rs 500 and the stop-loss is Rs 490, the risk per share is Rs 10, so the quantity is 100 shares. This is the maximum theoretical loss before brokerage, taxes and slippage. A calculated quantity does not make a trade safe, because gaps and costs can make the actual loss larger.""",
"risk-reward": """The risk-to-reward ratio compares what you stand to lose with what you hope to gain. If you risk Rs 10 per share to the stop-loss and the target is Rs 20 above entry, the reward-to-risk is 2 to 1.

The ratio only matters together with how often trades succeed. The break-even win rate before costs is 1 divided by (1 plus the reward-to-risk ratio). At 2 to 1 that is about one winning trade in three; at 1 to 1 it is one in two. Costs raise those thresholds. A high ratio on a target that is rarely reached is not an advantage, so targets should come from the chart, not from the ratio you wish for.""",
"diversification": """Diversification means spreading money across different investments so that one bad outcome does not damage the whole portfolio. The idea works best when holdings do not move together, for example different sectors, asset types or company sizes.

It reduces the risk tied to a single company or sector, but it does not remove market-wide risk, because many assets can fall at the same time. Holding ten stocks in the same sector is concentration, not diversification. Spreading too thinly also makes a portfolio hard to follow. Diversification is a risk-management tool, not a way to avoid losses.""",
"psychology": """Most trading errors are behavioural. Fear makes people exit good trades too early, greed makes them hold or oversize, and fear of missing out pushes them into chasing moves. After a loss, revenge trading tries to win the money back quickly, usually with bigger positions. After a run of wins, overconfidence leads to ignoring rules.

Practical defences are simple: write a trading plan with entry, stop-loss and position size before you trade; keep a journal of what you did and why; set a daily loss limit and stop when you hit it; and take breaks after emotional trades. Rules written in calm moments protect you in stressful ones.""",
"beginner-mistakes": """Common beginner mistakes include trading without a written plan, risking too much on one trade, skipping the stop-loss, and following tips from groups without understanding the reasoning. Others are using leverage too early, adding to losing positions in the hope of recovery, trading too often, and ignoring brokerage, taxes and slippage that eat into small gains.

Many beginners also judge a strategy from a handful of trades, when only a larger sample says anything. A better start is to learn the concepts, practise on paper, then trade very small while you learn how you react to real losses.""",
"capital-preservation": """Capital preservation means protecting the money you have so that you can keep learning and trading. Losses are harder to recover than they look: after losing 50%, you need a gain of 100% just to get back to where you started.

That is why traders cap the loss on any one trade, often a small percentage of capital, and cap total losses per day or month. Staying in cash is also a position and a valid choice when you see no good setup. The first goal is to survive long enough to learn; returns come second.""",
"scams": """Many trading scams use the same patterns. A promise of guaranteed or fixed returns is a classic red flag, because no legitimate adviser can guarantee market results. Others are pressure to deposit quickly, paid tip or signal groups with screenshots of only winning trades, fake or cloned trading apps, people pretending to be from SEBI or a broker, and requests to share OTPs, passwords or screen access.

Before trusting an adviser, check that they appear on SEBI's official list of registered investment advisers and research analysts, and use only apps your broker officially provides. If you have been defrauded, report it quickly through the national cybercrime portal or helpline and to your bank, and consider a complaint on SEBI's SCORES platform. Confirm current contact details on the official sites.""",
}
