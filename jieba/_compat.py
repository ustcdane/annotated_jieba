# -*- coding: utf-8 -*-
import sys

# 获得安装的Python的版本信息
PY2 = sys.version_info[0] == 2 # python 2.x

default_encoding = sys.getfilesystemencoding()

if PY2:
    text_type = unicode
    string_types = (str, unicode)

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

else:# 在Python3.x,所有的字符串都是使用Unicode编码的字符序列
    text_type = str
    string_types = (str,)
    xrange = range

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

# 字符串解码为Unicode
def strdecode(sentence):
    if not isinstance(sentence, text_type):# 非Unicode
        try:
            sentence = sentence.decode('utf-8')# utf-8解码为Unicode
        except UnicodeDecodeError:# UnicodeDecodeError则用gbk解码为Unicode
            sentence = sentence.decode('gbk', 'ignore')# 设置为ignore，则会忽略非法字符
    return sentence
