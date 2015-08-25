#coding:utf8
'''
 测试jieba __init__文件
'''

import os
import logging
import marshal
from math import log

_get_abs_path = lambda path: os.path.normpath(os.path.join(os.getcwd(), path))

DEFAULT_DICT = _get_abs_path("dict.txt")
#print DEFAULT_DICT

class Tokenizer(object):
    def __init__(self, dictionary=DEFAULT_DICT):
        self.dictionary = _get_abs_path(dictionary)
        self.FREQ = {}
        self.total = 0
        self.initialized = False
        self.cache_file = None
        
    def gen_pfdict(self, f_name):
        lfreq = {}
        ltotal = 0
        with open(f_name, 'rb') as f:
            for lineno, line in enumerate(f, 1):
                try:
                    line = line.strip().decode('utf-8')
                    word, freq = line.split(' ')[:2]
                    freq = int(freq)
                    lfreq[word] = freq
                    ltotal += freq
                    for ch in xrange(len(word)):
                        wfrag = word[:ch + 1]
                        if wfrag not in lfreq:
                            lfreq[wfrag] = 0
                except ValueError:
                    raise ValueError(
                        'invalid dictionary entry in %s at Line %s: %s' % (f_name, lineno, line))
        return lfreq, ltotal

    def check_initialized(self):
        if not self.initialized:
            abs_path = _get_abs_path(self.dictionary)
            if self.cache_file:
                cache_file = self.cache_file
            # 默认的cachefile
            elif abs_path:
                cache_file = "jieba.cache"

            load_from_cache_fail = True
            # cachefile 存在
            if os.path.isfile(cache_file):
                try:
                    with open(cache_file, 'rb') as cf:
                        self.FREQ, self.total = marshal.load(cf)
                    load_from_cache_fail = False
                except Exception:
                    load_from_cache_fail = True
            if load_from_cache_fail:
                self.FREQ, self.total = self.gen_pfdict(abs_path)
                #把dict前缀集合,总词频写入文件
                try:
                    with open(cache_file, 'w') as temp_cache_file:
                        marshal.dump((self.FREQ, self.total), temp_cache_file)
                except Exception:
                    #continue
                    pass
            # 标记初始化成功
            self.initialized = True

    def calc(self, sentence, DAG, route):
        N = len(sentence)
        route[N] = (0, 0)
        logtotal = log(self.total)
        #对概率值取对数之后的结果(可以让概率相乘的计算变成对数相加,防止相乘造成下溢)
        for idx in xrange(N - 1, -1, -1): 
            route[idx] = max((log(self.FREQ.get(sentence[idx:x + 1]) or 1) -
                              logtotal + route[x + 1][0], x) for x in DAG[idx])
    
    def get_DAG(self, sentence):
        self.check_initialized()
        DAG = {}
        N = len(sentence)
        for k in xrange(N):
            tmplist = []
            i = k
            frag = sentence[k]
            while i < N and frag in self.FREQ:
                if self.FREQ[frag]:
                    tmplist.append(i)
                i += 1
                frag = sentence[k:i + 1]
            if not tmplist:
                tmplist.append(k)
            DAG[k] = tmplist
        return DAG

if __name__ == '__main__':
    s = u'去北京大学玩'
    t = Tokenizer()
    dag = t.get_DAG(s)
    for d in dag:
        print d, dag
    route = {}
    t.calc(s, dag, route)
    print route
