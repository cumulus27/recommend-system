#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The main operate of recommend system.
"""

import pymysql
import SetData
import random
from surprise import SVD
from surprise import SVDpp
from surprise import KNNBasic
from surprise import SlopeOne
from surprise import Dataset

from surprise import evaluate, print_perf
import os
from surprise import Reader
from collections import defaultdict


class DatasetUserDatabases(Dataset):
    """
    Get the data from mySQL.
    """
    def __init__(self,host,database,charset,reader=None):

        Dataset.__init__(self,reader)
        self.host = host
        self.database = database
        self.charset = charset
        self.n_folds = 5
        self.shuffle = True
        self.result = None
        self.raw_ratings = None

    def get_data(self,user, password, table):
        my_connect = SetData.GetData(self.host, self.database, self.charset)
        my_connect.connect(user, password)
        my_connect.select("SELECT * FROM {}".format(table))
        self.result=my_connect.result
#        print(self.result)

    def build_data(self, key):
#        print(self.result)
        self.raw_ratings=[self.parse_line(line, key) for line in self.result]
#        print(self.raw_ratings)

    @staticmethod
    def parse_line(line, key):
        keys=key.split(', ')
#        print(keys)
        ParseLine = (line.get(id) for id in keys)
#        for id in keys:
#            print(line.get(id))


#        user_id=line.get('user_id')
#        item_id=line.get('item_id')
#        rating=line.get('rating')
#        timestamp=line.get('timestamp')

#        user_id=line.get('student_id')
#        item_id=line.get('courses_id')
#        rating=line.get('trend')
#        timestamp=line.get('created')
#        print(rating)

        return ParseLine

    def build_full_trainset(self):
        """Do not split the dataset into folds and just return a trainset as
        is, built from the whole dataset.

        User can then query for predictions, as shown in the :ref:`User Guide
        <train_on_whole_trainset>`.

        Returns:
            The :class:`Trainset`.
        """

        return self.construct_trainset(self.raw_ratings)

    def raw_folds(self):

        if self.shuffle:
            random.shuffle(self.raw_ratings)
            self.shuffle = False  # set to false for future calls to raw_folds

        def k_folds(seq, n_folds):
            """Inspired from scikit learn KFold method."""

            if n_folds > len(seq) or n_folds < 2:
                raise ValueError('Incorrect value for n_folds.')

            start, stop = 0, 0
            for fold_i in range(n_folds):
                start = stop
                stop += len(seq) // n_folds
                if fold_i < len(seq) % n_folds:
                    stop += 1
                yield seq[:start] + seq[stop:], seq[start:stop]

        return k_folds(self.raw_ratings, self.n_folds)

    def split(self, n_folds=5, shuffle=True):
        """Split the dataset into folds for future cross-validation.

        If you forget to call :meth:`split`, the dataset will be automatically
        shuffled and split for 5-folds cross-validation.

        You can obtain repeatable splits over your all your experiments by
        seeding the RNG: ::

            import random
            random.seed(my_seed)  # call this before you call split!

        Args:
            n_folds(:obj:`int`): The number of folds.
            shuffle(:obj:`bool`): Whether to shuffle ratings before splitting.
                If ``False``, folds will always be the same each time the
                experiment is run. Default is ``True``.
        """

        self.n_folds = n_folds
        self.shuffle = shuffle

def get_top_n(predictions, n=10):
    '''Return the top-N recommendation for each user from a set of predictions.

    Args:
        predictions(list of Prediction objects): The list of predictions, as
            returned by the test method of an algorithm.
        n(int): The number of recommendation to output for each user. Default
            is 10.

    Returns:
    A dict where keys are user (raw) ids and values are lists of tuples:
        [(raw item id, rating estimation), ...] of size n.
    '''

    # First map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n

if __name__ == '__main__':
#    reader = Reader(line_format='user item rating timestamp', sep='\t')
    reader = Reader(line_format='user item rating timestamp', sep='\t')
    data = DatasetUserDatabases('localhost','tictalk_db','utf8mb4',reader)

    data.get_data('py', '2151609', 'students_tutors')
    data.build_data('student_id, tutor_id, trend, created')

#    data.get_data('py','2151609','students_courses_tem')
#    data.build_data('student_id, course_id, trend, created')

#    data=DatasetUserDatabases('localhost','test','utf8mb4',reader)
#    data.get_data('py','2151609','u_data')
#    data.build_data('user_id, item_id, rating, timestamp')
    data.split(n_folds=5)

    trainset = data.build_full_trainset()
#    print(trainset)
#    algo = SVD()
    algo = SVDpp()
#    algo = KNNBasic()
#    algo = SlopeOne()
    algo.train(trainset)

    # Than predict ratings for all pairs (u, i) that are NOT in the training set.
    testset = trainset.build_anti_testset()
#    print(testset)
    predictions = algo.test(testset)

#    print(predictions)
    f=open('demo.txt','w')
    for i in predictions:
        k=str(i)
        f.write(k+"\n")
    f.close()


    top_n = get_top_n(predictions, n=10)

    # Print the recommended items for each user
    for uid, user_ratings in top_n.items():
        print(uid, [iid for (iid, _) in user_ratings])
#        print('ok')

    print('yes')


