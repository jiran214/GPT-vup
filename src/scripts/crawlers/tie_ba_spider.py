import requests

try:
    from parsel import Selector
    import pymysql
except ImportError::
    raise 'Please run pip install parsel pymysql cryptography'


from src.db.mysql import get_session
from src.db.models import TieBa

pymysql.install_as_MySQLdb()

# connecting to a MySQL database with user and password

session = requests.session()
prefix_url = 'https://tieba.baidu.com'
ba_url = 'https://tieba.baidu.com/f?kw={kw}&ie=utf-8&tp=0&pn={pn}'
tie_url = 'https://tieba.baidu.com/p/{tie_id}?pn={pn}'


class Ba:

    def __init__(self, kw, max_ba_pn, max_tie_pn, start_ba_pn=1, start_tie_pn=1, max_str_length=400):
        self.kw = kw
        self.start_ba_pn = start_ba_pn
        self.start_tie_pn = start_tie_pn
        self.max_ba_pn = max_ba_pn
        self.max_tie_pn = max_tie_pn
        self.max_str_length = max_str_length

    def get_tie_list(self, pn):
        r = session.get(ba_url.format(kw=self.kw, pn=pn))
        sl = Selector(text=r.text)

        href_list = sl.xpath("""//div[@class='threadlist_title pull_left j_th_tit ']//a/@href""").getall()
        tie_id_list = [href.split('/')[-1] for href in href_list]
        yield from tie_id_list

    def get_tie_detail(self, tie_id, pn):
        r = session.get(tie_url.format(tie_id=tie_id, pn=pn))
        sl = Selector(text=r.text)
        tie_item = sl.xpath("""//div[@class='d_post_content_main ']""")

        data_list = []
        for tie in tie_item:
            data_dict = {
                'tid': tie_id,
                'hash_id': '1',
                'content': '',
                # 'embedding': None
            }
            content_list = tie.xpath(
                """.//div[@class='d_post_content j_d_post_content ']//text()""").getall()
            content = ' '.join(content_list).strip().replace(' ', '')
            data_dict['hash_id'] = str(hash(content))
            data_dict['content'] = content

            # 过滤
            if len(content.replace(' ', '')) > 10:
                if len(content.replace(' ', '')) < self.max_str_length:
                    data_list.append(data_dict)
                else:
                    print('数据异常 ->', content)

        if data_list:
            self.save(data_list)

        if next_pn := sl.xpath(
                """//li[@class='l_pager pager_theme_5 pb_list_pager']/span/following-sibling::a[1]/text()""").get():
            next_args = (tie_id, next_pn)
            return next_args
        return None

    def save(self, data_list):
        with get_session() as s:
            for data_dict in data_list:
                s.add(TieBa(**data_dict))

    def depth_first_run(self):
        for ba_pn in range(self.start_ba_pn, self.max_ba_pn + 1):
            print(f'正在爬取{self.kw}吧 第{ba_pn}页...')
            for tid in self.get_tie_list(ba_pn):
                next_args = (tid, self.start_tie_pn)
                while 1:
                    print(f'正在爬取{self.kw}吧{tid}贴 第{next_args[1]}页...', end='')
                    next_args = self.get_tie_detail(*next_args)
                    print('完成！')
                    if not next_args or int(next_args[1]) == self.max_tie_pn+1:
                        break
        print('over')


if __name__ == '__main__':
    Ba(kw='孙笑川', max_ba_pn=1, max_tie_pn=1).depth_first_run()