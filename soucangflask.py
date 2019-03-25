from flask import Flask,render_template,request,make_response
from functools import wraps
from flask_cors import CORS
from apis import Page
import pymongo
import urllib
import json,re,time
import redis
import requests

from urllib import parse

from handlelog import Logger

# infologger = Logger('/mnt/data/soucangflask/all.log',level='info')
errorlogger = Logger('/mnt/logs/soucangflask/log/errorlog.log',level='error')
# errorlogger = Logger('/Users/zdp/test/soucang.log',level='error')

errortime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

def db():
    conn = pymongo.MongoClient(
        "mongodb://xhql:" + urllib.parse.quote_plus("xhql_190228_snv738J72*fjVNv8220aiVK9V820@_")+"@47.92.174.37:20388/webpage")['webpage']
    return conn

def redisdb():
    pool = redis.ConnectionPool(host='47.92.174.37', port=8991, db=1, password='28JCi*289V92ofj2owoBkv8282928SKVISmv8920565LjhMcs')
    connredis = redis.Redis(connection_pool=pool)
    return connredis

app = Flask(__name__)
CORS(app)

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p =1
    return p


@app.route('/')
def hello():
    conn = db()
    rdb = redisdb()
    #从连接中获取type信息
    wenzhangtype = request.args.get('class')
    #从reids中获取实体标签分类数量
    countentity = int(rdb.get('entity_count'))
    countlable = int(rdb.get('countlable'))
    counttype = int(rdb.get('counttype'))
    if wenzhangtype == 'baidujingyan':
        #获取文章总数
        num = conn.baidujingyan_details.find().count()
        #获取文章处理数
        dealnum = conn.baidujingyan_details.find({'sign':1}).count()
        #分页
        page_str = request.args.get('page')
        if not page_str:
            page_str = 1
        page_index = get_page_index(page_str)
        p = Page(num,page_index)
        classtype = 'baidujingyan'
        result = conn.baidujingyan_details.find().limit(p.limit).skip(p.offset).sort("release_date",-1)
    elif wenzhangtype == 'zhihu':
        num = conn.zhidao_details.find().count()
        dealnum = conn.zhidao_details.find({'sign': 1}).count()
        page_str = request.args.get('page')
        if not page_str:
            page_str = 1
        page_index = get_page_index(page_str)
        p = Page(num, page_index)
        classtype = 'zhihu'
        result = conn.zhidao_details.find().limit(p.limit).skip(p.offset).sort("release_date", -1)
    elif wenzhangtype == 'douban':
        num = conn.douban_details.find().count()
        dealnum = conn.douban_details.find({'sign': 1}).count()
        page_str = request.args.get('page')
        if not page_str:
            page_str = 1
        page_index = get_page_index(page_str)
        p = Page(num, page_index)
        classtype = 'douban'
        result = conn.douban_details.find().limit(p.limit).skip(p.offset).sort("release_date", -1)
    else:
        num = conn.web_detail.find().count()
        dealnum = conn.web_detail.find({'sign':1}).count()
        # num = conn.web_detail.find().count()
        # dealnum = conn.web_detail.find({'sign':1}).count()
        page_str = request.args.get('page')
        if not page_str:
            page_str = 1
        page_index = get_page_index(page_str)
        p = Page(num,page_index)
        result = conn.web_detail.find().limit(p.limit).skip(p.offset).sort("release_date",-1)
        classtype = 'web'
    return render_template('index.html',result=result, page=p, num=num, dealnum=dealnum, counttype=counttype,countlable=countlable,countentity=countentity,classtype = classtype)

@app.route('/blog/')
def blog():
    conn = db()
    blogid = request.args.get('blogid')
    textclass = request.args.get('class')
    if textclass == "baidujingyan":
        text = conn.baidujingyan_details.find_one({'id':blogid})
    elif textclass == 'zhihu':
        text = conn.zhidao_details.find_one({'id':blogid})
    elif textclass == 'douban':
        text = conn.douban_details.find_one({'id':blogid})
    else:
        text = conn.web_detail.find_one({'id':blogid})
    #获取分类
    types_baidu = conn.type.find_one({'id':blogid,'state':0})
    types_people = conn.type.find_one({'id':blogid,'state':1})
    # infologger.logger.info('types_baidu',types_baidu)
    # infologger.logger.info('types_people',types_people)
    if types_baidu:
        if 'content' in types_baidu.keys() and types_baidu['content']:
            typebd = ','.join(types_baidu['content'])
        else:
            typebd = ''
    else:
        typebd = ''
    if types_people:
        if 'content' in types_people.keys() and types_people['content']:
            typecontent = ','.join(types_people['content'])
        else:
            typecontent = ''
        if 'desc' in types_people.keys() and types_people['desc']:
            typedesc = ','.join(types_people['desc'])
        else:
            typedesc = ''
    else:
        typecontent = ''
        typedesc = ''
    if types_people and types_baidu:
        types = json.dumps([{"content":typecontent,"desc":typedesc,"source":"人工"},{"content":typebd,"source":"百度aip"}])
    elif not types_baidu and types_people:
        types = json.dumps([{"content":typecontent,"desc":typedesc,"source":"人工"}])
    elif not types_people and types_baidu:
        types = json.dumps([{"content":typebd,"source":"百度aip"}])
    else:
        types = json.dumps([])

    #获取标签
    labels_baidu = conn.label.find_one({'id':blogid,'state':0})
    labels_people = conn.label.find_one({'id':blogid,'state':1})
    #nlp标签（夏侯麒麟添加）
    labels_nlp = conn.label.find_one({'id':blogid,'state':2})
    # infologger.logger.info('labels_baidu',labels_baidu)
    # infologger.logger.info('labels_people',labels_people)
    # infologger.logger.info('labels_nlp',labels_nlp)
    if labels_baidu:
        if 'content' in labels_baidu.keys() and labels_baidu['content']:
            contentbd = ','.join(labels_baidu['content'])
        else:
            contentbd = ''
    else:
        contentbd = ''
    if labels_people:
        if 'content' in labels_people.keys() and labels_people['content']:
            contentpp = ','.join(labels_people['content'])
        else:
            contentpp = ''
        if 'desc' in labels_people.keys() and labels_people['desc']:
            desc = ','.join(labels_people['desc'])
        else:
            desc = ''
    else:
        contentpp = ''
        desc = ''
    #nlp_label（夏侯麒麟添加）
    if labels_nlp:
        if 'content' in labels_nlp.keys() and labels_nlp['content']:
            contentnlp = ','.join(labels_nlp['content'])
        else:
            contentnlp = ''
    else:
        contentnlp = ''

    if labels_people and labels_baidu and labels_nlp:
        labels = json.dumps([{"content":contentpp,"desc":desc,"source":"人工"},{"content":contentbd,"source":"百度aip"},{"content":contentnlp,"source":"nlp"}])
    elif labels_people and labels_nlp and not labels_baidu:
        labels = json.dumps([{"content":contentpp,"desc":desc,"source":"人工"},{"content":contentnlp,"source":"nlp"}])
    elif labels_people and labels_baidu and not labels_nlp:
        labels = json.dumps([{"content":contentpp,"desc":desc,"source":"人工"},{"content":contentbd,"source":"百度aip"}])
    elif labels_baidu and labels_nlp and not labels_people:
        labels = json.dumps([{"content":contentbd,"source":"百度aip"},{"content":contentnlp,"source":"nlp"}])
    elif not labels_people and not labels_nlp and labels_baidu:
        labels = json.dumps([{"content":contentbd,"source":"百度aip"}])
    elif not labels_people and not labels_baidu and labels_nlp:
        labels = json.dumps([{"content":contentnlp,"source":"nlp"}])
    elif not labels_baidu and not labels_nlp and labels_people:
        labels = json.dumps([{"content":contentpp,"desc":desc,"source":"人工"}])
    else:
        labels = json.dumps([])

    #获取片段(在操作过程中只删除某一个字段会报错)
    paragraphs = conn.segment.find({'id':blogid})
    need_list = []
    if paragraphs:
        for p in paragraphs:
            need = {"content":p['content'],"desc":p['desc'],"source":p['source'],"url":p['url']}
            need_list.append(need)
        # print(need_list)
        para = json.dumps(need_list)
    else:
        para = json.dumps([])
    # infologger.logger.info('paragraphs',paragraphs)

    #获取实体词
    entity_people = conn.entity.find_one({'id':blogid,'state':1})
    entity_nlp = conn.entity.find_one({'id':blogid,'state':2})
    # infologger.logger.info('entity_people',entity_people)
    # infologger.logger.info('entity_nlp',entity_nlp)
    if entity_nlp:
        if 'content' in entity_nlp.keys() and entity_nlp['content']:
            nlpentity = entity_nlp['content']
        else:
            nlpentity = ''
    else:
        nlpentity = ''
    if entity_people:
        if 'content' in entity_people.keys() and entity_people['content']:
            contententity = ','.join(entity_people['content'])
        else:
            contententity = ''
        if 'desc' in entity_people.keys() and entity_people['desc']:
            descentity = ','.join(entity_people['desc'])
        else:
            descentity = ''
    else:
        contententity = ''
        descentity = ''
    if entity_people and entity_nlp:
        entitys = json.dumps([{"content":contententity,"desc":descentity,"source":"人工"},{"content":nlpentity,"source":"NLP"}])
    elif not entity_nlp and entity_people:
        entitys = json.dumps([{"content":contententity,"desc":descentity,"source":"人工"}])
    elif not entity_people and entity_nlp:
        entitys = json.dumps([{"content":nlpentity,"source":"NLP"}])
    else:
        entitys = json.dumps([])
    return render_template('blog.html',content=text,labels=labels,types=types,para=para,entitys=entitys)

@app.route('/insertdata',methods = ['POST','GET'])
def insertdate():
    mongo = db()
    if request.method == "POST":
        try:
            blogid = request.args.get('blogid')
            data = request.json
            # infologger.logger.info('data',data)
            #实体入库逻辑
            if 'words' in data.keys():
                entity_data = data['words']
                people_content_entity = []
                people_desc_entity = []
                nlp_entity = []
                for e in entity_data:
                    if e['source'] == "人工":
                        people_content_entity.append(e['content'])
                        people_desc_entity.append(e['desc'])
                    if e['source'] == "NLP":
                        nlp_entity.append(e['content'])
                if people_content_entity:
                    people_item_entity = {'id':blogid,'content':people_content_entity,'desc':people_desc_entity,'source':'人工','state':1}
                    try:
                        mongo.entity.update({'id':blogid,'state':1},people_item_entity,True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                else:
                    mongo.entity.remove({'id':blogid,'state':1})
                if nlp_entity:
                    nlp_item_entity = {'id':blogid,'content':nlp_entity,'source':'NLP','state':2}
                    try:
                        mongo.entity.update({'id':blogid,'state':2},nlp_item_entity,True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                else:
                    mongo.entity.remove({'id':blogid,'state':2})
            else:
                mongo.entity.remove({'id':blogid})

            #标签入库逻辑
            if 'labels' in data.keys():
                labels = data['labels']
                people_content = []
                people_desc = []
                nlp_content = []
                tag = []
                for l in labels:
                    if l['source'] == '人工':
                        people_content.append(l['content'])
                        people_desc.append(l['desc'])
                    if l['source'] == '百度aip':
                        tag = [l['content']]
                    if l['source'] == 'NLP':
                        nlp_content.append(l['content'])
                if nlp_content:
                    nlp_item_label = {'id':blogid,'content':nlp_content,'source':'NLP','state':2}
                    try:
                        mongo.label.update({'id':blogid,'state':2},nlp_item_label,True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                else:
                    mongo.label.remove({'id':blogid,'state':2})

                if people_content:
                    people_item = {'id':blogid,'content':people_content,'desc':people_desc,'source':'人工','state':1}
                    try:
                        mongo.label.update({'id':blogid,'state':1},people_item,True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                    print(people_item)
                else:
                    mongo.label.remove({'id':blogid,'state':1})

                if tag:
                    baidu_item = {'id':blogid,'content':tag,'source':'百度aip','state':0}
                    try:
                        mongo.label.update({'id':blogid,'state':0},baidu_item,True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                else:
                    mongo.label.remove({'id':blogid,'state':0})
            else:
                mongo.label.remove({'id':blogid})

            #分类入库逻辑
            if 'categories' in data.keys():
                type_data = data['categories']
                print(type_data)
                people_content2 = []
                people_desc2 = []
                baidu_type = []
                for t in type_data:
                    if t['source'] == '人工':
                        people_content2.append(t['content'])
                        people_desc2.append(t['desc'])
                    if t['source'] == '百度aip':
                        baidu_type = [t['content']]
                if people_content2:
                    people_item_type = {'id':blogid,'content':people_content2,'desc':people_desc2,'source':'人工','state':1}
                    try:
                        mongo.type.update({'id':blogid,'state':1},people_item_type,True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                else:
                    mongo.type.remove({'id':blogid,'state':1})
                if baidu_type:
                    baidu_item_type = {'id':blogid,'content':baidu_type,'source':'百度aip','state':0}
                    try:
                        mongo.type.update({'id':blogid,'state':0},baidu_item_type,True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                    # print(baidu_item_type)
                else:
                    mongo.type.remove({'id':blogid,'state':0})
            else:
                mongo.type.remove({'id':blogid})

            #片段入库逻辑
            if 'paragraphs' in data.keys():
                paragraphs_data = data['paragraphs']
                paragraphs_content = []
                paragraphs_desc = []
                for p in paragraphs_data:
                    paragraphs_content.append(p['content'])
                    paragraphs_desc.append(p['desc'])
                if paragraphs_content:
                    try:
                        pd = mongo.segment.find_one({'id':blogid,'state':1})
                        if pd == None:
                            mongo.segment.update({'id':blogid},{'id':blogid,'desc':paragraphs_desc,'url':p['url'],'state':1,'source':p['source'],'content':paragraphs_content,'crawl_time':errortime,'update_time':errortime},True)
                        else:
                            if 'crawltime' in pd.keys():
                                crawltime = pd['crawl_time']
                            else:
                                crawltime = errortime
                            mongo.segment.update({'id':blogid},{'id':blogid,'desc':paragraphs_desc,'url':p['url'],'state':1,'source':p['source'],'content':paragraphs_content,'crawl_time':crawltime,'update_time':errortime},True)
                    except Exception as e:
                        errorlogger.logger.error(e)
                        return '{"code":0,"message":"入库失败"}'
                else:
                    mongo.segment.remove({'id':blogid})
            else:
                mongo.segment.remove({'id':blogid})
        except Exception as e:
            errorlogger.logger.error(e)
            return '{"code":1,"message":"其他错误"}'
        mongo.web_detail.update({'id':blogid},{'$set':{'sign':1}})
    return '{"code":2,"message":"入库成功"}'

@app.route('/care/')
def care():
    return render_template('care.html')

@app.route('/abstract/')
def abstract():
    conn = db()
    blogid = request.args.get('blogid')
    url = 'http://47.92.73.83:8099/abstract_sever?blogid={}'.format(blogid)
    content = conn.web_detail.find_one({'id':blogid})['content_html']
    abscontent = requests.get(url=url).content.decode()
    return render_template('abstract.html',content=content,abscontent=abscontent)





if __name__ == '__main__':
    # app.run(threaded=True)
    app.run(threaded=True,host='172.26.26.131',port=8993)
    # app.run()