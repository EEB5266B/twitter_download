import os
import httpx

class remote_check_gen():

    def __init__(self, remote_check, user_name):
        url = remote_check + "api/user/" + user_name + "/media_url/list"

        try:
            response = httpx.get(url)
            response.raise_for_status()  # 检查请求是否成功
            data = response.json()
            if isinstance(data, list):
                self.remote_check_data = set(data)
            else:
                print("API 返回的数据不是列表，已使用空集初始化")
                self.remote_check_data = set()
        except (httpx.RequestException, ValueError) as e:
            print(f"获取 API 缓存失败: {e}，已使用空集初始化")
            self.remote_check_data = set()

    def is_present(self, element):
        if element in self.remote_check_data:
            return False
        else:
            return True