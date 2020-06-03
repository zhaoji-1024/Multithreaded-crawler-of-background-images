import  requests
from lxml import etree
import queue
import threading
import time

class ImageSpider(object):

    def __init__(self):
        self.base_url = "http://sc.chinaz.com/tupian/beijingtupian_{}.html"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"
        }
        self.list_url_q = queue.Queue(80)
        for i in range(2,79):
            self.list_url_q.put(self.base_url.format(i))
        self.img_urls_q = queue.Queue(3000)

    # 请求方法
    def get_html_text(self, url):
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.content.decode()
        else:
            return None


    # 解析列表页方法
    def parse_list_page(self, text):
        html = etree.HTML(text)
        images_tag = html.xpath("//div[@class='box picblock col3']")
        items = []
        for i_t in images_tag:
            item = {}
            item["title"] = i_t.xpath(".//img/@alt")[0]
            item["url"] = i_t.xpath(".//img/@src2")[0]
            self.img_urls_q.put(item)

    #请求列表页获取img的url的方法
    def requests_list_page(self):
        while self.list_url_q.not_empty:
            list_url = self.list_url_q.get()
            text = self.get_html_text(list_url)
            self.parse_list_page(text)
            self.list_url_q.task_done()


    #保存图片到本地
    def save_imgs_toLocal(self):
        while self.img_urls_q.not_empty:
            item = self.img_urls_q.get()
            img_title = item["title"]
            img_url = item["url"]
            with open("./data/多线程背景图片爬虫/" + img_title + ".jpg", "wb") as fp:
                fp.write(requests.get(img_url, headers=self.headers).content)
                print(img_title + "save to local direction sucessfully...")
                self.img_urls_q.task_done()


    #主方法
    def run(self):
        thread_list = []

        for i in range(5):
            thread_list_page = threading.Thread(target=self.requests_list_page)
            thread_list.append(thread_list_page)

        for i in range(10):
            thread_img_Save = threading.Thread(target=self.save_imgs_toLocal)
            thread_list.append(thread_img_Save)

        for t in thread_list:
            #将子线程全部设置为守护线程后启动全部子线程，这意味着当主线程结束时，全部子线程也结束运行
            t.setDaemon(True)
            t.start()

        #阻塞主线程，待队列list_url_q和img_urls_q中的任务被全部接收并处理完成后再解除阻塞
        #这里的接收并处理完成指的是队列q执行q.get()和q.task_done()方法
        #这样就会使得程序执行到此时会判断两个队列是否全部为空即子线程任务是否全部完成
        #若子线程任务全部完成则解除阻塞，主线程结束，子线程也随之结束
        #若子线程任务未全部完成，则会使主线程阻塞，那么子线程将继续执行其任务直到全部完成
        self.list_url_q.join()
        self.img_urls_q.join()



if __name__ == '__main__':
    isr = ImageSpider()
    isr.run()