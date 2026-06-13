# 我们的业务场景做素材库的目的

**核心目的：对数据中台的文字数据进行补充，更好的服务Ai业务**

1. 数据中台的数据补充
2. 我们自己有个资料归档
   1. 微信聊天记录 => 清洗 => 文字素材库
   2. 图片   手动维护
   3. 聊天记录的截图、offer的截图
3. 为Ai客服系统提供**多模态的回复能力**
   1. 文字
   2. 图片
   3. 视频
      1. 我拍了很多主题的视频
         1. 大专可以学吗？ 1分钟视频
         2. 年龄大可以学吗？  1分钟视频

# 核心目标： 让Ai客服有多模态的回复能力

是对文本回复的补充。

# 数据中台

数据整合

1. 文本聊天数据
2. 图片
3. 视频

## 用户提问： 我大专可以学吗?

1. 大专当然可以
2. 需要我给你一些大专案例吗？
3. 回复图片
4. 回复视频（我的解读）

# 素材管理的功能

1. 动态创建文件夹
   1. 多级目录
      1. 喜报
         1. 大专
         2. 本科
         3. 硕士
      2. 截图
         1. 聊天记录
         2. 群里记录
         3. 收款

上传文件，传给火山引擎 tos 云盘服务，返回一个地址

# 技术方案

```Python
我现在已经有个Ai客服系统，我准备去构建知识库。
然后通过整个项目的数据清洗和素材管理，让Ai客户能够回复文字、图片、视频。

比如：用户问 我大专可以学吗？
Ai回复：大专当然可以学啊，我们这有很多案例xxxx
Ai回复：大专找到工作的喜报、聊天记录截图等等
Ai回复： 视频对于大专能学吗？这个问题的解答。

请你输出一套技术方案，主要解决我以下几个问题
1. 我们数据中心导出的文本数据结构？chunk如何拆分？postgre和pgvctor怎么存？怎么查？
2. 图片如何进行回复？命中语义
3. 视频如何回复？命中语义
```

## 两条路线

在线处理

1. 文本
2. 图片（人工维护图片的信息  + 图片链接）
   1. 图片 url
   2. 标签  14k  大专
   3. 描述 之前这个同学在北京15k，大专，失业了。。。。
3. 视频 （人工维护视频信息  + 视频链接 ）
   1. 视频本身  url
   2. 标签   大专
   3. 描述  人工写的摘要

离线处理：

1. 图片  ocr => 解析图片的文字  建库
   1. 补充对图片的描述
2. 视频  asr => 转写  => 建库
   1. 离线asr转写   补充视频的描述

```Python
你的方案大体是对的。
我准备分两条路走
1. 图片 视频初次上传的时候 人工维护标签和信息等等，能够直接让Rag命中语义返回图片、视频的在线链接
2. 图片 视频离线处理，补充知识库

请你根据我的思路，分别输出两个MD，前后有联系。
主要重点讲清楚
1. 纯文本内容  PostgreSQL+pgvctor数据怎么存，怎么切片，怎么查。分别给出数据示意
2. 图片   人工的信息维护什么？数据库存什么怎么查？
3. 视频 人工的信息维护什么？数据库存什么怎么查？
4. 离线的图片、视频怎么处理，数据怎么存，怎么查。如何设计？
```

# 在线策略

所有的多模态 统一用一张表

## 数据库的表设计

1. 数据类型
2. 返回的内容   文字、url
3. 标签、可信度
4. 来源、创建时间

```SQL
CREATE TABLE rag_assets (
    id              bigserial PRIMARY KEY,
    modality        varchar(10)  NOT NULL,          -- 'text' / 'image' / 'video'-- 检索核心
    retrieval_text  text         NOT NULL,          -- 真正被向量化的文本
    embedding       vector(1024),                   -- text-embedding-v3 输出-- 命中后返回给客服/前端的展示内容
    answer_text     text,                            -- 文字回复正文
    media_url       text,                            -- 图片/视频在线URL（text模态为空）
    cover_url       text,                            -- 视频封面URL
    duration_sec    integer,                         -- 视频时长（秒）-- 过滤 / 排序维度
    category        varchar(50),                     -- course/sales/objection...
    tags            jsonb DEFAULT '[]',              -- ["大专","北京","15k"]
    confidence      float DEFAULT 1.0,               -- 人工内容默认高置信-- 来源追溯 + 路线标记
    source_table    varchar(40),                     -- materials / video_assets / knowledge_articles
    source_id       bigint,
    enrich_status   varchar(10) DEFAULT 'manual',    -- manual（人工）/ enriched（已离线增强）
    status          varchar(20) DEFAULT 'active',    -- active / disabled
    created_at      timestamp DEFAULT now(),
    updated_at      timestamp DEFAULT now(),

    UNIQUE (source_table, source_id)                 -- 一个源对象对应一行，便于 UPSERT
);
```

## 文本怎么存？

`rag_assets`表

1. 数据中心导出JSONL
2. 构造embbeding的原始数据
   1. 写一段对jsonl的描述
   2. 长文本拆分chunk   007#1 007#2
   3. Embedding
3. 更新到rag_assets这张表

## 图片怎么存？

图片有一张单独的表 materials（只存图片）

1. 上传图片，人工去补充信息
   1. 图片的url
   2. 描述
   3. 标签
2. 落到数据库的内容
   1. 类型  图片
   2. 备注的原文
   3. embedding的向量
   4. llm的回复示意
   5. 标签
   6. 创建时间

```Bash
id            | 2001
modality      | image
retrieval_text| 深圳大专学员offer-字节15k。大专学历转行AI拿到offer的真实案例，证明学历不是门槛。大专 深圳 15k 字节 offer
embedding     | [0.022, -0.018, ...] (1024维)
answer_text   | 这是大专、深圳、15k相关的学员真实案例 👇
media_url     | https://bucket.tos-cn-beijing.volces.com/materials/masked/uuid-bbb.png
category      | report
tags          | ["大专","深圳","15k","字节","offer"]
source_table  | materials
source_id     | 5001
enrich_status | manual
```

## 视频怎么存？

video_assets （只存视频） 独立的表

video_assets 只存视频相关的原始数据。

最终会进行embbeding之后，更新到`rag_assets`总表。

最终的查询，实际上都是差的`rag_assets`。

## 最终的查询

只查询总表`rag_assets`

只需要和数据库建立一次链接

```Python
def answer_with_media(db, query, category=None):
    texts  = semantic_search(db, query, modality="text",  top_k=3, min_sim=0.35)
    images = semantic_search(db, query, modality="image", top_k=3, min_sim=0.40)
    videos = semantic_search(db, query, modality="video", top_k=1, min_sim=0.42)

    replies = []
    if texts:  replies.append({"type": "text",  "text": llm_polish(query, texts)})
    if images: replies.append({"type": "image", "text": images[0].answer_text,
                               "images": [i.media_url for i in images[:3]]})
    if videos:
        v = videos[0]
        replies.append({"type": "video", "text": v.answer_text,
                        "video": {"url": v.media_url, "cover": v.cover_url,
                                  "duration": v.duration_sec}})
    return replies   # 按 文字→图片→视频 顺序分条发送
```

# 离线方案

为什么要离线

纯人工：

1. 图片写描述
2. 视频要写描述吧

让Ai写描述呗。

1. 传个图
   1. 标签填一下
   2. 剩下描述Ai解析图片  Ai写
2. 传个视频（我们的场景可以，口播。  没声音，服装宣传没文案）
   1. 标签填一下
   2. 剩下描述Ai解析（asr解析声音转文字）  Ai写

你既然有了ai写描述，为何还要人工呢？

比如有些视频没有说话，纯内容表达

## 假设我只传图，什么都不管了

要看具体的场景

1. 图的内容足够丰富
2. LLM解析图片内容
3. LLM根据解析的内容输出一个json
   1. 分类
   2. 标签
   3. 描述

## OCR和VLM的区别？

OCR主要是翻译

VLM主要是识别逻辑

豆包模型  doubao-1.8-vision  混合模型  

## 离线其实只干一件事情

1. 当你上传图片或者视频
2. Ai就开始解析，返回文字内容
3. 补充进retrieval_text
4. 重新embedding
5. 其他不变

## 幂等更新

retrieval_text： 人工备注  +  Ai生成的

字符串拼接

```Python
var str = A + B
```

意外：拼接了多次   ABBBB

`manual_text`（存放人工 A，写入后几乎不动）

`machine_text`（存放Ai生成的 B，由离线 Worker 随时覆盖）

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=NTIzODBkOTM0Nzc5NWYyMTdlMzQxYzViODFjMGE4MmJfZFNMcGVJbTdvQnhNSk9lRjhZb1ZjZ2R3ZVFBTlA1cnBfVG9rZW46RWltQWJBbEE0bzI5S0d4WDlqbmN5eXVJbjViXzE3ODEzMzc4NzU6MTc4MTM0MTQ3NV9WNA&add_watermark=true&scene_type=CCM)

**你就是指挥官，不要全部指望Ai。**

## 离线任务

厨师  和  黑板的故事

用postgre原始的表

1.  `rag_assets`表有一个enrich_status   
   1. 没有任务
   2. 等待处理
   3. 处理中
   4. 已处理完成
2. Python有一个脚本，不断的去轮询，有等待处理的任务吗？
3. 有就拿过来   通过worker去处理
4. 处理好返回

# 课外补充

1. 传统的后台数据库怎么做幂等更新
2. 了解下传统的消息队列  kafka  rabit mq
3. 了解下redis怎么做消息队列