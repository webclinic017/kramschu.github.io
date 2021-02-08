from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Indicators")
AddReference("QuantConnect.Common")

from QuantConnect import *
from QuantConnect.Parameters import *
from QuantConnect.Benchmarks import *
from QuantConnect.Brokerages import *
from QuantConnect.Util import *
from QuantConnect.Interfaces import *
from QuantConnect.Algorithm import *
from QuantConnect.Algorithm.Framework import *
from QuantConnect.Algorithm.Framework.Selection import *
from QuantConnect.Algorithm.Framework.Alphas import *
from QuantConnect.Algorithm.Framework.Portfolio import *
from QuantConnect.Algorithm.Framework.Execution import *
from QuantConnect.Algorithm.Framework.Risk import *
from QuantConnect.Indicators import *
from QuantConnect.Data import *
from QuantConnect.Data.Consolidators import *
from QuantConnect.Data.Custom import *
from QuantConnect.Data.Fundamental import *
from QuantConnect.Data.Market import *
from QuantConnect.Data.UniverseSelection import *
from QuantConnect.Notifications import *
from QuantConnect.Orders import *
from QuantConnect.Orders.Fees import *
from QuantConnect.Orders.Fills import *
from QuantConnect.Orders.Slippage import *
from QuantConnect.Scheduling import *
from QuantConnect.Securities import *
from QuantConnect.Securities.Equity import *
from QuantConnect.Securities.Forex import *
from QuantConnect.Securities.Interfaces import *
from datetime import date, datetime, timedelta
from QuantConnect.Python import *
from QuantConnect.Storage import *
QCAlgorithmFramework = QCAlgorithm
QCAlgorithmFrameworkBridge = QCAlgorithm

VAR_CASH = 100000
START_YEAR = 2020
START_MONTH = 1
START_DAY = 1
END_YEAR = 2021
END_MONTH = 1
END_DAY = 1
BUY_TOL = .1
SELL_TOL = .05

class MomentumLeverage(QCAlgorithm):

    def Initialize(self):
        '''Initialise the data and resolution required, as well as the cash and start/end dates for your algorithm.
            All algorithms must initialized.
            In this case we manually set the universe, and in future releases we will determine
             the best performing asset to select.
             WIP -Kepe
           '''

        # Set Start Date
        self.SetStartDate(START_YEAR,START_MONTH,START_DAY)

        # Set End Date
        self.SetEndDate(END_YEAR, END_MONTH, END_DAY)

        # Set starting cash
        self.SetCash(VAR_CASH)

        # Define symbols
        self.NAS = "TQQQ"
        self.SPY = "UPRO"
        self.RUS = "TNA"
        self.DOW = "UDOW"

        # Initialize universe
        self.universe = [self.NAS, self.SPY, self.RUS, self.DOW]
        nas_data = self.AddEquity(self.NAS, Resolution.Daily)
        #nas_options = self.AddOption(self.NAS, Resolution.Daily)
        spy_data = self.AddEquity(self.SPY, Resolution.Daily)
        #spy_options = self.AddOption(self.SPY, Resolution.Daily)
        rus_data = self.AddEquity(self.RUS, Resolution.Daily)
        #rus_options = self.AddOption(self.RUS, Resolution.Daily)
        dow_data = self.AddEquity(self.DOW, Resolution.Daily)
        #dow_options = self.AddOption(self.DOW, Resolution.Daily)

        self.current = datetime.min

        self.window_NAS = RollingWindow[float](5)
        self.window_SPY = RollingWindow[float](5)
        self.window_RUS = RollingWindow[float](5)
        self.window_DOW = RollingWindow[float](5)


        # define our daily macd(12,26) with a 9 day signal for buy signals
        self.macd_NAS = self.MACD(self.NAS, 12, 26, 9, MovingAverageType.Exponential, Resolution.Daily)
        self.macd_SPY = self.MACD(self.SPY, 12, 26, 9, MovingAverageType.Exponential, Resolution.Daily)
        self.macd_RUS = self.MACD(self.RUS, 12, 26, 9, MovingAverageType.Exponential, Resolution.Daily)
        self.macd_DOW = self.MACD(self.DOW, 12, 26, 9, MovingAverageType.Exponential, Resolution.Daily)

    def OnData(self, data):
        '''OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.

        Arguments:
            data: Slice object keyed by symbol containing the stock data
        '''

        self.window_NAS.Add(self.Securities[self.NAS].Price)
        self.window_SPY.Add(self.Securities[self.SPY].Price)
        self.window_RUS.Add(self.Securities[self.RUS].Price)
        self.window_DOW.Add(self.Securities[self.DOW].Price)


        # if the Indicator Signals have enough data
        if self.Ready():

            # If the algorithm has a position
            if self.HavePosition() is True:

                # If risk management function returns True a sell order was made.
                if self.ManageRisk(SELL_TOL) is True: return

            # Else there is no position, we can check for a buy signal.
            else:

                # Position represents a ticker for a symbol with a buy signal. if the function returns None, there are no buy signals above threshold, so return.
                position = self.BuySignal()
                if position is None: return

                self.SetHoldings(position, .9)
                #self.BuyOptions(position)
                self.current = self.Time

    def BuySignal(self):
        buy_tolerance = BUY_TOL
        buy_universe = [0,0,0,0]

        buy_universe[0] = self.macd_NAS.Current.Value - self.macd_NAS.Signal.Current.Value
        buy_universe[1] = self.macd_SPY.Current.Value - self.macd_SPY.Signal.Current.Value
        buy_universe[2] = self.macd_RUS.Current.Value - self.macd_RUS.Signal.Current.Value
        buy_universe[3] = self.macd_DOW.Current.Value - self.macd_DOW.Signal.Current.Value

        if max(buy_universe) > buy_tolerance:
            pos = buy_universe.index(max(buy_universe))
            self.Debug(buy_universe)
            return self.universe[pos]

        return None

    def HavePosition(self):
        if self.Portfolio[self.NAS].Quantity > 0 or self.Portfolio[self.SPY].Quantity > 0 or self.Portfolio[self.RUS].Quantity > 0 or self.Portfolio[self.DOW].Quantity > 0:
            return True

        return False

    def Ready(self):

        if self.macd_NAS.IsReady and self.macd_SPY.IsReady and self.macd_RUS.IsReady and self.macd_DOW.IsReady:
            return True

        return False


    def BuyOptions(self, position):

        # Get the contracts for that symbol
        contracts = self.OptionChainProvider.GetOptionContractList(position, self.Time.date())

        # Return if there are no contracts found
        if len(contracts) == 0: return

        # Remove the calls leaving the puts in the chain
        put = [x for x in contracts if x.ID.OptionRight == 1]

        # sort the contracts according to their expiration dates and choose the ATM options
        contracts = sorted(sorted(put, key = lambda x: abs(self.Securities[position].Price - x.ID.StrikePrice - (.05*self.Securities[position].Price))),
        key = lambda x: x.ID.Date, reverse=True)

        # Get the atm contract with the nearest expiration
        self.contract = contracts[0]
        self.AddOptionContract(self.contract, Resolution.Daily)
        self.Buy(self.contract, 1)

    def ManageRisk(self, sell_tolerance):

        # if invested and momentum, liquidate

            if self.Portfolio[self.NAS].Quantity > 0:
                if self.macd_NAS.Current.Value < self.macd_NAS.Signal.Current.Value - sell_tolerance:
                    self.Liquidate(self.NAS)
                    return True

                elif (self.Time - self.current).days >= 5:
                    if self.Securities[self.NAS].Price < 1.05 * self.window_NAS[4]:
                        self.Liquidate(self.NAS)
                        return True

            elif self.Portfolio[self.SPY].Quantity > 0:
                if self.macd_SPY.Current.Value < self.macd_SPY.Signal.Current.Value - sell_tolerance:
                    self.Liquidate(self.SPY)
                    return True

                elif (self.Time - self.current).days >= 5:
                    if self.Securities[self.NAS].Price < 1.05 * self.window_NAS[4]:
                        self.Liquidate(self.NAS)
                        return True


            elif self.Portfolio[self.RUS].Quantity > 0:
                if self.macd_RUS.Current.Value < self.macd_RUS.Signal.Current.Value - sell_tolerance:
                    self.Liquidate(self.RUS)
                    return True

                elif (self.Time - self.current).days >= 5:
                    if self.Securities[self.NAS].Price < 1.05 * self.window_NAS[4]:
                        self.Liquidate(self.NAS)
                        return True

            elif self.Portfolio[self.DOW].Quantity > 0:
                if self.macd_DOW.Current.Value < self.macd_DOW.Signal.Current.Value - sell_tolerance:
                    self.Liquidate(self.DOW)
                    return True

                elif (self.Time - self.current).days >= 5:
                    if self.Securities[self.NAS].Price < 1.05 * self.window_NAS[4]:
                        self.Liquidate(self.NAS)
                        return True

            return False
