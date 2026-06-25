# 未来Ai之争就是数据之争

## 过去公司的竞争可能是技术的壁垒。

## 真正拉开差距的数据。

## 数据可以干啥？

1. 建立Rag知识库
2. 可以那数据清洗之后  做模型微调

## 你没有数据，空系统是无用的。

## 数据未来是企业的核心资产、核心价值。

## 技术不值钱了。

## 数据就是业务、业务就是数据。

## 关于大家面试找工作的感想。

1. 我们去写项目，实际上是拍电影（来源于小说改写的剧本）
2. 但是我们面试其实是写小说、造梦、画饼

## 我们的业务场景（通用）

我们是一家线上教育公司。

卖课。

1. 抖音（直播间）
2. 微信咨询 ajian888520  班主任： dwang888999

加我们微信，咨询课程。

1. 人工接待
2. Ai客服
   1. 数据来源
      1. 自己建的飞书知识库、写的文档。
      2. 导入真实微信数据、数据清洗。（数据中心的范畴之一）
         1. 客户的咨询就是我们卖课的过程（业务   产品=> 钱）
3. 数据源
   1. 微信的客户咨询数据（现有）
   2. 我搞个麦克风  把我所有说过的话录下来 ASR转文字
      1. 和数据中心打通  清洗
         1. 课程相关
         2. 公司团队管理
         3. 短视频素材
      2. 沉淀成数据，驱动Ai Agent去干活，降本增效
   3. 课程的课件  项目源代码   
      1. 数据清洗
      2. 输出技术分享
      3. 生成短视频的技术文案 => 技术分享的视频 => 发抖音

## 电商的场景建立数据中心

业务 => 产品 => 钱

1. 数据来源
   1. C端直接挂店铺
   2. 私域咨询成交  微信  whtasapp
      1. 数据导出 清洗 建立数据中心
         1. 做Ai客服
         2. 做销售培训系统
         3. 模型微调
      2. 建立素材中心（和客服数据打通）
         1. 产品生图
         2. 产品生文案
         3. 多模态的知识库
      3. 订单管理 
      4. 发票管理
      5. 跟单管理 清关
      6. 老板平时的讲话 录音  Asr
         1. 建立知识库
         2. 发抖音
         3. 团队管理

## 保险业务数据中心

1. 客户咨询   => 数据中心
2. 保险的详细条款
3. 素材中心
   1. 宣传图片
   2. 保险的介绍文案

## 未来的业务功能扩展，实际上是数据的扩展

# 我们的数据是怎么来的？

[微信数据处理流程](https://jianxuanguan.feishu.cn/wiki/AFxawZFUAiJOsQkGeCwcCRFMngc?sheet=4Meqxp)

[docker安装与env key配置](https://jianxuanguan.feishu.cn/wiki/JqIEwKqmhiThm6kwxnkc7OqdnVe)

# 微信的数据导出流程

转换的过程你了解即可，不需要很的去实操。

1. 用工具https://gitee.com/git-jiadong/wechatDataBackup导出微信数据
2. 得到一个SQ Lite  轻量数据库（就是另一种形式 Mysql） 只读的
3. 写一个python脚本  （ETL 桥接），进行格式转换（Ai写的脚本）
4. 转成Postgre 数据库
5. 写个前端界面+python服务 读数据

只保留了文本内容。（业务核心展示就够了）

图片 视频 音频过滤了

# 环境准备

Docker

1. 向量数据库  pg
2. Postgre
3. 初始化的数据（准备的假数据）

1. ## 安装docker

https://www.docker.com/

https://www.docker.com/products/docker-desktop/

一直下一步 默认就行。

网站打不开就尝试  关闭或者开启VPN

1. ## 测试docker的安装状态

```Python
docker --version
```

1. ## 关闭你本地的 postgre服务、关闭本地pg

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=MmM3NTEzMTgyODY5NWNmMmM1NTY1OTNkYzlmMjg2OTNfSmE5VWNNTjdsYVhHckxCYmU2SFV0QVRSMlJkUWhHaWxfVG9rZW46UmJRSWJkVklobzZHSzl4b1dkTmM4ak1Bbk9oXzE3ODE1MjkzNzY6MTc4MTUzMjk3Nl9WNA&add_watermark=true&scene_type=CCM)

1. ## 安装docker 镜像

项目根目录

(base) PS D:\5.0 project\ai-sale-course>

```Python
docker compose -f docker-compose.db.yml up -d
```

1. ## Cd backend 启动后台

```Python
uv sync

cp env.example .env   // 你们等下配

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

1. ## Cd fontend 启动前端

需要安装nodejs

```Python
npm i 
npm run dev
```

1. ## 配置env key

```Bash
# Database (docker compose -f docker-compose.db.yml up -d)
DATABASE_URL=postgresql://postgres:123456@localhost:5432/aiwxchat


# DeepSeek API
DEEPSEEK_API_KEY=sk-456fe0c07a584d4ebdf6fd8e728d8e
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# WeChat Database Path
WECHAT_DB_PATH=../Msg/Msg

# WeChat Voice File Path
VOICE_FILE_PATH=../FileStorage/Voice

# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
APP_ENV=dev

# Volcengine TOS (Object Storage)
TOS_ACCESS_KEY=AKLTZDVkNWFmYWYwMzBiNGQyZGFjMWY2NjVhODRlMT
TOS_SECRET_KEY=TlRsaE9URXdOVFkyWmpnek5HTmxaRGc0TVdZMVpUZzxWldWak5XWQ==
TOS_ENDPOINT=https://tos-cn-beijing.volces.com
TOS_REGION=cn-beijing
TOS_BUCKET=wx-bucket

# Cloud Embedding API (DashScope)
ARK_API_KEY=sk-68d7db0a23614de88ced681ac57
ARK_EMBEDDING_MODEL=text-embedding-v3
ARK_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

[docker安装与env key配置](https://jianxuanguan.feishu.cn/wiki/JqIEwKqmhiThm6kwxnkc7OqdnVe)

# 代码仓库

https://gitee.com/leejersey/ai-sale-course

# 项目核心

**数据中台的概念，是贯穿我们所有项目。**

这个项目核心我们围绕数据清洗去讲。

项目6：数据清洗

项目7：Ai销售考核

项目8：Ai素材库

# 数据清洗 数据源

我们项目中的实际数据源   postgre

为什么要清洗？脏数据。

# 微信的数据源

postgre3张表

1. 联系人
2. 会话
3. 原始消息
   1. 文字
   2. 音频
   3. 视频

python服务端查询数据库，给前端api

前端调用，界面展示

# 微信聊天记录展示的作用

**我们公司，只有1个微信账号。**

给销售去使用，去学习。

**如果有多个账号，功能继续扩展。逻辑是一样的。**

目的：

1. 公司内部学习，全公司都能访问学习
   1. 把敏感信息脱敏
2. 获取数据源
   1. 可以查询消息记录

# 机器python脚本清洗数据流程

SQ Lite （只读）=> **转换脚本ETL** => **PostGre数据**

经过数据过滤

我是22年创业  => 26年  4年。

1. 时间  25.11以后（跟业务不相关的去掉）
2. 关键词过滤  （出现 前端  过滤掉）
3. 低质量对话 （割韭菜  过滤掉）
4. 价格    （关于价格的数据清洗掉）

两个维度：

1. 整段会话删除
2. 具体某一条

我们的数据过滤 应该在**PostGre数据（原始数据）之后**

数据过滤流程  

为了保证架构的灵活性，不能在ELT阶段过滤数据。

只要原始数据在，我想怎么过滤怎么过滤，都不会破坏系统。

系统的可扩展性。

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=ZmNmYzAzNGMyNWEwNDI3OGE4NDI2ZWVlMjk0YWE5ZjVfazE1RnRyUEpFMHMwT0lXRDBnNXloa1lCdE13eVh6RkVfVG9rZW46VXViRGJ2NWFCb2NEMk14eHdTV2M2Tmdibk5jXzE3ODE1MjkzNzY6MTc4MTUzMjk3Nl9WNA&add_watermark=true&scene_type=CCM)

# 人工清洗环节

postGre的原始数据表 => 机器清洗过滤 => `staging_conversations`表

`staging_conversations`表  是  经过机器过滤之后的会话

接下来开始人工清洗

1. 数据拒绝  删掉   没通过
2. 通过了的  打上标签
   1. 补充功能
      1. 会话可编辑

人工清洗实际上 修改 `staging_conversations`这张表

`staging_conversations`最终留下的高质量对话，高质量原始数据。

# 人工补充数据（自定义对话数据管理）

场景在哪？

我现在有10款鞋子。

出了个新款 。

1. 人工补充新款的信息。
2. 有一些我们希望Ai能回复的，但是用户从来没问过，未来可能会问。

`staging_conversations` 对于我们来说就是一段对话

5分钟为维度切割。

```Python
张老师: 你好，我想了解一下你们的课程
我: 你好呀～欢迎咨询！我们有基础班和进阶班两种
张老师: 基础班多少钱？
我: 基础班现在活动价2980，原价3980
张老师: 有点贵，能优惠吗？
我: 现在报名可以送价值500的资料包，相当于只要2480哦
自定义数据  ``是一张新的表``  custom_conversations
```

真正的数据源(高质量的数据) =  `staging_conversations`（人工清洗 打标签的数据）  + `custom_conversations`（人工手动加的数据）

我们拿这些数据可以干嘛？

1. 建立Rag知识库 => 给Ai客服系统使用（项目1）
2. 建立Rag知识库 => 销售培训AI用 （项目7）
3. 输出 SFT需要的数据  => 微调
4. 输出 DPO需要的数据  => 微调
5. Ai素材库（项目8 喜报 + 视频） => 对`custom_conversations`强化补充 => 继续服务Ai客户系统（文本、图片、视频回复）

# 思维通了，一通百通

# 数据导出-Rag知识库

真正的数据源 =  `staging_conversations`（人工清洗 打标签的数据）  + `custom_conversations`（人工手动加的数据）

真正的数据源 => 转换规则 => Rag数据

# 数据导出-微调的数据

真正的数据源 =  `staging_conversations`（人工清洗 打标签的数据）  + `custom_conversations`（人工手动加的数据）

真正的数据源 => 转换规则 => 微调数据

# 数据导出-支撑Ai销售考核系统