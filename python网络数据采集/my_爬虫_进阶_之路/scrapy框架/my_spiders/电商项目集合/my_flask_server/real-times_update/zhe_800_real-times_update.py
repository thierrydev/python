# coding:utf-8

'''
@author = super_fazai
@File    : zhe_800_real-times_update.py
@Time    : 2017/11/18 16:00
@connect : superonesfazai@gmail.com
'''

import sys
sys.path.append('..')

from zhe_800_parse import Zhe800Parse
from my_pipeline import SqlServerMyPageInfoSaveItemPipeline

from gc import collect
from settings import (
    IS_BACKGROUND_RUNNING,
    MY_SPIDER_LOGS_PATH,)

from sql_str_controller import z8_select_str_3
from multiplex_code import (
    _get_sku_price_trans_record,
    _get_spec_trans_record,
    _get_stock_trans_record,
    _get_async_task_result,
    _get_new_db_conn,
    _print_db_old_data,)

from fzutils.cp_utils import _get_price_change_info
from fzutils.spider.async_always import *

class Z8Updater(AsyncCrawler):
    """折800常规商品实时更新"""
    def __init__(self, *params, **kwargs):
        AsyncCrawler.__init__(
            self,
            *params,
            **kwargs,
            log_print=True,
            log_save_path=MY_SPIDER_LOGS_PATH + '/折800/实时更新')
        self.tmp_sql_server = None
        self.goods_index = 1
        self.concurrency = 10       # 并发量

    async def _get_db_old_data(self):
        self.tmp_sql_server = SqlServerMyPageInfoSaveItemPipeline()
        result = None
        try:
            result = list(self.tmp_sql_server._select_table(sql_str=z8_select_str_3))
        except TypeError:
            self.lg.error('TypeError错误, 原因数据库连接失败...(可能维护中)')

        await _print_db_old_data(logger=self.lg, result=result)

        return result

    async def _get_new_ali_obj(self, index) -> None:
        if index % 10 == 0:
            try:
                del self.zhe_800
            except:
                pass
            collect()
            self.zhe_800 = Zhe800Parse()

    async def _update_one_goods_info(self, item, index):
        '''
        更新一个goods的信息
        :param item:
        :param index:
        :return: ['goods_id', bool:'成功与否']
        '''
        res = False
        goods_id = item[0]
        await self._get_new_ali_obj(index=index)
        self.tmp_sql_server = await _get_new_db_conn(db_obj=self.tmp_sql_server, index=index, logger=self.lg)
        if self.tmp_sql_server.is_connect_success:
            self.lg.info('------>>>| 正在更新的goods_id为({0}) | --------->>>@ 索引值为({1})'.format(goods_id, index))
            self.zhe_800.get_goods_data(goods_id=goods_id)
            data = self.zhe_800.deal_with_data()
            if data != {}:
                data['goods_id'] = goods_id
                data['shelf_time'], data['delete_time'] = get_shelf_time_and_delete_time(
                    tmp_data=data,
                    is_delete=item[1],
                    shelf_time=item[4],
                    delete_time=item[5])

                # 监控纯价格变动
                price_info_list = old_sku_info = json_2_dict(item[6], default_res=[])
                try:
                    old_sku_info = format_price_info_list(price_info_list=price_info_list, site_id=11)
                except AttributeError:  # 处理已被格式化过的
                    pass
                new_sku_info = format_price_info_list(data['price_info_list'], site_id=11)
                data['_is_price_change'], data[
                    'sku_info_trans_time'], price_change_info = _get_sku_price_trans_record(
                    old_sku_info=old_sku_info,
                    new_sku_info=new_sku_info,
                    is_price_change=item[7] if item[7] is not None else 0,
                    db_price_change_info=json_2_dict(item[9], default_res=[]),
                    old_price_trans_time=item[12],)
                data['_is_price_change'], data['_price_change_info'] = _get_price_change_info(
                    old_price=item[2],
                    old_taobao_price=item[3],
                    new_price=data['price'],
                    new_taobao_price=data['taobao_price'],
                    is_price_change=data['_is_price_change'],
                    price_change_info=price_change_info,)
                if data['_is_price_change'] == 1:
                    self.lg.info('价格变动!!')

                # 监控纯规格变动
                data['is_spec_change'], data['spec_trans_time'] = _get_spec_trans_record(
                    old_sku_info=old_sku_info,
                    new_sku_info=new_sku_info,
                    is_spec_change=item[8] if item[8] is not None else 0,
                    old_spec_trans_time=item[13],)
                if data['is_spec_change'] == 1:
                    self.lg.info('规格属性变动!!')

                # 监控纯库存变动
                data['is_stock_change'], data['stock_trans_time'], data[
                    'stock_change_info'] = _get_stock_trans_record(
                    old_sku_info=old_sku_info,
                    new_sku_info=new_sku_info,
                    is_stock_change=item[10] if item[10] is not None else 0,
                    db_stock_change_info=json_2_dict(item[11], default_res=[]),
                    old_stock_trans_time=item[14],)
                if data['is_stock_change'] == 1:
                    self.lg.info('规格的库存变动!!')

                res = self.zhe_800.to_right_and_update_data(data, pipeline=self.tmp_sql_server)

            else:  # 表示返回的data值为空值
                pass
        else:  # 表示返回的data值为空值
            self.lg.error('数据库连接失败，数据库可能关闭或者维护中')

        index += 1
        self.goods_index = index
        collect()
        await async_sleep(2.)

        return [goods_id, res]

    async def _update_db(self):
        while True:
            self.lg = await self._get_new_logger(logger_name=get_uuid1())
            result = await self._get_db_old_data()
            if result is None:
                pass
            else:
                self.goods_index = 1
                tasks_params_list = TasksParamsListObj(tasks_params_list=result, step=self.concurrency)
                self.zhe_800 = Zhe800Parse()
                index = 1
                while True:
                    try:
                        slice_params_list = tasks_params_list.__next__()
                        # self.lg.info(str(slice_params_list))
                    except AssertionError:  # 全部提取完毕, 正常退出
                        break

                    tasks = []
                    for item in slice_params_list:
                        self.lg.info('创建 task goods_id: {}'.format(item[0]))
                        tasks.append(self.loop.create_task(self._update_one_goods_info(item=item, index=index)))
                        index += 1

                    await _get_async_task_result(tasks=tasks, logger=self.lg)

                self.lg.info('全部数据更新完毕'.center(100, '#'))
            if get_shanghai_time().hour == 0:  # 0点以后不更新
                await async_sleep(60 * 60 * 5.5)
            else:
                await async_sleep(5.5)
            try:
                del self.zhe_800
            except:
                pass
            collect()

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

def _fck_run():
    # 遇到: PermissionError: [Errno 13] Permission denied: 'ghostdriver.log'
    # 解决方案: sudo touch /ghostdriver.log && sudo chmod 777 /ghostdriver.log
    _ = Z8Updater()
    loop = get_event_loop()
    loop.run_until_complete(_._update_db())
    try:
        del loop
    except:
        pass

def main():
    '''
    这里的思想是将其转换为孤儿进程，然后在后台运行
    :return:
    '''
    print('========主函数开始========')
    daemon_init()
    print('--->>>| 孤儿进程成功被init回收成为单独进程!')
    _fck_run()

if __name__ == '__main__':
    if IS_BACKGROUND_RUNNING:
        main()
    else:
        _fck_run()