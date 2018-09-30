#!/usr/local/bin/env python
from __future__ import division
import numpy as np
from numpy import array
from numpy.random import sample as rs
from numpy import newaxis as na
import pandas as pd
from scipy.stats import sem
import seaborn as sns
import string
import matplotlib.pyplot as plt



def update_Qi(Qval, reward, alpha):
    return Qval + alpha * (reward - Qval)

def update_Pall(Qvector, beta):
    return np.array([np.exp(beta*Q_i) / np.sum(np.exp(beta * Qvector)) for Q_i in Qvector])


class MultiArmedBandit(object):
    """ defines a multi-armed bandit task

    ::Arguments::
        preward (list): 1xN vector of reward probaiblities for each of N bandits
        rvalues (list): 1xN vector of payout values for each of N bandits
    """
    def __init__(self, preward=[.8, .5, .2, .9], rvalues=[2, 1, 1, .5]):
        self.preward = preward
        self.rvalues = rvalues

    def get_feedback(self, action_ix):
        pOutcomes = np.array([self.preward[action_ix], 1-self.preward[action_ix]])
        Outcomes = np.array([self.rvalues[action_ix], 0])
        feedback = np.random.choice(Outcomes, p=pOutcomes)
        return feedback


class Qagent(object):
    """ defines the learning parameters of single q-learning agent
    in a multi-armed bandit task

    ::Arguments::
        alpha (float): learning rate
        beta (float): inverse temperature parameter
        preward (list): 1xN vector of reward probaiblities for each of N bandits
        rvalues (list): 1xN vector of payout values for each of N bandits

    """
    def __init__(self, alpha=.1, beta=.15, epsilon=.1, preward=[.8, .5, .2, .9],
                 rvalues=[2, 1, 1, .5]):

        self.bandits = MultiArmedBandit(preward=preward, rvalues=rvalues)
        self.updateQ = lambda Qval, r, alpha: Qval + alpha*(r - Qval)
        self.updateP = lambda Qvector, act_i, beta: np.exp(beta*Qvector[act_i])/np.sum(np.exp(beta*Qvector))
        self.nact = len(preward)
        self.actions = np.arange(self.nact)
        self.alpha = alpha
        self.beta = beta
        self.epsilon = epsilon


    def play_bandits(self, ntrials=1000, get_output=False):

        pdata = np.zeros((ntrials+1, self.nact))
        pdata[0, :] = np.array([1/self.nact]*self.nact)
        qdata = np.zeros_like(pdata)
        actions = np.arange(self.nact)
        self.choices = []
        self.feedback = []

        for t in range(ntrials):

            # select bandit arm (action)
            act_i = np.random.choice(actions, p=pdata[t, :])

            # observe feedback
            r = self.bandits.get_feedback(act_i)

            # update value of selected action
            qdata[t+1, act_i] = update_Qi(qdata[t, act_i], r, self.alpha)

            # broadcast old values for unchosen actions
            for act_j in self.actions[np.where(self.actions!=act_i)]:
                qdata[t+1, act_j] = qdata[t, act_j]

            # update action selection probabilities and store data
            pdata[t+1, :] = update_Pall(qdata[t+1, :], self.beta)
            self.choices.append(act_i)
            self.feedback.append(r)

        self.pdata = pdata[1:, :]
        self.qdata = qdata[1:, :]
        self.make_output_df()

        if get_output:
            return self.data.copy()


    def make_output_df(self):
        df = pd.concat([pd.DataFrame(dat) for dat in [self.qdata, self.pdata]], axis=1)
        columns = np.hstack(([['{}{}'.format(x, c) for c in self.actions] for x in ['q', 'p']]))
        df.columns = columns
        df.insert(0, 'trial', np.arange(1, df.shape[0]+1))
        df['choice'] = self.choices
        df['feedback'] = self.feedback
        self.data = df.copy()


    def simulate_multiple_agents(self, nagents=10, ntrials=1000):
        dflist = []
        for i in range(nagents):
            # agent_i = Qagent(alpha=self.alpha, beta=self.beta, epsilon=self.epsilon, preward=self.preward, rvalues=self.rvalues)
            data_i = self.play_bandits(ntrials=ntrials, get_output=True)
            data_i.insert(0, 'agent', i+1)
            dflist.append(data_i)

        return pd.concat(dflist)


def simulate_multiple_agents(nagents=10, ntrials=1000, alpha=.1, beta=.15,
    epsilon=.1, preward=[.8, .5, .2, .9], rvalues=[2, 1, 1, .5]):

    dflist = []
    for i in range(nagents):
        agent_i = Qagent(alpha=alpha, beta=beta, epsilon=epsilon, preward=preward, rvalues=rvalues)
        data_i = agent_i.play_bandits(ntrials=ntrials, get_output=True)
        data_i.insert(0, 'agent', i+1)
        dflist.append(data_i)

    return pd.concat(dflist)