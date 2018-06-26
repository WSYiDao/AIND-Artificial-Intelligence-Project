import math
import statistics
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM
from sklearn.model_selection import KFold
from asl_utils import combine_sequences


class ModelSelector(object):
    '''
    base class for model selection (strategy design pattern)
    '''

    def __init__(self, all_word_sequences: dict, all_word_Xlengths: dict, this_word: str,
                 n_constant=3,
                 min_n_components=2, max_n_components=10,
                 random_state=14, verbose=False):
        self.words = all_word_sequences
        self.hwords = all_word_Xlengths
        self.sequences = all_word_sequences[this_word]
        self.X, self.lengths = all_word_Xlengths[this_word]
        self.this_word = this_word
        self.n_constant = n_constant
        self.min_n_components = min_n_components
        self.max_n_components = max_n_components
        self.random_state = random_state
        self.verbose = verbose

    def select(self):
        raise NotImplementedError

    def base_model(self, num_states):
        # with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                    random_state=self.random_state, verbose=False).fit(self.X, self.lengths)
            if self.verbose:
                print("model created for {} with {} states".format(self.this_word, num_states))
            return hmm_model
        except:
            if self.verbose:
                print("failure on {} with {} states".format(self.this_word, num_states))
            return None


class SelectorConstant(ModelSelector):
    """ select the model with value self.n_constant

    """

    def select(self):
        """ select based on n_constant value

        :return: GaussianHMM object
        """
        best_num_components = self.n_constant
        return self.base_model(best_num_components)
        

class SelectorBIC(ModelSelector):
    """ select the model with the lowest Bayesian Information Criterion(BIC) score

    http://www2.imm.dtu.dk/courses/02433/doc/ch6_slides.pdf
    Bayesian information criteria: BIC = -2 * logL + p * logN
    """

    def select(self):
        """ select the best model for self.this_word based on
        BIC score for n between self.min_n_components and self.max_n_components

        :return: GaussianHMM object

        "Free parameters" are parameters that are learned by the model and it is a sum of:
        1. The free transition probability parameters, which is the size of the transmat matrix less one row because they add up to 1 and therefore the final row is deterministic, so `n*(n-1)`
        2. The free starting probabilities, which is the size of startprob minus 1 because it adds to 1.0 and last one can be calculated so `n-1`
        3. Number of means, which is `n*f`
        4. Number of covariances which is the size of the covars matrix, which for "diag" is `n*f`
        """

        warnings.filterwarnings("ignore", category=DeprecationWarning)
        min_bic = None
        best_model = None
        
        for num_states in range(self.min_n_components,self.max_n_components + 1):
            try:
                hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                                            random_state=self.random_state, verbose=False).fit(self.X,self.lengths)
                logL = hmm_model.score(self.X,self.lengths)
                logN = math.log(len(self.X))
                # n*(n-1) + (n-1) + n*f + n*f ---> n^2 + 2*n*f - 1 
                f = len(self.X[0])
                p = num_states**2 + 2*f*num_states - 1
                BIC = -2 * logL + p * logN
                if (min_bic == None or min_bic > BIC):
                    min_bic = BIC
                    best_model = hmm_model
            except:
                continue
        return best_model

class SelectorDIC(ModelSelector):
    ''' select best model based on Discriminative Information Criterion

    Biem, Alain. "A model selection criterion for classification: Application to hmm topology optimization."
    Document Analysis and Recognition, 2003. Proceedings. Seventh International Conference on. IEEE, 2003.
    http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.58.6208&rep=rep1&type=pdf
    https://pdfs.semanticscholar.org/ed3d/7c4a5f607201f3848d4c02dd9ba17c791fc2.pdf
    DIC = log(P(X(i)) - 1/(M-1)SUM(log(P(X(all but i))
    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        word_sequences = self.sequences
        all_words = self.words.keys()
        M = len(all_words)
        max_DIC = None
        best_model = None
        for num_states in range(self.min_n_components,self.max_n_components + 1):
            try:
                hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                        random_state=self.random_state, verbose=False).fit(self.X,self.lengths)
                logI = hmm_model.score(self.X,self.lengths)
                for word in all_words:
                    sum_scores = 0.0
                    if word != self.this_word:
                        X,lengths = self.hwords[word]
                        sum_scores += hmm_model.score(X,lengths)
                    DIC = logI + 1.0/(M-1)*sum_scores
                if(max_DIC == None or max_DIC < DIC):
                    max_DIC =DIC
                    best_model = hmm_model
            except:
                continue
        return best_model

class SelectorCV(ModelSelector):
    ''' select best model based on average log Likelihood of cross-validation folds

    '''
    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        word_sequences = self.sequences
        split_method = KFold(n_splits = max(2,min(5,len(word_sequences))))
        max_score = None
        best_model = None
        for num_states in range(self.min_n_components,self.max_n_components + 1):
            try:
                scores_list = []
                for cv_train_idx, cv_test_idx in split_method.split(word_sequences):
                    train_data, train_length = combine_sequences(cv_train_idx,word_sequences)
                    test_data , test_length  = combine_sequences(cv_test_idx,word_sequences)
                    hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                            random_state=self.random_state, verbose=False).fit(train_data,train_length)
                    score = hmm_model.score(test_data,test_length)
                    scores_list.append(score)
                tmp_score = np.mean(scores_list)
                if(max_score == None or tmp_score > max_score):
                    max_score = tmp_score
                    best_model = hmm_model
            except:
                continue
        return best_model
