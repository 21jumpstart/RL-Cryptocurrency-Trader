# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 23:53:12 2018

@author: Julius
"""

from tensorforce.environments import Environment
import numpy as np
from products import update_hourly, get_relevent_ids, normalize

class Coinbase(Environment):
    def __init__(self):
        ids = get_relevent_ids()
        product = ids[0]
        df = update_hourly(product)
        norm_data = normalize(df)
        norm_data.iloc[::-1]

        self._prices = norm_data['close'].values
        self._observations = np.nan_to_num(norm_data.values[:,-6:])
        
        self._total_steps = len(norm_data)
        
        self._starting_balance = 1000
        self._usd = self._starting_balance
        self._btc = 0

        self._evaluation = self._starting_balance
        
        self._set_beginning_state()
        
    
    def __str__(self):
        return str({'balance': {'usd': self._usd, 'btc': self._btc}, 'price': self._current_price})

    def close(self):
        """
        Close environment. No other method calls possible afterwards.
        """
        pass

    def seed(self, seed):
        """
        Sets the random seed of the environment to the given value (current time, if seed=None).
        Naturally deterministic Environments (e.g. ALE or some gym Envs) don't have to implement this method.
        Args:
            seed (int): The seed to use for initializing the pseudo-random number generator (default=epoch time in sec).
        Returns: The actual seed (int) used OR None if Environment did not override this method (no seeding supported).
        """
        return None

    def reset(self):
        """
        Reset environment and setup for new episode.
        Returns:
            initial state of reset environment.
        """
        
        ids = get_relevent_ids()
        product = ids[0]
        df = update_hourly(product)
        norm_data = normalize(df)
        norm_data.iloc[::-1]

        self._prices = norm_data['close'].values
        self._observations = np.nan_to_num(norm_data.values[:,-6:])
        
        self._total_steps = len(norm_data)
        
        self._usd = self._starting_balance
        self._btc = 0

        self._evaluation = self._starting_balance
        
        self._set_beginning_state()
        
        return self._current_state

    def _take_action(self, action):
        '''
        Buy or sell based on how much you want the portfolio to be in BTC
        '''
        self._step += 1
        trade = action['trade']
        percentage = action['percentage']
        if trade:
            worth_in_btc = self._usd / self._current_price + self._btc
            percent_btc = self._btc / worth_in_btc
            percent_change = percentage - percent_btc
            amount_change = percent_change * worth_in_btc
            self._trade_btc(amount_change)
        
    def _trade_btc(self, amount):
        '''
        Buys or sells an amount worth of BTC
        '''
        price = amount * self._current_price
        fee = 0.005
        if False:
            fee = 0
        deduction = 1 - fee
        if amount > 0:
            self._usd = self._usd - price
            self._btc = self._btc + amount * deduction
        else:
            self._usd = self._usd - price * deduction
            self._btc = self._btc + amount
        
    def _set_beginning_state(self):
        self._step = np.random.randint(0,self._total_steps-1)
    
    @property
    def _done(self):
        if self._evaluation < self._starting_balance/2:
            return True
        if self._evaluation > self._starting_balance*2:
            return True
        if self._step < self._total_steps-1:
            return False
        return True
    
    @property
    def _current_price(self):
        return self._prices[self._step]
    
    @property
    def _current_state(self):
        return self._observations[self._step]
    
    def _get_reward(self):
        prev = self._evaluation
        self._evaluation = self._usd + self._btc * self._current_price
        reward = self._evaluation - prev
        return reward

    def execute(self, action):
        """
        Executes action, observes next state(s) and reward.
        Args:
            actions: Actions to execute.
        Returns:
            Tuple of (next state, bool indicating terminal, reward)
        """
        self._take_action(action)
        state = self._current_state
        done = self._done
        reward = self._get_reward()
        return (state, done, reward)
        

    @property
    def states(self):
        """
        Return the state space. Might include subdicts if multiple states are 
        available simultaneously.
        Returns:
            States specification, with the following attributes
                (required):
                - type: one of 'bool', 'int', 'float' (default: 'float').
                - shape: integer, or list/tuple of integers (required).
        """
        return dict(type='float', shape=6, min_value=0, max_value=1)

    @property
    def actions(self):
        """
        Return the action space. Might include subdicts if multiple actions are 
        available simultaneously.
        Returns:
            actions (spec, or dict of specs): Actions specification, with the following attributes
                (required):
                - type: one of 'bool', 'int', 'float' (required).
                - shape: integer, or list/tuple of integers (default: []).
                - num_actions: integer (required if type == 'int').
                - min_value and max_value: float (optional if type == 'float', default: none).
        """
        return dict(trade=dict(type='bool', shape=1), percentage = dict(type='float', min_value=0, max_value=1))
