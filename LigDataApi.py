import base64
import ctypes
from math import pi
import os
import tempfile
import requests
import bpy
from urllib3.exceptions import HTTPError

# current_path = os.path.dirname(os.path.realpath(__file__))
# dylib_path = os.path.join(current_path, 'LiGDataApi.dylib')
# Url_Path = ctypes.cdll.LoadLibrary(dylib_path)
# # 設置回傳值型態
# Url_Path.get_LOGIN_URL.restype = ctypes.c_char_p
# Url_Path.get_DOWNLOAD_URL.restype = ctypes.c_char_p
# Url_Path.get_UPLOAD_URL.restype = ctypes.c_char_p
# Url_Path.get_SYNC_URL.restype = ctypes.c_char_p
# Url_Path.get_SCENE_LIST.restype = ctypes.c_char_p

class ApiClient:
    _client = None
    @staticmethod
    def shared():
        if not ApiClient._client:
            ApiClient._client = ApiClient()
        return ApiClient._client

    def __init__(self):
        self._errors = None
        self.token = None

    @property
    def errors(self):
        return self._errors

    def get_token(self):
        return self.token

    def authenticated(self):
        return self.token is not None

    def login(self, email, pwd):
        # login_url = 'https://api.lightgen.space/api/login'
        login_url = 'https://api.lig.com.tw/api/v1/login'
        try:
            r = requests.post(login_url, json={"user": {"email": email, "password": pwd}})
            if r.status_code != 200:
                self._errors = r.text
                return False
            self.token = r.json()['token']
            return True
        except HTTPError as err:
            self._errors = err
        return False

    def logout(self):
        self.token = None

    def auth_headers(self):
        if self.token is None:
            return {'User-Agent': 'Blender LiG Plugin Client'}
        return {'Authorization': 'Bearer ' + self.token, 'User-Agent': 'Blender LiG Plugin Client'}

    def download_ar_objects(self, scene_id):
        download_url = 'https://api.lig.com.tw/api/v1/ar_objects_from_scene/'
        if ' ' in str(scene_id):   # if scan_id contains space, remove it
            scene_id = scene_id.split()[0]
        r = requests.get(download_url + scene_id, headers=self.auth_headers())
        if not r:
            return
        
        #print('顯示 scene_id', scene_id)

        ar_objects = r.json()['ar_objects']
        return ar_objects

    def download(self, url):
        r = requests.get(url)
        if r.status_code != 200:
            return None

        fn = os.path.join(tempfile.gettempdir(), os.path.basename(url))
        with open(fn, 'wb') as tf:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    tf.write(chunk)
        
        # tf = open(fn, 'wb+')
        # if not tf:
        #     return None
        # tf.write(r.content)
        return tf

    #檔案上傳
    def upload(self, ar_object=dict()):
        upload_url = 'https://api.lig.com.tw/api/v1/ar_objects/'
        ar_id = ar_object.get('id', -1)
        if ar_id < 1:
            return
        payload = {
            'location': ar_object['location'],
            'zoom': ar_object['zoom'],
            'model': ar_object['model'],
        }
        try:
            r = requests.patch(upload_url + str(ar_id), json=payload, headers=self.auth_headers())
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
    #檔案上傳結尾
    
        # File upload
    def upload_files(self, filepaths):
        upload_url = 'https://api.lig.com.tw/api/v1/assets'
        assets = []
        for fp in filepaths:
            filename = os.path.basename(fp)
            ext = fp.split(".")[-1]

            f = open(fp, "rb")
            data = f.read()
            encrypted = base64.b64encode(data).decode('UTF-8')
            assets.append({"filename": filename, "ext": ext, "data": encrypted, "client_id": 1})
        payload = {"assets": assets}

        try:
            r = requests.post(upload_url, json=payload, headers=self.auth_headers())
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)

    def sync_with_server(self, obj, operator):
        sync_url = 'https://api.lig.com.tw/api/v1/ar_objects/%r'
        def radians_to_degree(deg):
            return deg * 180 / pi
        data = {
            "location": {
                "x": obj.location[0],
                "y": obj.location[1],
                "z": obj.location[2],
                "rotate_x": radians_to_degree(obj.rotation_euler[0]),
                "rotate_y": radians_to_degree(obj.rotation_euler[1]),
                "rotate_z": radians_to_degree(obj.rotation_euler[2]),
            },
            "model": {
                "type": obj.lig_ar_obj.model_type,
                "fields": {},
            },
        }
        r = requests.patch(sync_url % obj.lig_ar_obj.ar_id, json=data, headers=self.auth_headers())
        return r

    def scene_list(self):
        scene_list_url = 'https://api.lig.com.tw/api/v1/scenes'
        r = requests.get(scene_list_url, headers=self.auth_headers())
        if not r:
            return []

        return r.json()['scenes']