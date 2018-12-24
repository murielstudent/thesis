
import numpy as np

from utils import *

def now_or_never(futures, reduce_risk=0.9, order_method = 'market_order', transaction_cost=0.0):

    """
    This strategy buys now when profit can be made, it does not wait for better oppertunities
    """

    reduce_risk = np.min([1., reduce_risk]) # should be between 0 and 1
    print(reduce_risk)
    print(order_method)
    bah

    current_price = futures[0][0]
    # expectation of the maximum best deal 
    best_deal  = np.mean([np.max(future[1:])-future[0] for future in futures])
    selling_price = best_deal+current_price
    if best_deal > (transaction_cost*current_price + transaction_cost*selling_price):
        # case of one sample need special treatment
        if np.shape(futures)[0] == 1:
            return [('buy', current_price, 0), 
                ('sell', selling_price, np.argmax(futures[0][1:])+1)]
        # find best selling moment = where most futures are within this region
        T = len(futures[0])
        time_slices = [[future[t] for future in futures] for t in range(1,T)]
        F = [ECDF(time_slice, [selling_price]) for time_slice in time_slices]
        score = [1. - f for f in F]

        # penalize for fat tail if you like
        if reduce_risk>0 and order_method=='market_order':
            beta = reduce_risk*np.min(score)/10.
            # low shortfall is bad since this means low selling price
            penalty = [beta/expected_shortfall(time_slice) for time_slice in time_slices]
            score = [score[i] - penalty[i] for i in range(len(penalty))]

        elif reduce_risk>0 and order_method == 'limit_order':
            penalty = [expected_shortfall(time_slice) for time_slice in time_slices]
            adjusted_selling_price = ((1-reduce_risk)*selling_price) + (reduce_risk*penalty[selling_moment-1])
            print('selling_price:', selling_price, ' adjusted_selling_price: ', adjusted_selling_price)
            selling_price = adjusted_selling_price
            best_deal = selling_price-current_price
            if best_deal <= (transaction_cost*current_price + transaction_cost*selling_price):
                return None

        score = np.asmatrix(score)
        selling_moment = np.argmax(score[1:]) + 1

        return [('buy', current_price, 0), 
                ('sell', selling_price, selling_moment)]
    else:
        return None

def if_you_do_it_do_it_good(futures, reduce_risk=False, format='price', transaction_cost=0.0):

    """
    This strategy buys now only when this is the best buy moment given the futures
    if the future indicate better buy moments, it does nothing
    """

    current_price = futures[0][0]
    T = len(futures[0]) # time
    best_deals, best_buys, best_sells, buy_moments = [],[],[],[]
    for future in futures:
        # for each optional buy moment, find best selling moment
        options = [(np.max(future[i+1:]), future[i], np.max(future[i+1:])-future[i], i) for i in range(T-1)]
        # select the best combination
        winner = max(options,key=lambda item:item[2])
        best_deals.append(winner[2])
        best_buys.append(winner[1])
        best_sells.append(winner[0])
        buy_moments.append(winner[3])

    buying_price = np.mean(best_buys)
    selling_price = np.mean(best_sells)
    best_deal = np.mean(best_deals)
    # make sure you buy before all selling oppertunities are gone
    buy_before = np.max(buy_moments)
    # take into account the transaction costs
    if best_deal > (transaction_cost*buying_price + transaction_cost*selling_price):
        # one sample need special treatment
        if np.shape(futures)[0] == 1:
            return [('buy', buying_price, buy_before), 
                ('sell', selling_price, np.argmax(futures[0][buy_before:])+buy_before)]
        # find best selling moment = were most futures are within this region
        time_slices = [[future[t] for future in futures] for t in range(1,T)]
        F_buy = [ECDF(time_slice, [buying_price]) for time_slice in time_slices]
        score_buy = F_buy/np.sum(F_buy)
        buying_moment = np.argmin(F_buy[:buy_before+1])
        F_sell = [ECDF(time_slice, [selling_price]) for time_slice in time_slices]
        F_sell = F_sell/np.sum(F_sell)
        score_sell = [1. - f for f in F_sell]

        # penalize for fat tail if you like
        if reduce_risk and order_method=='market_order':
            beta = np.min(score_sell)/100.
            penalty = [beta/expected_shortfall(time_slice) for time_slice in time_slices]
            score_sell = [score_sell[i] - penalty[i] for i in range(len(penalty))]
        
        elif reduce_risk and order_method == 'limit_order':
            penalty = [expected_shortfall(time_slice) for time_slice in time_slices]
            adjusted_selling_price = (0.9*selling_price) + (0.1*penalty[selling_moment-1])
            print('selling_price:', selling_price, ' adjusted_selling_price: ', adjusted_selling_price)
            selling_price = adjusted_selling_price
            best_deal = adjusted_selling_price-current_price
            if best_deal <= (transaction_cost*buying_price + transaction_cost*selling_price):
                return None

        score_sell = np.asmatrix(score_sell)
        selling_moment = buying_moment + (np.argmax(score_sell[buying_moment+1:])+1)
        return [('buy', buying_price, buying_moment), 
                ('sell', selling_price, selling_moment)]
    else:
        return None


