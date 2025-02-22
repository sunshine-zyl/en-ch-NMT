# -*- coding: utf-8 -*-
"""
 @Time    : 2018/12/6 下午5:02
 @FileName: interface.py
 @author: 王炳宁
 @contact: wangbingning@sogou-inc.com
"""
import os

import torch
from werkzeug.serving import make_server
from werkzeug.wrappers import Request, Response
from jinja2 import *
import sentencepiece as spm

from model import GeneratorSelfAttention
from torchUtils import get_model, get_tensor_data

n_embedding = 512
n_hidden = 512
n_layer = 8
batch_size = 32
is_cuda = torch.cuda.is_available()
sp = spm.SentencePieceProcessor()
sp.load('total.uni.35000.model')
model = GeneratorSelfAttention(sp.GetPieceSize(), n_embedding, n_hidden, n_layer)
print('build done')
model.load_state_dict(
    get_model('model/model.trans.{}.{}.th'.format(n_hidden, n_layer)))
if is_cuda:
    model.cuda()
model.eval()
print('model loaded')


def trim(prediction):
    if sp.GetPieceSize() + 1 in prediction:
        end = prediction.index(sp.GetPieceSize() + 1)
    elif 0 in prediction:
        end = prediction.index(0)
    else:
        end = len(prediction)
    prediction = prediction[0:end]
    return prediction


def translate(sequence):
    sequence = sequence.strip()
    ids = sp.EncodeAsIds(sequence)
    ids = torch.LongTensor([ids[0:100]])
    if is_cuda:
        ids = ids.cuda()
    inputs = [None, ids]
    with torch.no_grad():
        prediction = model(inputs)
    output = get_tensor_data(prediction)
    prediction = trim(output[0].tolist())
    return sp.DecodeIds(prediction)


@Request.application
def application(request):
    url_path = request.path
    if url_path == '/translate':
        source = request.args['source']
        target = translate(source)
        translation_html_data = open('webservice/translate.html', 'r',
                                     encoding='utf-8').read()
        return Response(Template(translation_html_data).render(source=source, target=target), status='200 OK',
                        content_type='text/html')
    translation_html_data = open('webservice/index.html', 'rb').read()
    return Response(translation_html_data, status='200 OK', content_type='text/html')


if __name__ == '__main__':
    print("----------导入翻译文本并翻译----------")
    src_trgs = []
    with open("data/test_en.txt", "r") as fr:
        for line in fr.readlines():
            line = line.strip("\n").strip()
            trg = translate(line)
            src_trg = line + '\t' + trg + '\n'
            src_trgs.append(src_trg)
    print("----------f翻译条数：%d"%len(src_trgs)----------)
    print("----------结束翻译，保存翻译结果到txt文件中----------")
    with open("data/pre_en-zh.txt", "w") as fw:
        fw.writelines(src_trgs)
    print("----------成功保存，结束----------")
            
#     server = make_server('0.0.0.0', 4000, application, threaded=True)
#     server.serve_forever()
#     from werkzeug.serving import run_simple
#
#     run_simple('0.0.0.0', 4000, application)
