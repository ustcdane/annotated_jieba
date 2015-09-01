from __future__ import absolute_import, unicode_literals
import re
import os
import marshal
import sys
from .._compat import *

MIN_FLOAT = -3.14e100

PROB_START_P = "prob_start.p" 
PROB_TRANS_P = "prob_trans.p"
PROB_EMIT_P = "prob_emit.p"

'''
StatusSet: 
状态值(隐状态)集合有4种，分别是B,M,E,S，对应于一个汉字在词语中的地位即B（开头）,
M（中间 ),E（结尾）,S（独立成词）

ObservedSet:
观察值集合,即汉字
'''

#状态转移集合，比如B状态前只可能是E或S状态
PrevStatus = {
    'B': 'ES',
    'M': 'MB',
    'S': 'SE',
    'E': 'BM'
}


def load_model():
    _curpath = os.path.normpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))

    start_p = {} # 初始状态分布
    abs_path = os.path.join(_curpath, PROB_START_P)
    with open(abs_path, 'rb') as f:
        start_p = marshal.load(f)

    trans_p = {} # 转移概率
    abs_path = os.path.join(_curpath, PROB_TRANS_P)
    with open(abs_path, 'rb') as f:
        trans_p = marshal.load(f)

    emit_p = {} # 发射概率
    abs_path = os.path.join(_curpath, PROB_EMIT_P)
    with open(abs_path, 'rb') as f:
        emit_p = marshal.load(f) 

    return start_p, trans_p, emit_p

if sys.platform.startswith("java"):
    start_P, trans_P, emit_P = load_model()
else:
    from .prob_start import P as start_P
    from .prob_trans import P as trans_P
    from .prob_emit import P as emit_P

'''
HMM在实际应用中主要用来解决3类问题:
1. 评估问题(概率计算问题)
   即给定观测序列 O=O1,O2,O3…Ot和模型参数λ=(A,B,π)，怎样有效计算这一观测序列出现的概率.
   (Forward-backward算法)

 2. 解码问题(预测问题)
   即给定观测序列 O=O1,O2,O3…Ot和模型参数λ=(A,B,π)，怎样寻找满足这种观察序列意义上最优的隐含状态序列S。
   (viterbi算法,近似算法)

 3. 学习问题
 即HMM的模型参数λ=(A,B,π)未知，如何求出这3个参数以使观测序列O=O1,O2,O3…Ot的概率尽可能的大.
 (即用极大似然估计的方法估计参数,Baum-Welch,EM算法)
'''

# HMM模型中文分词中，我们的输入是一个句子(也就是观察值序列)，输出是这个句子中每个字的状态值

# HMM的解码问题
def viterbi(obs, states, start_p, trans_p, emit_p):
    V = [{}]  # 状态概率矩阵  
    path = {}
    for y in states:  # 初始化状态概率
        V[0][y] = start_p[y] + emit_p[y].get(obs[0], MIN_FLOAT)
        path[y] = [y] # 记录路径
    for t in xrange(1, len(obs)):
        V.append({})
        newpath = {}
        for y in states:
            em_p = emit_p[y].get(obs[t], MIN_FLOAT)
            # t时刻状态为y的最大概率(从t-1时刻中选择到达时刻t且状态为y的状态y0)
            (prob, state) = max([(V[t - 1][y0] + trans_p[y0].get(y, MIN_FLOAT) + em_p, y0) for y0 in PrevStatus[y]])
            V[t][y] = prob
            newpath[y] = path[state] + [y] # 只保存概率最大的一种路径 
        path = newpath 
    # 求出最后一个字哪一种状态的对应概率最大，最后一个字只可能是两种情况：E(结尾)和S(独立词)  
    (prob, state) = max((V[len(obs) - 1][y], y) for y in 'ES')

    return (prob, path[state])

# 利用 viterbi算法得到句子分词的生成器
def __cut(sentence):
    global emit_P
    # viterbi算法得到sentence 的切分
    prob, pos_list = viterbi(sentence, 'BMES', start_P, trans_P, emit_P)
    begin, nexti = 0, 0
    # print pos_list, sentence
    for i, char in enumerate(sentence):
        pos = pos_list[i]
        if pos == 'B':
            begin = i
        elif pos == 'E':
            yield sentence[begin:i + 1]
            nexti = i + 1
        elif pos == 'S':
            yield char
            nexti = i + 1
    if nexti < len(sentence):
        yield sentence[nexti:]

re_han = re.compile("([\u4E00-\u9FA5]+)")# 匹配中文的正则
re_skip = re.compile("(\d+\.\d+|[a-zA-Z0-9]+)")# 匹配数字(包含小数)或字母数字


def cut(sentence):
    sentence = strdecode(sentence)
    blocks = re_han.split(sentence)
    for blk in blocks:
        if re_han.match(blk): # 汉语块
            for word in __cut(blk):# 调用HMM切分
                yield word
        else:
            tmp = re_skip.split(blk)
            for x in tmp:
                if x:
                    yield x
