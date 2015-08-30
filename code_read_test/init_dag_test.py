#coding:utf8
'''
 测试jieba __init__文件
'''

import os
import logging
import marshal
import re
from math import log

import jieba



_get_abs_path = lambda path: os.path.normpath(os.path.join(os.getcwd(), path))

DEFAULT_DICT = _get_abs_path("dict.txt")
re_eng = re.compile('[a-zA-Z0-9]', re.U)

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

    #动态规划，计算最大概率的切分组合
    def calc(self, sentence, DAG, route):
        N = len(sentence)
        route[N] = (0, 0)
         # 对概率值取对数之后的结果(可以让概率相乘的计算变成对数相加,防止相乘造成下溢)
        logtotal = log(self.total)
        # 从后往前遍历句子 反向计算最大概率
        for idx in xrange(N - 1, -1, -1):
           # 列表推到求最大概率对数路径
           # route[idx] = max([ (概率对数，词语末字位置) for x in DAG[idx] ])
           # 以idx:(概率对数最大值，词语末字位置)键值对形式保存在route中
           # route[x+1][0] 表示 词路径[x+1,N-1]的最大概率对数,
           # [x+1][0]即表示取句子x+1位置对应元组(概率对数，词语末字位置)的概率对数
            route[idx] = max((log(self.FREQ.get(sentence[idx:x + 1]) or 1) -
                              logtotal + route[x + 1][0], x) for x in DAG[idx])
                                                      
    # DAG中是以{key:list,...}的字典结构存储
    # key是字的开始位置
    
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

    def cut_DAG_NO_HMM(self, sentence):
        DAG = self.get_DAG(sentence)
        route = {}
        self.calc(sentence, DAG, route)
        x = 0
        N = len(sentence)
        buf = ''
        while x < N:
            y = route[x][1] + 1 
            l_word = sentence[x:y]# 得到以x位置起点的最大概率切分词语
            if re_eng.match(l_word) and len(l_word) == 1:#数字,字母
                buf += l_word
                x = y
            else:
                if buf:
                    yield buf
                    buf = ''
                yield l_word
                x = y
        if buf:
            yield buf
            buf = ''
            

if __name__ == '__main__':
    s = u'去北京大学玩'
    t = Tokenizer()
    dag = t.get_DAG(s)
    
    print 'DAG:'
    for d in dag:
        print d, ':', dag[d]
    route = {}
    t.calc(s, dag, route)
    print 'route:'
    print route
    
    print('/'.join(t.cut_DAG_NO_HMM(u'优衣库视频')))
