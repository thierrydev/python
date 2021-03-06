# coding:utf-8

'''
@author = super_fazai
@File    : article_spider.py
@connect : superonesfazai@gmail.com
'''

"""
文章资讯爬虫

已支持:
    1. 微信文章内容爬取(https://weixin.sogou.com)
    2. 今日头条文章内容爬取(https://www.toutiao.com)
    3. 简书文章内容爬取(https://www.jianshu.com)
    4. qq看点文章内容爬取(根据QQ看点中分享出的地址)
    5. 天天快报(根据天天快报分享出的地址)
待实现:
    1. 网易新闻
"""

from os import getcwd
from os.path import abspath
from gc import collect
from my_items import WellRecommendArticle
from settings import (
    ARTICLE_ITEM_LIST,
    MY_SPIDER_LOGS_PATH,
    PHANTOMJS_DRIVER_PATH,
    IP_POOL_TYPE,)

from fzutils.spider.fz_driver import BaseDriver
from ftfy import fix_text
from requests import session
from fzutils.spider.selector import async_parse_field
from fzutils.spider.async_always import *

class ArticleParser(AsyncCrawler):
    """article spider"""
    def __init__(self, logger=None, *params, **kwargs):
        AsyncCrawler.__init__(
            self,
            *params,
            **kwargs,
            log_print=True,
            logger=logger,
            log_save_path=MY_SPIDER_LOGS_PATH + '/articles/_/',
            ip_pool_type=IP_POOL_TYPE)
        self.driver_path = PHANTOMJS_DRIVER_PATH

    @staticmethod
    async def _get_headers():
        return {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': get_random_pc_ua(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

    async def _get_phone_headers(self):
        return {
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': get_random_phone_ua(),
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
        }

    @staticmethod
    async def _get_obj_origin() -> dict:
        '''
        设置obj_origin_dict
        :return:
        '''
        return {
            'wx': {
                'obj_origin': 'mp.weixin.qq.com',
                'site_id': 4,
            },
            'tt': {
                'obj_origin': 'www.toutiao.com',
                'site_id': 5,
            },
            'js': {
                'obj_origin': 'www.jianshu.com',
                'site_id': 6,
            },
            'kd': {
                'obj_origin': 'post.mp.qq.com',
                'site_id': 7,
            },
            'kb': {
                'obj_origin': 'kuaibao.qq.com',
                'site_id': 8,
            },
        }

    async def _get_html_by_driver(self, url, load_images=False):
        '''
        使用driver获取异步页面
        :return:
        '''
        driver = BaseDriver(
            executable_path=self.driver_path,
            ip_pool_type=self.ip_pool_type,
            load_images=load_images,
            logger=self.lg)
        body = driver.get_url_body(url=url)
        # self.lg.info(body)
        try:
            del driver
        except:
            pass
        collect()

        return body

    async def _get_wx_article_html(self, article_url) -> tuple:
        '''
        得到wx文章内容
        :return: body, video_url
        '''
        body = await unblock_request(url=article_url, headers=await self._get_headers(), ip_pool_type=self.ip_pool_type, logger=self.lg)
        # self.lg.info(body)
        assert body != '', '获取到wx的body为空值!'

        return await self._wash_wx_article_body(body=body)

    async def _get_tt_article_html(self, article_url) -> tuple:
        '''
        得到头条文章内容
        :param article_url:
        :return: body, video_url
        '''
        headers = await self._get_headers()
        headers.update({
            'authority': 'www.toutiao.com',
            'referer': 'https://www.toutiao.com/',
        })
        body = await unblock_request(url=article_url, headers=headers, ip_pool_type=self.ip_pool_type, logger=self.lg)
        # self.lg.info(str(body))
        assert body != '', '获取到wx的body为空值!'

        return body, ''

    async def _get_js_article_html(self, article_url) -> tuple:
        '''
        得到简书文章html
        :param article_url:
        :return:
        '''
        headers = await self._get_headers()
        headers.update({
            'authority': 'www.jianshu.com',
            'referer': 'https://www.jianshu.com/',
        })
        body = await unblock_request(url=article_url, headers=headers, ip_pool_type=self.ip_pool_type, logger=self.lg)
        # self.lg.info(str(body))
        assert body != '', '获取到的js的body为空值!'

        return body, ''

    @staticmethod
    async def _wash_tt_article_content(content) -> str:
        '''
        清洗头条文章的content内容
        :return: body, video_url
        '''
        content = fix_text(content)
        # self.lg.info(content)
        # 图片设置居中
        content = re.compile(' inline=\"0\">').sub(' style=\"height:auto;width:100%;\">', content)

        return content

    @staticmethod
    async def _wash_js_article_content(content) -> str:
        '''
        清洗简书文章的content内容
        :param content:
        :return:
        '''
        # 处理图片
        content = re.compile(' data-original-src=').sub(' src=', content)
        content = re.compile(' data-original-filesize=\".*?\"').sub(' style=\"height:auto;width:100%;\"', content)

        # 附加上原生的style
        # 此法在server上getcwd()得到的是'/', os.path.abspath('.')得到的才是当前目录, 还是'/', 改用云存
        # now_path = abspath('.') + '/tmp/jianshu_style.txt'
        # print(now_path)
        # with open(now_path, 'r') as f:
        #     _ = Requests._wash_html(f.read())
        #     self.lg.info(str(_))

        jianshu_style_txt_url = 'http://pimkvjbu6.bkt.clouddn.com/jianshu_style.txt'
        with session() as s:
            _ = Requests._wash_html(s.get(url=jianshu_style_txt_url).content.decode('utf-8'))
        assert _ != '', '云端jianshu_style_txt获取失败!'

        content = _ + content

        return content

    async def _get_article_html(self, article_url, article_url_type) -> tuple:
        '''
        获取文章的html
        :return:
        '''
        video_url = ''
        body = ''
        try:
            if article_url_type == 'wx':
                return await self._get_wx_article_html(article_url=article_url)
            elif article_url_type == 'tt':
                return await self._get_tt_article_html(article_url=article_url)
            elif article_url_type == 'js':
                return await self._get_js_article_html(article_url=article_url)
            elif article_url_type == 'kd':
                return await self._get_kd_article_html(article_url=article_url)
            elif article_url_type == 'kb':
                return await self._get_kb_article_html(article_url=article_url)
            else:
                raise AssertionError('未实现的解析!')
        except AssertionError:
            self.lg.error('遇到错误:', exc_info=True)
            return body, video_url

    async def _get_kd_article_html(self, article_url):
        '''
        获取qq看点的html
        :param article_url:
        :return:
        '''
        headers = await self._get_headers()
        headers.update({
            'authority': 'post.mp.qq.com',
        })
        body = await unblock_request(url=article_url, headers=headers, ip_pool_type=self.ip_pool_type, logger=self.lg)
        # self.lg.info(body)
        assert body != '', '获取到的kd的body为空值!'

        return body, ''

    async def _get_kb_article_html(self, article_url):
        '''
        获取天天快报的html
        :param article_url:
        :return:
        '''
        headers = await self._get_phone_headers()
        headers.update({
            'authority': 'kuaibao.qq.com',
        })
        body = await unblock_request(url=article_url, headers=headers, ip_pool_type=self.ip_pool_type, logger=self.lg)
        # self.lg.info(body)
        assert body != '', '获取到的kb的body为空值!'
        '''
        单独处理含视频的
        '''
        title_selector_obj = await self._get_kb_title_selector_obj()
        if await async_parse_field(parser=title_selector_obj, target_obj=body, logger=self.lg) == '':
            # 表示title获取到为空值, 可能是含视频的
            # TODO 暂时先不获取天天快报含视频的
            self.lg.info('此article_url可能含有视频')
            # body = await self._get_html_by_driver(url=article_url, load_images=True)

        return body, ''

    async def _get_kb_title_selector_obj(self) -> dict:
        '''
        得到快报title selector
        :return:
        '''
        for item in ARTICLE_ITEM_LIST:
            if item.get('short_name', '') == 'kb':
                return item['title']

        raise AssertionError('获取kb 的title selector obj失败!')

    async def _wash_wx_article_body(self, body) -> tuple:
        '''
        清洗wx文章
        :return: body, video_url
        '''
        # 处理微信防盗链
        body = re.compile('<head>').sub('<head><meta name=\"referrer\" content=\"never\">', body)
        body = re.compile('data-src=').sub('src=', body)

        video_url = ''
        # 单独处理含视频标签的
        try:
            # videos_url_list = re.compile('<div class=\"tvp_video\"><video.*?src=\"(.*?)\"></video><div class=\"tvp_shadow\">').findall(body)
            videos_url_list = re.compile('<iframe class=\"video_iframe\" .*? src=\"(.*?)\"></iframe>').findall(body)
            assert videos_url_list != []
            self.lg.info('视频list: {}'.format(videos_url_list))
            self.lg.info('此文章含视频! 正在重新获取文章html...')

            tmp_body = await self._get_html_by_driver(url=videos_url_list[0], load_images=True)
            # self.lg.info(tmp_body)
            assert tmp_body != '', 'tmp_body为空值!'
            try:
                video_div = '<div style=\"text-align:center; width:100%; height:100%;\">' + \
                            re.compile('(<embed.*?)</div></div>').findall(tmp_body)[0] + '</div>'
                # self.lg.info(video_div)
            except IndexError:
                raise IndexError('获取video_div时索引异常!')
            # (只处理第一个视频)
            body = re.compile('<iframe class=\"video_iframe\" .*?></iframe>').sub(video_div, body, count=1)
            video_url = videos_url_list[0]
        except AssertionError:
            pass
        except Exception:
            self.lg.error('遇到错误: ', exc_info=True)
        # self.lg.info(body)

        return body, video_url

    async def _get_parse_obj(self, article_url_type) -> dict:
        '''
        获取到对应解析对象
        :return:
        '''
        for item in ARTICLE_ITEM_LIST:
            if article_url_type == item.get('short_name', ''):
                if item.get('obj_origin', '') == self.obj_origin_dict[article_url_type].get('obj_origin'):
                    parse_obj = item
                    return parse_obj

        raise NotImplementedError('未找到解析对象!')

    async def _parse_article(self, article_url) -> dict:
        '''
        解析文章内容
        :param article_url: 待抓取文章的url
        :return:
        '''
        self.obj_origin_dict = await self._get_obj_origin()    # 设置obj_origin_dict
        child_debug = await self.is_child_can_debug(article_url)
        if not child_debug:
            self.lg.error('article_url未匹配到对象 or debug未开启!')
            return {}

        try:
            article_url_type = await self._judge_url_type(article_url=article_url)
            parse_obj = await self._get_parse_obj(article_url_type=article_url_type)
        except (ValueError, NotImplementedError):      # article_url未知!
            self.lg.error(exc_info=True)
            return {}

        article_html, video_url = await self._get_article_html(
            article_url=article_url,
            article_url_type=article_url_type)
        # self.lg.info(article_html)
        try:
            title = await self._get_article_title(parse_obj=parse_obj, target_obj=article_html)
            author = await self._get_author(parse_obj=parse_obj, target_obj=article_html)
            head_url = await self._get_head_url(parse_obj=parse_obj, target_obj=article_html)
            content = await self._get_article_content(parse_obj=parse_obj, target_obj=article_html, article_url=article_url)
            print(content)
            create_time = await self._get_article_create_time(parse_obj=parse_obj, target_obj=article_html)
            comment_num = await self._get_comment_num(parse_obj=parse_obj, target_obj=article_html)
            fav_num = await self._get_fav_num(parse_obj=parse_obj, target_obj=article_html)
            praise_num = await self._get_praise_num(parse_obj=parse_obj, target_obj=article_html)
            tags_list = await self._get_tags_list(parse_obj=parse_obj, target_obj=article_html)
            site_id = await self._get_site_id(article_url_type=article_url_type)
            profile = await self._get_profile(parse_obj=parse_obj, target_obj=article_html)
        except (AssertionError, Exception):
            self.lg.error('遇到错误:', exc_info=True, stack_info=False)
            return {}

        _ = WellRecommendArticle()
        _['nick_name'] = author
        _['head_url'] = head_url
        _['profile'] = profile
        _['share_id'] = await self._get_share_id(article_url_type=article_url_type, article_url=article_url)
        _['title'] = title
        _['comment_content'] = ''
        _['share_img_url_list'] = []
        _['goods_id_list'] = []
        _['div_body'] = content
        _['gather_url'] = article_url       # wx 阅读原文跳出个验证
        _['create_time'] = create_time
        _['site_id'] = site_id
        _['goods_url_list'] = []
        _['tags'] = tags_list
        _['share_goods_base_info'] = []     # [{'goods_id': 'xxx', 'img_url': 'xxx'}, ...]
        _['video_url'] = video_url
        _['likes'] = praise_num
        _['collects'] = fav_num
        _['comment_num'] = comment_num

        return dict(_)

    async def _get_praise_num(self, parse_obj, target_obj):
        '''
        点赞数
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        praise_num = 0
        _ = await async_parse_field(parser=parse_obj['praise_num'], target_obj=target_obj, logger=self.lg)
        # self.lg.info(str(_))
        try:
            praise_num = int(_)
        except:
            pass

        return praise_num

    async def _get_fav_num(self, parse_obj, target_obj):
        '''
        收藏数
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        fav_num = await async_parse_field(parser=parse_obj['fav_num'], target_obj=target_obj, logger=self.lg)

        return fav_num

    async def _get_profile(self, parse_obj, target_obj):
        '''
        推荐人简介或个性签名
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        profile = await async_parse_field(parser=parse_obj['profile'], target_obj=target_obj, logger=self.lg)

        return profile

    async def _get_author(self, parse_obj, target_obj):
        '''
        作者
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        author = await async_parse_field(parser=parse_obj['author'], target_obj=target_obj, logger=self.lg)
        try:
            assert author != '', '获取到的author为空值!'
        except AssertionError:
            if parse_obj['short_name'] == 'kb':
                author = await self._get_kb_author_where_have_video(target_obj=target_obj)

        assert author != '', '获取到的author为空值!'

        return author

    async def _get_article_title(self, parse_obj, target_obj):
        '''
        文章title
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        title = await async_parse_field(parser=parse_obj['title'], target_obj=target_obj, logger=self.lg)
        try:
            assert title != '', '获取到的title为空值!'
        except AssertionError:
            if parse_obj['short_name'] == 'kb':
                title = await self._get_kb_title_where_have_video(target_obj=target_obj)

        assert title != '', '获取到的title为空值!'

        return title

    async def _get_head_url(self, parse_obj, target_obj) -> str:
        '''
        得到文章发布者的头像url
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        head_url = await async_parse_field(parser=parse_obj['head_url'], target_obj=target_obj, logger=self.lg)
        # 天天快报存在头像为''
        if head_url != '' \
                and not head_url.startswith('http'):
            head_url = 'https:' + head_url
        else:
            pass

        return head_url

    async def _get_share_id(self, **kwargs) -> str:
        '''
        得到唯一的share_id
        :return:
        '''
        article_url_type = kwargs.get('article_url_type', '')
        article_url = kwargs.get('article_url', '')

        if article_url_type == 'wx':
            return get_uuid1()

        article_id_selector = await self._get_article_id_selector(article_url_type=article_url_type)
        share_id = await async_parse_field(parser=article_id_selector, target_obj=article_url, logger=self.lg)
        assert share_id != '', '获取到的share_id为空值!'

        return share_id

    async def _get_article_id_selector(self, article_url_type) -> (dict, None):
        '''
        获取article_id的selector
        :param self:
        :param article_url_type:
        :return:
        '''
        for item in ARTICLE_ITEM_LIST:
            if article_url_type == item.get('short_name', ''):
                return item['article_id']

        raise NotImplementedError

    async def _get_comment_num(self, parse_obj, target_obj) -> int:
        '''
        文章评论数
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        comment_num = 0
        _ = await async_parse_field(parser=parse_obj['comment_num'], target_obj=target_obj, logger=self.lg)
        # self.lg.info(str(_))
        try:
            comment_num = int(_)
        except ValueError:      # 未提取到评论默认为0
            pass

        return comment_num

    async def _get_tags_list(self, parse_obj, target_obj) -> list:
        '''
        获取文章的tags list
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        is_first = False
        if parse_obj.get('short_name', '') == 'kd':
            # 取第一个str
            is_first = True

        tags_list = await async_parse_field(parser=parse_obj['tags_list'], target_obj=target_obj, is_first=is_first, logger=self.lg)
        if tags_list == '':
            return []

        if parse_obj.get('obj_origin', '') == self.obj_origin_dict['kd'].get('obj_origin'):
            tags_list = tags_list.split(',')

        if parse_obj.get('obj_origin', '') == self.obj_origin_dict['tt'].get('obj_origin')\
                or parse_obj.get('obj_origin', '') == self.obj_origin_dict['js'].get('obj_origin')\
                or parse_obj.get('obj_origin', '') == self.obj_origin_dict['kd'].get('obj_origin'):
            tags_list = [{
                'keyword': i,
            } for i in tags_list]

        return tags_list

    async def _get_article_create_time(self, parse_obj, target_obj) -> str:
        '''
        文章创建时间点
        :param parse_obj:
        :param target_obj:
        :return:
        '''
        create_time = await async_parse_field(parser=parse_obj['create_time'], target_obj=target_obj, logger=self.lg)
        # assert create_time != '', '获取到的create_time为空值!'

        return create_time

    async def _get_article_content(self, parse_obj, target_obj, article_url) -> str:
        '''
        article content
        :return:
        '''
        content = await async_parse_field(parser=parse_obj['content'], target_obj=target_obj, logger=self.lg)
        # TODO 先不处理QQ看点的视频
        # if content == '' \
        #         and parse_obj.get('short_name', '') == 'kd':
        #     # 单独处理QQ看点含视频的content
        #     html = await self._get_html_by_driver(url=article_url, load_images=True)
        #     print(html)

        try:
            assert content != '', '获取到的content为空值!'
        except AssertionError:
            if parse_obj.get('short_name', '') == 'kb':
                content = await self._get_kb_content_where_have_video(target_obj=target_obj)

        assert content != '', '获取到的content为空值!'
        if parse_obj.get('short_name', '') == 'tt':
            # html乱码纠正
            content = await self._wash_tt_article_content(content=content)

        if parse_obj.get('short_name', '') == 'js':
            # 图片处理
            content = await self._wash_js_article_content(content=content)

        if parse_obj.get('short_name', '') == 'kd':
            # 图片处理
            content = await self._wash_kd_article_content(content=content)

        if parse_obj.get('short_name', '') == 'kb':
            # css 处理为原生的
            content = await self._wash_kb_article_content(content=content)

        content = '<meta name=\"referrer\" content=\"never\">' + content  # hook 防盗链

        return content

    async def _get_kb_title_where_have_video(self, **kwargs) -> str:
        '''
        获取kb(含有视频)的title
        :return:
        '''
        target_obj = kwargs['target_obj']

        # 得到含视频的title
        _ = {
            'method': 'css',
            'selector': 'article.video-art div.video-title-container h1 ::text'
        }
        title = await async_parse_field(parser=_, target_obj=target_obj, logger=self.lg)
        # self.lg.info(title)

        return title

    async def _get_kb_author_where_have_video(self, **kwargs) -> str:
        '''
        获取kb(含有视频)的author
        :param kwargs:
        :return:
        '''
        target_obj = kwargs['target_obj']

        _ = {
            'method': 'css',
            'selector': 'article.media-art h1 ::text',
        }
        author = await async_parse_field(parser=_, target_obj=target_obj, logger=self.lg)
        # self.lg.info(author)

        return author

    async def _get_kb_content_where_have_video(self, **kwargs) -> str:
        '''
        获取kb(含有视频)的content
        :param kwargs:
        :return:
        '''
        target_obj = kwargs['target_obj']

        _ = {
            'method': 'css',
            'selector': 'txpdiv.txp_video_container video',
        }
        # phantomjs无法获取到原视频地址
        content = await async_parse_field(parser=_, target_obj=target_obj, logger=self.lg)

        return content

    @staticmethod
    async def _wash_kd_article_content(content) -> str:
        '''
        清洗QQ看点content
        :param content:
        :return:
        '''
        # 处理图片
        content = re.compile('<svg .*?>.*?</svg>').sub('', content)
        # 替换掉img 标签中src为svg的
        _ = re.compile(' src=\"data:image/svg\+xml;.*?\" ')
        # pprint(_.findall(content))
        content = _.sub(' ', content)
        content = re.compile(' data-src=').sub(' src=', content)
        content = re.compile('data-lazy=\"\d+\"').sub('style=\"height:auto;width:100%;\"', content)
        content = re.compile('<a class=\"jubao\"><i></i>举报内容</a>').sub('', content)

        # 给与原装的css
        content = '<link rel="stylesheet" href="//mp.gtimg.cn/themes/default/client/article/article.css?_bid=2321&v=2017082501">' + \
            content

        return content

    @staticmethod
    async def _wash_kb_article_content(content) -> str:
        '''
        清洗kb content
        :param content:
        :return:
        '''
        # 给与原生的css
        content = r'<link href="//mat1.gtimg.com/www/cssn/newsapp/cyshare/cyshare_20181121.css" type="text/css" rel="stylesheet">' + \
            content

        return content

    @staticmethod
    async def is_child_can_debug(article_url) -> bool:
        '''
        判断是否是子对象, 以及是否debug是打开
        :return:
        '''
        for item in ARTICLE_ITEM_LIST:
            if item.get('obj_origin', '') in article_url:
                if item.get('debug'):
                    return True

        return False

    async def _get_site_id(self, article_url_type) -> int:
        '''
        获取文章的site_id
        :return:
        '''
        if article_url_type == 'wx':
            return self.obj_origin_dict['wx'].get('site_id')

        elif article_url_type == 'tt':
            return self.obj_origin_dict['tt'].get('site_id')

        elif article_url_type == 'js':
            return self.obj_origin_dict['js'].get('site_id')
        
        elif article_url_type == 'kd':
            return self.obj_origin_dict['kd'].get('site_id')

        elif article_url_type == 'kb':
            return self.obj_origin_dict['kb'].get('site_id')

        else:
            raise ValueError('未知的文章url!')

    async def _judge_url_type(self, article_url) -> str:
        '''
        判断url类别
        :return:
        '''
        for key, value in self.obj_origin_dict.items():
            if value.get('obj_origin') in article_url:
                return key

        raise ValueError('未知的文章url!')

    def __del__(self):
        try:
            del self.lg
        except:
            pass
        try:
            del self.loop
        except:
            pass
        collect()

if __name__ == '__main__':
    _ = ArticleParser()
    loop = get_event_loop()
    # wx
    # 存在链接过期的情况
    # https://mp.weixin.qq.com/s?__biz=MzA4MjQxNjQzMA==&mid=2768396229&idx=1&sn=&scene=0#wechat_redirect
    # url = 'https://mp.weixin.qq.com/s?src=11&timestamp=1542166201&ver=1243&signature=qYsoi7Sn3*tmw9x-lXxo6sJfSYDGGyHewzZyJCjgovA8taCXuTtENN7X2d4dPnOz1TvEnO2LsYJR1W3IwozcIzLyfhcdcZgOoqyzPLhz469ssieB15ojFrdtA2y83*As&new=1'
    # url = 'https://mp.weixin.qq.com/s?src=11&timestamp=1545195601&ver=1283&signature=0wD3ij5dP9cs5hAXeHqb12I6CgxVu8HmadJhszmKuGI-PSMqcIoYd66qvE4Mg5ejrxCxWTgDC-s1xMaKviWC4Noe9GjwKzZpFCXLyRt6IkTne1YF4Yc8qmDvBVgb3w5c&new=1'

    # 头条(视频切入到content中了)    [https://www.toutiao.com/]
    # url = 'https://www.toutiao.com/a6623290873448759815/'
    # url = 'https://www.toutiao.com/a6623125148088140291/'
    # url = 'https://www.toutiao.com/a6623325882381500931/'     # 含视频
    # url = 'https://www.toutiao.com/a6623270159790375438/'

    # 简书
    url = 'https://www.jianshu.com/p/ec1e9f6129bd'
    # url = 'https://www.jianshu.com/p/a02313dd3875'
    # url = 'https://www.jianshu.com/p/7160ad815557'
    # url = 'https://www.jianshu.com/p/1a60bdc3098b'

    # QQ看点
    # url = 'https://post.mp.qq.com/kan/article/2184322959-232584629.html?_wv=2147483777&sig=24532a42429f095b9487a2754e6c6f95&article_id=232584629&time=1542933534&_pflag=1&x5PreFetch=1&web_ch_id=0&s_id=gnelfa_3uh3g5&share_source=0'
    # 含视频
    # url = 'http://post.mp.qq.com/kan/video/201271541-2525bea9bc8295ah-x07913jkmml.html?_wv=2281701505&sig=50b27393b64a188ffe7f646092dbb04f&time=1542102407&iid=Mjc3Mzg2MDk1OQ==&sourcefrom=0'

    # 天天快报
    # url = 'https://kuaibao.qq.com/s/NEW2018120200710400?refer=kb_news&titleFlag=2&omgid=78610c582f61e3b1f414134f9d4fa0ce'
    # url = 'https://kuaibao.qq.com/s/20181201A0VJE800?refer=kb_news&titleFlag=2&omgid=78610c582f61e3b1f414134f9d4fa0ce'
    # 含视频(不处理)
    # url = 'https://kuaibao.qq.com/s/20180906V1A30P00?refer=kb_news&titleFlag=2&omgid=78610c582f61e3b1f414134f9d4fa0ce'
    article_parse_res = loop.run_until_complete(_._parse_article(article_url=url))
    pprint(article_parse_res)
    print(dumps(article_parse_res))
