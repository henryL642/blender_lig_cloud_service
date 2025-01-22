

bl_info = {
    "name": "LiG AR Cloud",
    "author": "Plain Wu <plainwu@gmail.com> Druid Ting<druiddin@gmail.com> Henry Lin<henry.lin@lig.com.tw>",
    "version": (1, 4, 3),
    "blender": (4, 3, 0),
    "location": "Scene->LiG Cloud Service",
    "description": "A Blender addon to interact with cloud services for downloading and updating objects.",
    "warning": "",
    "support": 'OFFICIAL',
    "category": "Import-Export",
    "doc_url": "https://github.com/henryL642/blender_lig_cloud_service/wiki",  # 文檔鏈接
    "tracker_url": "https://github.com/henryL642/blender_lig_cloud_service/issues",  # Issue Tracker
}

if "bpy" in locals():
    import importlib
    importlib.reload(LigDataApi)
else:
    from . import LigDataApi

import os
import subprocess
import sys
import bpy
import requests
import math
import json
import enum
import concurrent.futures
from PIL import Image
from datetime import datetime
from math import degrees, pi
from urllib.parse import urlparse
from mathutils import Vector
from bpy_extras.image_utils import load_image
from bpy_extras.io_utils import ImportHelper, ExportHelper
from math import radians

# 需要安装的依赖包
REQUIRED_PACKAGES = [
    "requests",
    "Pillow",
]

from bpy.props import (
    StringProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    FloatVectorProperty,
    CollectionProperty,
    PointerProperty,
)

from bpy.types import (
    Context,
    Operator,
    AddonPreferences,
    PropertyGroup,
    UIList,
    Panel,
)

from bpy_extras.object_utils import (
    object_data_add,
) 

class ARObjectType(enum.Enum):
    IMAGE = 5
    VIDEO = 9
    MODEL_3D = 8
    ARINFOBALL = 13    
    PARTICLE = 16

from bpy.types import Panel, Operator, PropertyGroup # type: ignore

#====================================================
# 1) 自訂屬性: ARJsonProperties
#====================================================
class LiGAccount:
    email: StringProperty(name="Light Space Acount(email) ", subtype='NONE',)   # type: ignore
    password: StringProperty(name="Password ", subtype='PASSWORD',) # type: ignore
    token: StringProperty(name="Access Token", subtype='NONE',) # type: ignore
class ARJsonProperties(PropertyGroup):
    # 儲存整包 JSON 的字串
    json_data: StringProperty(
        name="AR JSON Data",
        description="Stores the entire AR object JSON as string",
        default=""
    )   # type: ignore

    model_type: StringProperty(name="Model Type", default="")  # type: ignore
    obj_name: StringProperty(name="Object Name", default="")  # type: ignore
    #------------------------------------------------
    # location.x, location.y, location.z, rotate_x, rotate_y, rotate_z
    #------------------------------------------------
    loc_x: bpy.props.FloatProperty(name="X")  # type: ignore
    loc_y: bpy.props.FloatProperty(name="Y")  # type: ignore
    loc_z: bpy.props.FloatProperty(name="Z")  # type: ignore
    rotate_x: bpy.props.FloatProperty(name="RotX")    # type: ignore
    rotate_y: bpy.props.FloatProperty(name="RotY")    # type: ignore
    rotate_z: bpy.props.FloatProperty(name="RotZ")    # type: ignore

    #------------------------------------------------
    # zoom.x, zoom.y, zoom.z
    #------------------------------------------------
    zoom_x: bpy.props.FloatProperty(name="ZoomX") # type: ignore
    zoom_y: bpy.props.FloatProperty(name="ZoomY") # type: ignore
    zoom_z: bpy.props.FloatProperty(name="ZoomZ") # type: ignore

    type: bpy.props.IntProperty(name="Object Type") # type: ignore
    #------------------------------------------------
    # model.fields - 以下屬性都在 fields 裡：共通屬性
    #------------------------------------------------
    visible_distance: bpy.props.FloatProperty(name="VisibleDist", default=20.0)   # type: ignore
    is_ignore: bpy.props.BoolProperty(name="Is Ignore",default=False) # type: ignore
    face_me: bpy.props.BoolProperty(name="Face Camera",default=False) # type: ignore
    is_hidden: bpy.props.BoolProperty(name="Hidden",default=False) # type: ignore
    is_double_sided: bpy.props.BoolProperty(name="Is Double Side",default=False) # type: ignore
    is_occlusion: bpy.props.BoolProperty(name="Is Occusion",default=False) # type: ignore
    is_allow_pinch: bpy.props.BoolProperty(name="Is Allow Pinch",default=False) # type: ignore
    #------------------------------------------------
    # model.fields - 以下屬性都在 fields 裡：Image
    #------------------------------------------------
    width: bpy.props.FloatProperty(name="Width", default=1.0) # type: ignore
    height: bpy.props.FloatProperty(name="Height", default=1.0)   # type: ignore
    is_size_scale_lock: bpy.props.BoolProperty(name="Lock Aspect Ratio", default= True)  # type: ignore   
    bloom_intensity: bpy.props.FloatProperty(name="Bloom Intensity")    # type: ignore
    bloom_radius: bpy.props.FloatProperty(name="bloom_radius")  # type: ignore
    #------------------------------------------------
    # model.fields - 以下屬性都在 fields 裡：Vedio
    #------------------------------------------------
    hue_angle: bpy.props.StringProperty(name="hue_angle")    # type: ignore  
    hue_range: bpy.props.StringProperty(name="hue_range", default = '20')  # type: ignore  
    saturation: bpy.props.StringProperty(name="saturation", default = '0.5')   # type: ignore  
    is_play: bpy.props.BoolProperty(name="Is Paly", default=False)  # type: ignore
    is_loop_play: bpy.props.BoolProperty(name="Is Loop Play", default=False)  # type: ignore
    #------------------------------------------------
    # model.fields - 以下屬性都在 fields 裡：3DModel
    #------------------------------------------------
    animation_speed: bpy.props.StringProperty(name="Animation Speed", default='1.0') # type: ignore
    start_frame_enabled: bpy.props.BoolProperty(name="Use Start Frame", default=False) # type: ignore
    start_frame_value: bpy.props.IntProperty(name="Start Frame Value")     # type: ignore
    end_frame_enabled: bpy.props.BoolProperty(name="Use Start Frame", default=False) # type: ignore
    end_frame_value: bpy.props.IntProperty(name="Start Frame Value")    # type: ignore

    fps: bpy.props.StringProperty(name="FPS",default="24.0")  # type: ignore
    multiply_number: bpy.props.StringProperty(name="Multiply Number") # type: ignore
    multiply_radius: bpy.props.StringProperty(name="Multiply Radius")  # type: ignore
    multiply_range: bpy.props.StringProperty(name="Multiply_Range")  # type: ignore
    multiply_is_zero_y: bpy.props.BoolProperty(name="multiply_is_zero_y", default = False)  # type: ignore
    #------------------------------------------------
    # model.fields - 以下屬性都在 fields 裡：ARInfoBall
    #------------------------------------------------
    floor_count: bpy.props.IntProperty(name="Floor Count")  # type: ignore
    floor_height: bpy.props.FloatProperty(name="Floor Height")  # type: ignore
    floor_gap: bpy.props.FloatProperty(name="Floor Gap") # type: ignore
    face_width: bpy.props.FloatProperty(name="Face Width")    # type: ignore
    floor_count: bpy.props.IntProperty(name="Floor Count") # type: ignore
    face_gap: bpy.props.FloatProperty(name="Face Gap")  # type: ignore
    speed: bpy.props.FloatProperty(name="Speed") # type: ignore
    floor_angles: bpy.props.FloatVectorProperty(
                    name="Floor Angles",
                    description="Stores a vector of 3 floats",
                    size=3,  # 長度為3
                    default=(0.0, 0.0, 0.0)  # 初始值
                    )   # type: ignore
    face_gap_list: bpy.props.FloatVectorProperty(
                    name="Gap List",
                    description="Stores a vector of 3 floats",
                    size=3,  # 長度為3
                    default=(0.0, 0.0, 0.0)  # 初始值
                    )   # type: ignore
    #------------------------------------------------
    # model.fields - 以下屬性都在 fields 裡：Particle
    #------------------------------------------------
    particle_birth_rate: FloatProperty(
        name="Birth Rate",
        description="Particle birth rate",
        default=0.0,
        min=0.0,
    )   # type: ignore
    particle_birth_rate_variation: FloatProperty(
        name="Birth Rate Variation",
        description="Variation in particle birth rate",
        default=0.0,
        min=0.0,
    )   # type: ignore
    particle_life_span: FloatProperty(
        name="Life Span",
        description="Particle life span",
        default=0.0,
        min=0.0,
    )   # type: ignore
    particle_life_span_variation: FloatProperty(
        name="Life Span Variation",
        description="Variation in particle life span",
        default=0.0,
        min=0.0,
    )   # type: ignore
    particle_velocity: FloatProperty(
        name="Velocity",
        description="Particle velocity",
        default=0.0,
        min=0.0,
    )   # type: ignore
    particle_velocity_variation: FloatProperty(
        name="Velocity Variation",
        description="Variation in particle velocity",
        default=0.0,
        min=0.0,
    )   # type: ignore

    #------------------------------------------------
    # actions, transparency, events, sub_events, is_child
    # actions / events / sub_events 可能是清單或字串
    # 這裡先用 StringProperty 簡單儲存
    #------------------------------------------------
    actions: bpy.props.StringProperty(name="Actions") # type: ignore
    # transparency: bpy.props.FloatProperty(name="Transparency", default=1.0)   # type: ignore
    transparency: FloatProperty(
        name="Transparency",
        description="Transparency of the object",
        default=1.0,  # 默认值
        min=0.0,      # 最小值
        max=1.0,      # 最大值
    )   # type: ignore
    events: bpy.props.StringProperty(name="Events")   # type: ignore
    sub_events: bpy.props.StringProperty(name="Sub Events")   # type: ignore
    is_child: bpy.props.BoolProperty(name="Is Child",default = False) # type: ignore
class LiGToggleProperties(PropertyGroup):
    show_basic_data: bpy.props.BoolProperty(name="Show Basic Data", default=False)  # type: ignore
    show_model_fields: bpy.props.BoolProperty(name="Show Model Fields", default=True)   # type: ignore
    show_events: bpy.props.BoolProperty(name="Show Events", default=False)  # type: ignore
class TargetObjectItem(PropertyGroup):
    """目標物件列表項目"""
    name: bpy.props.StringProperty(name="物件名稱") # type: ignore
class LIGASSET_UploadItem(PropertyGroup):
    text: bpy.props.StringProperty(name="Upload Text", default="", subtype='FILE_PATH') # type: ignore
class SceneProperty(PropertyGroup):
    lid: StringProperty(name='LiG Scene ID', subtype='NONE')    # type: ignore
class ScenesProperty(PropertyGroup):
    name: StringProperty(name='LiG Scene', subtype='NONE')  # type: ignore
class ActionValuePropertyGroup(PropertyGroup):
    key: bpy.props.StringProperty(name="Key")   # type: ignore
    value: bpy.props.StringProperty(name="Value")    # type: ignore
class ActionPropertyGroup(PropertyGroup): 
    action_id: bpy.props.StringProperty(name="Action ID")  # type: ignore
    action_values: bpy.props.CollectionProperty(type=ActionValuePropertyGroup) # type: ignore
class ActionsPropertyGroup(PropertyGroup):
    actions_values:StringProperty() # type: ignore
    actions: bpy.props.CollectionProperty(type=ActionPropertyGroup)  # type: ignore
#====================================================
# 2) Parameters: 
#====================================================
# 定義事件名稱及其 ID
EVENTS_ENUM = [
    ('1', "Touch", "點擊事件"),
    ('6', "Location", "觸發位置事件"),
    ('7', "lookAt", "觸發注視事件"),
    ('8', "repeatForver", "重複觸發"),
    ('9', "Time", "觸發時間事件"),
    ('10', "sceneStart", "觸發場景開始"),
    ('11', "proximityEnter", "觸發進入區域"),
    ('12', "promityLeave", "觸發離開區域"),
    ('13', "Period", "觸發時間段事件")
]

ACTION_PARAMETERS = {
    13: {  # 物件旋轉
        "direction_x": 0.0,
        "direction_y": 0.0,
        "direction_z": 0.0
    },
    6: {  # 物件移動
        "move_x": 0.0,
        "move_y": 0.0,
        "move_z": 0.0
    },
    15: {  # 物件縮放
        "scale_x": 1.0,
        "scale_y": 1.0,
        "scale_z": 1.0
    }
}

action_id_data = {
    3: 'movement',
    5: 'display',
    6: 'play',
    7: 'show',
    8: 'openURL',
    9: 'hidden',
    10: 'animspeed',
    11: 'animcontrol',
    12: 'anirepeat',
    13: 'rotation',
    15: 'scale',
    16: 'fadein',
    17: 'fadeout',
    18: 'fadeOpacityBy',
    19: 'fadeOpacityTo',
    20: 'rectMove',
    21: 'circle moving',
    22: 'moveToFace',
    23: 'playAudio',
    24: 'playImpactFeedback',
    25: 'switchScene',
    26: 'uiAction',
    27: 'game',

}

events_id_data = {
    1: 'click',
    6: 'look_at',
    7: 'repeat',
    8: 'moments',
    9: 'sceneStart',
    10: 'proximityEnter',
    11: 'proximityLeave',
    12: 'period',
}

key_to_chinese = {
    'visible_distance':'表示距離',
    'width': '幅',
    'height': '高さ',
    'face_me': '向ける',
    'is_ignore': '距離無視',
    'is_hidden':'非表示',
    'is_size_scale_lock':'アスペクト比',
    'is_double_sided':'両面',
    'animation_speed':'動畫速度',
    'start_frame':'起始幀格',
    'end_frame':'結束幀格',
    'fps':'幀率',
    'multiply_number':'增殖數量',
    'multiply_radius':'增殖半徑',
    'multiply_range':'增殖範圍',
    'multiply_is_zero_y':'平面增殖',
    'is_occlusion':'透明且遮擋',
    'bloom_intensity':'光暈強度',
    'bloom_radius':'光暈半徑',
}

evnet_name_map = {
    1:"Touch",
    5:"Location",
    6:"LootAt",
    7:"RepeatForver",
    8:"Time",
    9:"SceneStart",
    10:"ProximityEnter",
    11:"ProximityLeave",
    12:"Period",
}

action_name_map = {
    3:"move",
    6:"playVideo",
    7:"showHiddenNode",
    8:"openWeb",
    9:"hiddenNode",
    10:"animateSpeed",
    11:"animateControl",
    12:"animateRepeatCount",
    13:"rotateBy",
    15:"scale",
    19:"fadeOpacityTo",
    21:"curveMove",
    22:"moveToFace",
    23:"playAudio",
    24:"playImpactFeedback",
    25:"switchScene",
    26:"uiAction",
    27:"game",
    28:"moveTo",
    33:"aim",
    34:"stopanimation",
    35:"disable",
    36:"enable",
    37:"panoramaurl",
    39:"aibot",
    40:"switchBackScene",
    41:"openmap",
    44:"callapi",
}

# 用於存儲複製的 events 數據
copied_events = None
alignment_value = None  # 存儲對齊值
alignment_axis = None  # 存儲對齊的軸

#====================================================
# 2) Functions: 
#====================================================
def install_packages():
    # 获取 Blender 的 Python 解释器路径
    python_exe = sys.executable

    # 安装每个依赖包
    for package in REQUIRED_PACKAGES:
        try:
            # 检查包是否已安装
            __import__(package)
        except ImportError:
            # 如果未安装，则使用 pip 安装
            print(f"Installing {package}...")
            subprocess.check_call([python_exe, "-m", "pip", "install", package])

def download_json_from_server(url, local_filepath):
    """ 從伺服器下載 JSON, 寫入 local_filepath """
    resp = requests.get(url)
    resp.raise_for_status()  # 若非 200 會丟出錯誤
    data_str = resp.text
    with open(local_filepath, "w", encoding="utf-8") as f:
        f.write(data_str)
    print(f"Downloaded JSON from {url} -> {local_filepath}")

def load_json_to_blender(obj, local_filepath):
    """
    讀取檔案內的 JSON，寫入 obj.json_props.json_data
    再將需要在 UI 顯示/編輯的欄位同步到對應 Blender 屬性。
    """
    with open(local_filepath, "r", encoding="utf-8") as f:
        data_str = f.read()
    obj.json_props.json_data = data_str
    data = json.loads(data_str)
    obj_type = data.get("model").get('type')
    sync_from_json(obj,obj_type)

def save_json_to_file(obj, local_filepath):
    """ sync_to_json(obj) -> 寫回 local_filepath """    
    with open(local_filepath, "w", encoding="utf-8") as f:
        f.write(obj.json_props.json_data)
    print(f"Saved JSON to {local_filepath}")

def sync_from_json(obj_name,obj_type):
    """
    解析 obj.json_props.json_data ==> ARJsonProperties。
    """
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f'Object "{obj_name}" not found')
        return

    if hasattr(obj, 'json_props'):        
        props = obj.json_props
        if not props.json_data:
            return
        try:
            data = json.loads(props.json_data)  # Json data 轉文字
        except json.JSONDecodeError:
            print("Warning: JSON decode error.")
            return

        loc = data.get('location')
        # 位置 & 旋轉
        props.loc_x = loc.get('x')
        props.loc_y = loc.get('y')
        props.loc_z = loc.get('z')
        props.rotate_x = loc.get('rotate_x')
        props.rotate_y = loc.get('rotate_y')
        props.rotate_z = loc.get('rotate_z')

        # zoom
        zoom = data.get("zoom", {})
        props.zoom_x = zoom.get("x", 1.0)
        props.zoom_y = zoom.get("y", 1.0)
        props.zoom_z = zoom.get("z", 1.0)

        # model / fields
        props.obj_name = str(data['id'])+"-"+data['name']

        model = data.get("model", {})
        props.model_type = str(model.get("type", ""))
        fields = model.get("fields", {})

        props.visible_distance = fields.get("visible_distance", 20.0)
        props.is_ignore = fields.get("is_ignore", False)
        props.face_me = fields.get("face_me", False)
        props.is_hidden = fields.get("is_hidden", False)
        props.is_double_sided = fields.get("is_double_sided", False)
        props.is_occlusion = fields.get("is_occlusion", False)
        props.is_allow_pinch = fields.get("is_allow_pinch", False)

        if obj_type == ARObjectType.IMAGE.value:
            # image
            props.width = fields.get("width", 1.0)
            props.height = fields.get("height", 1.0)
            props.is_size_scale_lock = fields.get("is_size_scale_lock", True)
            props.bloom_intensity = fields.get("bloom_intensity", 0.0)
            props.bloom_radius = fields.get("bloom_radius", 0.0)

        if obj_type == ARObjectType.VIDEO.value:
            # video
            props.hue_angle = str(fields.get("hue_angle", ""))
            props.hue_range = str(fields.get("hue_range", ""))
            props.saturation = str(fields.get("saturation", 0.5))
            props.is_play = fields.get("is_play", False)
            props.is_loop_play = fields.get("is_loop_play", False)

        if obj_type == ARObjectType.MODEL_3D.value:
        # 3D Model
            props.animation_speed = str(fields.get("animation_speed", ""))
            start_frame_val = fields.get("start_frame", None)
            if start_frame_val is None:
                props.start_frame_enabled = False
            else:
                props.start_frame_enabled = True
                props.start_frame_value = int(start_frame_val)
            end_frame_val = fields.get("end_frame", None)
            if end_frame_val is None:
                props.end_frame_enabled = False
            else:
                props.end_frame_enabled = True
                props.end_frame_value = int(end_frame_val)    
            props.fps = str(fields.get("fps", ""))
            props.multiply_number = str(fields.get("multiply_number", ""))
            props.multiply_radius = str(fields.get("multiply_radius", ""))
            props.multiply_range = str(fields.get("multiply_range", ""))
            props.multiply_is_zero_y = fields.get("multiply_is_zero_y", False)

        if obj_type == ARObjectType.ARINFOBALL.value:
            # ARInfoBall
            props.floor_count = fields.get("floor_count", 0)
            props.floor_height = fields.get("floor_height", 0.0)
            props.floor_gap = fields.get("floor_gap", 0.0)
            props.face_width = fields.get("face_width", 0.0)
            props.face_gap = fields.get("face_gap", 0.0)
            props.speed = fields.get("speed", 0.0)
            floor_angles = fields.get("floor_angles", [0.0,0.0,0.0])
            if len(floor_angles) == 3:
                props.floor_angles = floor_angles
            face_gap_list = fields.get("face_gap_list", [0.0,0.0,0.0])
            if len(face_gap_list) == 3:
                props.face_gap_list = face_gap_list

        if obj_type == ARObjectType.PARTICLE.value:
            # Particle
            props.particle_birth_rate = fields.get("particle_birth_rate", 0.0)
            props.particle_birth_rate_variation = fields.get("particle_birth_rate_variation", 0.0)
            props.particle_life_span = fields.get("particle_life_span", 0.0)
            props.particle_life_span_variation = fields.get("particle_life_span_variation", 0.0)
            props.particle_velocity = fields.get("particle_velocity", 0.0)
            props.particle_velocity_variation = fields.get("particle_velocity_variation", 0.0)

        # actions
        actions_val = data.get("actions", None)
        props.actions = str(actions_val) if actions_val is not None else ""

        # transparency
        props.transparency = data.get("transparency", 1.0)

        # events
        events_val = data.get("events", None)
        props.events = str(events_val) if events_val is not None else ""

        # sub_events
        sub_val = data.get("sub_events", None)
        props.sub_events = str(sub_val) if sub_val is not None else ""

        # is_child
        props.is_child = data.get("is_child", False)
    else:
        print(f'Object "{props.name}" dese not have "json_props"')

def sync_to_json(obj_name,obj_type):  #ARJsonProperties 中的屬性值寫回 obj.json_props.json_data，
    """
    將 ARJsonProperties 中的屬性值寫回 obj.json_props.json_data，
    以維持整個 JSON 原結構。
    """
    obj = bpy.data.objects.get(obj_name)
    props = obj.json_props
    if not props.json_data:
        return
    try:
        data = json.loads(props.json_data)
    except json.JSONDecodeError:
        print("Warning: JSON decode error.")
        return
    
    # location
    if "location" not in data:
        data["location"] = {}

    data["location"]["x"] = props.loc_x
    data["location"]["y"] = props.loc_y
    data["location"]["z"] = props.loc_z
    data["location"]["rotate_x"] = props.rotate_x
    data["location"]["rotate_y"] = props.rotate_y
    data["location"]["rotate_z"] = props.rotate_z

    # zoom
    if "zoom" not in data:
        data["zoom"] = {}
    data["zoom"]["x"] = props.zoom_x
    data["zoom"]["y"] = props.zoom_y
    data["zoom"]["z"] = props.zoom_z

    # model
    data.setdefault("model", {})
    data["model"].setdefault("fields", {})
    fields = data["model"]["fields"]

    fields["visible_distance"] = props.visible_distance
    fields["is_ignore"] = props.is_ignore
    fields["face_me"] = props.face_me
    fields["is_hidden"] = props.is_hidden
    fields["is_double_sided"] = props.is_double_sided
    fields["is_occlusion"] = props.is_occlusion
    fields["is_allow_pinch"] = props.is_allow_pinch

    if obj_type == ARObjectType.IMAGE.value: #image
        fields["width"] = props.width
        fields["height"] = props.height
        fields["is_size_scale_lock"] = props.is_size_scale_lock
        fields["bloom_intensity"] = props.bloom_intensity
        fields["bloom_radius"] = props.bloom_radius
    if obj_type == ARObjectType.VIDEO.value: # video
        fields["hue_angle"] = float(props.hue_angle) if props.hue_angle else None
        fields["hue_range"] = float(props.hue_range) if props.hue_range else None
        fields["saturation"] = float(props.saturation) if props.saturation else None
        fields["is_play"] = props.is_play
        fields["is_loop_play"] = props.is_loop_play

    if obj_type == ARObjectType.MODEL_3D.value:  # 3D Model
        fields["animation_speed"] = float(props.animation_speed) if props.animation_speed else None
        fields["start_frame"] = props.start_frame_value
        fields["end_frame"] = props.end_frame_value
        fields["fps"] = float(props.fps) if props.fps else None
        fields["multiply_number"] = float(props.multiply_number) if props.multiply_number else None
        fields["multiply_radius"] = props.multiply_radius
        fields["multiply_range"] = props.multiply_range
        fields["multiply_is_zero_y"] = props.multiply_is_zero_y

    if obj_type == ARObjectType.ARINFOBALL.value:  # arinfoball
        fields["floor_count"] = props.floor_count
        fields["floor_height"] = props.floor_height
        fields["floor_gap"] = props.floor_gap
        fields["face_width"] = props.face_width
        fields["face_gap"] = props.face_gap
        fields["speed"] = props.speed
        fields["floor_angles"] = list(props.floor_angles)
        fields["face_gap_list"] = list(props.face_gap_list)

    if obj_type == ARObjectType.PARTICLE.value:  # particle
        fields["particle_birth_rate"] = props.particle_birth_rate
        fields["particle_birth_rate_variation"] = props.particle_birth_rate_variation
        fields["particle_life_span"] = props.particle_life_span
        fields["particle_life_span_variation"] = props.particle_life_span_variation
        fields["particle_velocity"] = props.particle_velocity
        fields["particle_velocity_variation"] = props.particle_velocity_variation

    # actions
    try:
        # 嘗試把 props.actions 當 JSON parse
        data["actions"] = json.loads(props.actions)
    except:
        # 否則存字串
        data["actions"] = props.actions

    # transparency
    data["transparency"] = props.transparency

    # events
    try:
        data["events"] = json.loads(props.events)
    except:
        data["events"] = props.events

    # sub_events
    try:
        data["sub_events"] = json.loads(props.sub_events)
    except:
        data["sub_events"] = props.sub_events

    # is_child
    data["is_child"] = props.is_child

    props.json_data = json.dumps(data, ensure_ascii=False, indent=4)

def extract_events_from_object(obj):
    """從物件中提取 Actions 數據"""
    if hasattr(obj, "json_props") and obj.json_props.json_data:
        data = json.loads(obj.json_props.json_data)
        return data.get("events", [])
    return []

def menu_func_import(self, context):
    pass
    #self.layout.operator(LiGLoginOperator.bl_idname, text="LiG Cloud")

def menu_func_export(self, context):
    pass
    #self.layout.operator(LiGUploader.bl_idname, text="LiG Cloud")

def object_to_collection(obj, target_collection):
    # 從所有集合中移除該物體
    for col in obj.users_collection:
        col.objects.unlink(obj)
    
    # 將物體連接到目標集合
    target_collection.objects.link(obj)
    
    # 遞歸處理所有子物體
    for child in obj.children:
        object_to_collection(child, target_collection)

# 計算只有父物體的數量
def count_objects_in_collection(collection_name):
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        
        # 計算只有父物體的數量
        parent_object_count = sum(1 for obj in collection.objects if not obj.parent or obj.parent.name not in collection.objects)
        
        print(f"'{collection_name}' 中的父物體層級數量: {parent_object_count}")
        return parent_object_count
    else:
        print(f"集合 '{collection_name}' 不存在")
        return 0

#共用函式區---------------------------------------------------------------------------------------------------------------------
def file_name_set(name):
    file_name = f"{name}.json"
    return file_name

def key_set(name):
    file_name = f"{name}_key_recode.txt"
    return file_name

def transform(location_x, location_y, location_z, rotate_x, rotate_y, rotate_z, scale_x, scale_y, scale_z):  
        location_y, location_z = location_z, -location_y # 交換並取反 location_y 和 location_z
        rotate_y, rotate_z = rotate_z, -rotate_y # 交換並取反 rotate_y 和 rotate_z
        scale_y, scale_z = scale_z, scale_y # 交換 scale_x 和 scale_y
        return location_x, location_y, location_z, rotate_x, rotate_y, rotate_z, scale_x, scale_y, scale_z # 回傳轉換後的座標和旋轉角度

def update_json_path(self, context):
    file_path = self.json_path  # 指定文件路径

    if os.path.isfile(file_path):
        try:
            bpy.data.texts.load(file_path)  # 加載文件
            print(f"The file at {file_path} has been loaded.")
        except:
            print(f"Failed to load the file at {file_path}")
    else:
        print(f"No file found at {file_path}")


    """移除選定的目標物件"""
    bl_idname = "object.remove_target_object"
    bl_label = "移除目標物件"

    def execute(self, context):
        target_index = context.scene.target_objects_index
        if target_index >= 0 and target_index < len(context.scene.target_objects):
            context.scene.target_objects.remove(target_index)
            context.scene.target_objects_index -= 1
            self.report({'INFO'}, "已移除目標物件")
        else:
            self.report({'WARNING'}, "請選擇有效的目標物件")
        return {'FINISHED'}

#====================================================
# 3) Class Panel
#====================================================
class LiGPreferences(AddonPreferences, LiGAccount):  #Addon 登入登出界面
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text='LiG Cloud Acount')
        if self.token:
            layout.label(text='Acount : ' + self.email)
            layout.operator(LiGLogoutOperator.bl_idname)
        else:
            layout.prop(self, 'email')
            layout.prop(self, 'password')
            layout.operator(LiGLoginOperator.bl_idname)

class LiGScenePanel(Panel):   #下載LiG 場景列表
    bl_label = "LiG Cloud Service"
    bl_idname = "OBJECT_PT_lig_scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.operator(LiGSetupOperator.bl_idname, text='Refresh Scenes List')
        layout.prop(context.scene, "save_path")
        # prop_search(data, property, search_data, search_property, text='', text_ctxt='', translate=True, icon='NONE', results_are_suggestions=False)
        if len(context.scene.lig_scenes) > 0:
            layout.prop_search(context.scene, "lig_scene", context.scene, "lig_scenes", icon='NONE')
        if context.scene.lig_scene:
            layout.operator(LiGDownloader.bl_idname, text='Download AR Objects',icon='TRIA_DOWN_BAR')

class LIGASSET_PT_Upload(Panel): #檔案上傳server
    bl_label = "Lig-Asset上傳"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Lig-Asset上傳'  # 將此面板放在 Tools 分類中

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("ligasset.add_textfield", text="增加路徑", icon="ADD")
        row.operator("ligasset.remove_textfield", text="移除路徑", icon="REMOVE")
        
        for item in context.scene.ligasset_upload_texts:
            layout.prop(item, "text", text="資產路徑")
        
        layout.operator("ligasset.op_upload", text="上傳至雲端", icon="URL")

class LiG3DVIEWJSONPanel(Panel):  # Json面板-3DVIEW - Main 
    bl_label = "JSON Management"
    bl_idname = "1: OBJECT_PT_data_lig_json"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LiG-JSON'
    bl_order = 1
    
    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and not obj.parent:
            box_json = layout.box()
            box_json.operator('lig.json_refresh', text='JSON Download', icon='FILE_REFRESH')  # 顯示刷新按鈕
            box_json.operator('lig.json_update', text='JSON Refresh', icon='FILE_REFRESH')# 在面板上增加一个更新JSON數據的按鈕            
            box_json.operator('lig.json_upload', text='JSON Upload',icon='URL',text_ctxt='在面板上增加一个上傳JSON數據的按鈕')# 在面板上增加一个上傳JSON數據的按鈕

class LiG_PT_ObjSelection(Panel):   # JSON 3DVIEW - Obj Selection
    bl_label = "Object Selection"
    bl_idname = "2: OBJECT_PT_obj_selection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LiG-JSON'  
    bl_options = {'DEFAULT_CLOSED'}   
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj:
            box_apply = layout.box()
            box_apply.label(text="Object Selected")
            row = box_apply.row()
            row.operator("lig.frame_selected", text="Frame Selected", icon='VIEWZOOM')  # 新增一個移動到中心視角的按鈕            

class LiG_PT_BasicPanel(Panel):  # Json 3DVIEW 面板 - Basic 子面板（2024/12/16）
    bl_label = "Basic Properties (Y-Up)"
    bl_idname = "3: VIEW3D_PT_lig_basic_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LiG-JSON'
    bl_options = {'DEFAULT_CLOSED'} 
    bl_order = 3
    # bl_parent_id = "VIEW3D_PT_lig_json_panel"  # 設置父面板

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj:  # 確保物件存在
            layout.label(text="Basic Parameters (Y UP):")
            layout.label(text="Blender --> AR Coordinates")
            # 添加初始化按鈕
            # layout.operator("object.initialize_custom_props", text="Initialize Custom Properties")

            location = obj.location
            rotation_euler = obj.rotation_euler
            scale = obj.scale
            mapped_location = (location.x, location.y, location.z)
            mapped_rotation = (rotation_euler.x, rotation_euler.z, rotation_euler.y)
            mapped_scale = (scale.x, scale.z, scale.y)

            box = layout.box()
            box.label(text="LocationTransfer")
            rowlx = box.row()
            rowly = box.row()
            rowlz = box.row()
            rowlx.prop(obj, "location", index=0, text=f"Right-Left: {mapped_location[0]:.2f}")
            rowly.prop(obj, "location", index=1, text=f"Front-Back: {mapped_location[2]:.2f}")  # 轉換後 Y
            rowlz.prop(obj, "location", index=2, text=f"UP-Down: {mapped_location[1]*-1:.2f}")  # 轉換後 -Z

            boxr = layout.box()
            boxr.label(text="RotationTransfer")
            rowrx = boxr.row()
            rowry = boxr.row()
            rowrz = boxr.row()
            rowrx.prop(obj, "rotation_euler", index=0, text=f"X: {mapped_rotation[0]:.2f}")
            rowry.prop(obj, "rotation_euler", index=2, text=f"Y: {mapped_rotation[2]:.2f}")  # 轉換後 Y
            rowrz.prop(obj, "rotation_euler", index=1, text=f"Z: {mapped_rotation[1]:.2f}")  # 轉換後 Z            

            boxs = layout.box()
            boxs.label(text="ScaleTransfer")
            rowsx = boxs.row()
            rowsy = boxs.row()
            rowsz = boxs.row()
            rowsx.prop(obj, "scale", index=0, text=f"X: {mapped_scale[0]:.2f}")
            rowsy.prop(obj, "scale", index=2, text=f"Y: {mapped_scale[2]:.2f}")  # 轉換後 Y
            rowsz.prop(obj, "scale", index=1, text=f"Z: {mapped_scale[1]:.2f}")  # 轉換後 Z   

class LIG_PT_JsonPanel(Panel): # JSON 3DVIEW 面板 - Field（2024/12/15）
    bl_label = "Field Management"
    bl_idname = "4: VIEW3D_PT_lig_json_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LiG-JSON'
    bl_options = {'DEFAULT_CLOSED'} 
    bl_order = 4

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and hasattr(obj, "json_props") and obj.json_props.json_data:
            # layout.operator(LIG_OT_SetProperties.bl_idname, text="Set Property")

            data = json.loads(obj.json_props.json_data)
            fields = data['model']['fields']
            model_type = data['model']['type']

            # layout.label(text="Model Fields:")

            if model_type == ARObjectType.IMAGE.value:  # Image
                self.draw_image_fields(layout, obj)
            elif model_type == ARObjectType.VIDEO.value:  # Video
                self.draw_video_fields(layout, obj)
            elif model_type == ARObjectType.MODEL_3D.value:  # 3D Model
                self.draw_3d_model_fields(layout, obj)
            elif model_type == ARObjectType.ARINFOBALL.value: # InfoBall v1.0
                self.draw_ARInfoBall_fields(layout, obj)
            elif model_type == ARObjectType.PARTICLE.value: # Particle
                self.draw_particle_fields(layout, obj)                

    def draw_image_fields(self, layout, obj):
        props = obj.json_props
        layout.label(text="Image Parameters:")
        box = layout.box()
        box.label(text="general")   
        col = box.column(align=True)       
        col.prop(props, 'is_child')
        col.prop(props, 'is_allow_pinch')
        col.prop(props, 'is_occlusion')
        col.prop(props, 'is_hidden')
        col.prop(props, 'face_me')
        col.prop(props, 'visible_distance')
        col.prop(props, 'is_ignore')
        col.prop(props, 'transparency')

        box = layout.box()
        box.label(text="image properties") 
        col = box.column(align=True) 
        col.prop(props, 'width')
        col.prop(props, 'height')
        col.prop(props, 'is_double_sided')
        col.prop(props, 'is_size_scale_lock')
        
    def draw_video_fields(self, layout, obj):
        props = obj.json_props
        layout.label(text="Video Parameters:")
        box = layout.box()
        box.label(text="general")   
        col = box.column(align=True)      
        col.prop(props, 'is_child')
        col.prop(props, 'is_allow_pinch')
        col.prop(props, 'is_occlusion')
        col.prop(props, 'is_hidden')
        col.prop(props, 'face_me')
        col.prop(props, 'visible_distance')
        col.prop(props, 'is_ignore')
        col.prop(props, 'transparency')

        box = layout.box()
        box.label(text="keying")  
        col = box.column(align=True)  
        col.prop(props, 'hue_angle')
        col.prop(props, 'hue_range')
        col.prop(props, 'saturation')
        box = layout.box()
        box.label(text="play property")  
        col = box.column(align=True)
        col.prop(props, 'is_play')
        col.prop(props, 'is_loop_play')

    def draw_3d_model_fields(self, layout, obj):
        props = obj.json_props
        layout.label(text="3D Model Parameters:")
        box_g = layout.box()
        box_g.label(text="general")
        col_g = box_g.column(align=True)     
        col_g.prop(props, "is_child")
        col_g.prop(props, "is_allow_pinch")
        col_g.prop(props, "is_occlusion")
        col_g.prop(props, "is_hidden")
        col_g.prop(props, "face_me")
        col_g.prop(props, "visible_distance")
        col_g.prop(props, "is_ignore")
        col_g.prop(props, "transparency")

        box_b = layout.box()
        box_b.label(text="basic property")  
        col_b = box_b.column(align=True)   
        col_b.prop(props, "width")
        col_b.prop(props, "height")
        col_b.prop(props, "is_double_sided")

        box_a = layout.box()
        box_a.label(text="animation property")  
        col_a = box_b.column(align=True)  
        col_a.prop(props, "animation_speed") 
        col_a.prop(props, "start_frame_value") 
        col_a.prop(props, "end_frame_value") 
        col_a.prop(props, "fps") 

        box_m = layout.box()
        box_m.label(text="multiplier property")   
        col_a = box_m.column(align=True)  
        col_a.prop(props, "multiply_number")         
        col_a.prop(props, "multiply_radius")         
        col_a.prop(props, "multiply_range")         
        col_a.prop(props, "multiply_is_zero_y")         

    def draw_ARInfoBall_fields(self, layout, obj):
        props = obj.json_props
        layout.label(text="ArInfoBall v1.0 Parameters:")
        box = layout.box()
        box.label(text="general")
        col = box.column(align=True)     
        col.prop(props, "is_child")
        col.prop(props, "is_allow_pinch")
        col.prop(props, "is_occlusion")
        col.prop(props, "is_hidden")
        col.prop(props, "face_me")
        col.prop(props, "visible_distance")
        col.prop(props, "is_ignore")
        col.prop(props, "transparency")

        box = layout.box()
        box.label(text="layer property")
        col = box.column(align=True)   
        col.prop(props, 'floor_count')
        col.prop(props, 'face_count')
        col.prop(props, 'floor_height')
        col.prop(props, 'face_width')
        box.prop(props, 'floor_gap')
        col.prop(props, 'face_gap_list')
        col.prop(props, 'floor_angles')

    def draw_particle_fields(self, layout, obj):
        props = obj.json_props
        layout.label(text="Particle Parameters:")
        box = layout.box()
        box.label(text="general")
        col = box.column(align=True)     
        col.prop(props, "is_child")
        col.prop(props, "is_allow_pinch")
        col.prop(props, "is_occlusion")
        col.prop(props, "is_hidden")
        col.prop(props, "face_me")
        col.prop(props, "visible_distance")
        col.prop(props, "is_ignore")
        col.prop(props, "transparency")

        box = layout.box()
        box.label(text="partivle property")
        col = box.column(align=True)    
        col.prop(props, 'particle_birth_rate')
        col.prop(props, 'particle_birth_rate_variation')
        col.prop(props, 'particle_life_span')
        col.prop(props, 'particle_life_span_variation')
        col.prop(props, 'particle_velocity')
        col.prop(props, 'particle_velocity_variation')    

class LiG_PT_OBJAlignment(Panel):   # JSON 3DVIEW - Obj Alignment
    bl_label = "Object Alignment"
    bl_idname = "5: OBJECT_PT_obj_alignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LiG-JSON'   
    bl_options = {'DEFAULT_CLOSED'} 
    bl_order = 5

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj:
            box = layout.box()
            box.label(text = "Alignment")
            col = box.column()
            col.label(text="Select above 2 objects to align.")
            col.label(text=f"Selected objects: {len(context.selected_objects)}")

            if len(context.selected_objects)>1:
                if all(obj.parent is None for obj in context.selected_objects):                 
                    x_button = box.operator('lig.alignment',text='X Alignment')
                    x_button.axis = 'X'
                    y_button = box.operator('lig.alignment',text='Y Alignment')
                    y_button.axis = 'Y'
                    z_button = box.operator('lig.alignment',text='Z Alignment')
                    z_button.axis = 'Z'
                else:
                    layout.label(text="All selected objects must be top-level for alignment.")

            #如果對齊值存在，顯示修改及應用按鈕
            global alignment_axis,alignment_value
            if alignment_value is not None:
                box.label(text=f"Current {alignment_axis} Value: {alignment_value:.2f}")
                row = box.row()
                row.prop(context.scene, "alignment_input", text="")
                row.operator("lig.apply_alignment",text = "Apply")

class ActionPanel(Panel): # JSON 3DVIEW - event/action panel
    bl_label = "Event Viewer"
    bl_idname = "6: VIEW3D_PT_action_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LiG-JSON"
    bl_options = {'DEFAULT_CLOSED'} 
    bl_order = 6

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        # 檢查是否存在 events 屬性
        if obj and hasattr(obj, "json_props") and obj.json_props.json_data:                            
            json_data = json.loads(obj.json_props.json_data) 
            events = json_data.get('events',[])
            if events:
                for event in events:
                    # 創建一個 Box，顯示事件 ID
                    event_id = event.get("id")
                    event_name = evnet_name_map.get(event_id, None)
                    event_box = layout.box()
                    event_box.label(text=f"Event: {event_name}")

                    actions = event.get('actions',[])
                    for action in actions:
                        action_id = action.get("id")
                        action_name = action_name_map.get(action_id, None)
                        
                        action_values = action.get("values", {})
                        if action_values:
                            # 確保 action_values 是字典，並且包含有效的結構
                            if isinstance(action_values, dict):
                                # 排序 action_values 根據 group 值
                                sorted_action_values = sorted(
                                    action_values.items(),
                                    key=lambda item: (
                                        item[1].get("group", float("inf")) #確保按 group 排序，無 group 時排最
                                        if isinstance(item[1],dict) else float("inf") # 非字典排最後
                                    )
                            )
                            # 重新構建排序後的字典
                            sorted_action_values = dict(sorted_action_values)
                            action_box = event_box.box()
                            action_box.label(text=f"Action: {action_name}")  
                            # 渲染 UI
                            for action_key, action_value in sorted_action_values.items():
                                row = action_box.row()
                                row.label(text=f"{action_key}: {action_value}")
                        else:
                            action_box.label(text="No values available for this action.")
            else:
                layout.label(text="No events found.")
        else:
            layout.label(text="No data available.")

class EventOperation(Panel):
    bl_label = "Event Operation"
    bl_idname = "7: OBJECT_PT_data_eventOP"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LiG-JSON'
    bl_order = 7   

    def draw(self, context):
        layout = self.layout
        obj = context.object
        # 檢查是否存在 json_props 並且有 events 數據
        if obj and hasattr(obj, "json_props") and obj.json_props.json_data:
            json_data = json.loads(obj.json_props.json_data)
            events = json_data.get('events',[])
            #如果有數據，顯示copy按鈕
            row = layout.row()
            if events:
                row.operator("lig.copy_events", text="Copy Events")
            else:
                row.label(text = "No Event to Copy")

        # 如果有已複製的 events 的數據，顯示Paste按鈕
        row = layout.row()
        if copied_events:
            row.operator("lig.paste_events",text="Paste Event")
            #顯示複製的 events 的數據
            box = layout.box()
            box.label(text="Copied Events Preview:")
            for i,event in enumerate(copied_events):
                box.label(text=f'Event{i+1}:{event}')
        else:
            row.enabled = False
            row.operator("lig.paste_events",text="Paste Event")

        if copied_events:
            row=layout.row()
            row.operator("lig.clean_events",text="Clean Events Paste")

#====================================================
# 4) Class Operation
#====================================================

class LiGDownloader(Operator):  #下載AR物件
    bl_idname = "lig.download"
    bl_label = "Download AR Objects from LiG Cloud"

    def execute(self, context):
        # 初始化
        self.context = context
        self.set_save_path = context.scene.save_path

        # 檢查保存路徑
        if not self._validate_save_path():
            return {'CANCELLED'}

        # 確保用戶已登錄
        self.client = LigDataApi.ApiClient.shared()
        if not self.client.authenticated():
            self.report({'ERROR'}, "Login to LiG Cloud first")
            return {'CANCELLED'}

        # 下載 AR 物件數據
        ar_objects = self.client.download_ar_objects(context.scene.lig_scene)
        parent_col_name = context.scene.lig_scene 
        parent_collection = bpy.data.collections.get(parent_col_name) or CreateCollection.create_collection(parent_col_name)        
        if not ar_objects:
            self.report({'ERROR'}, "No AR objects found to download")
            return {'CANCELLED'}

        # 收集下載任務
        download_tasks = []
        for ar_obj in ar_objects:
            print(ar_obj)
            obj_name = f"{ar_obj['id']}-{ar_obj['name']}"
            obj_type = ar_obj['model']['type']
            urls = self._extract_url(ar_obj)
            if urls:
                if isinstance(urls, list):  # ARINFOBALL has multiple URLs
                    for i, url in enumerate(urls):
                        download_tasks.append((ar_obj, url, i))  # include index for filename
                else:  # single URL for other object types
                    download_tasks.append((ar_obj, urls, 0))
            else:
                self.report({'WARNING'}, f"No URL found for object {obj_name}")

        # 使用 ThreadPoolExecutor 進行多線程下載
        downloaded_items = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._download_file_with_ar_obj, ar_obj, url, idx) for ar_obj, url, idx in download_tasks]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    ar_obj, file_path, idx = future.result()
                    if file_path:
                        downloaded_items.append((ar_obj, file_path, idx))
                    else:
                        self.report({'ERROR'}, f"Failed to download file for {ar_obj['name']}")
                except Exception as e:
                    self.report({'ERROR'}, f"Download failed: {e}")

        # 在主線程中導入下載的模型
        for ar_obj, file_path, idx in downloaded_items:
            obj_name = f"{ar_obj['id']}-{ar_obj['name']}"
            obj_type = ar_obj['model']['type']
            location = self._transform_location(ar_obj['location'])
            rotation = self._transform_rotation(ar_obj['location'])
            scale = self._transform_scale(ar_obj['zoom'])
            jsonfile_name = f"{obj_name}.json"
            json_path = os.path.join(context.scene.save_path, jsonfile_name)
            # 已經存在的物件，更新位置屬性、更新properties
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                obj.location = location
                obj.rotation_euler = rotation
                obj.scale = scale
                obj.json_props.json_data = json.dumps(ar_obj)
                obj_name = obj.json_props.obj_name
            else:  # 新的物件
                if os.path.exists(file_path):      
                    # 1.建立一個空體                
                    empty_obj = self._create_empty_object(obj_name)
                    if obj_type == ARObjectType.ARINFOBALL.value:
                        # 獲取原始 texture.photos 的 URL 列表
                        original_urls = ar_obj['model']['texture']['photos']                        
                        # 收集當前物件所有已下載的圖片路徑（按原始順序）
                        sorted_file_paths = []
                        for url in original_urls:
                            # 根據 URL 在 downloaded_items 中查找對應的本地路徑
                            for downloaded_ar_obj, downloaded_path, idx in downloaded_items:
                                print(f"ar_obj ID: {ar_obj['id']}, file_path: {file_path}, idx: {idx}")
                                if downloaded_ar_obj['id'] == ar_obj['id'] and url in downloaded_ar_obj['model']['texture']['photos'][idx]:
                                    sorted_file_paths.append(downloaded_path)
                                    break
                        # 將排序後的圖片路徑傳遞給 _create_arinfoball_layers
                        self._create_arinfoball_layers(empty_obj, ar_obj['model']['fields'], sorted_file_paths)            
                        self._set_empty_object(empty_obj, location, rotation, scale)
                    else:
                        self._import_model(file_path, obj_name, empty_obj)
                        self._set_empty_object(empty_obj, location, rotation, scale)
                    obj = bpy.data.objects.get(obj_name)
                    if obj:
                        obj.json_props.json_data = json.dumps(ar_obj)
                        print(f'json_data: {obj.json_props.json_data}')
                        sync_from_json(obj_name,obj_type)
                        save_json_to_file(obj, json_path)
                        object_to_collection(obj, parent_collection)
                    else:
                        self.report({'ERROR'}, f'{obj_name} not built')                
        self.report({'INFO'}, "Download and import completed.")
        return {'FINISHED'}

    def _validate_save_path(self):
        """檢查保存路徑是否有效"""
        if not self.set_save_path:
            self.report({'ERROR'}, "Save path not set.")
            return False
        if not os.path.exists(self.set_save_path):
            self.report({'ERROR'}, "Output path does not exist. Please reset it.")
            return False
        return True

    def _extract_url(self, ar_obj):
        """從 AR 物件中提取下載 URL"""
        obj_type = ar_obj['model']['type']
        if obj_type == ARObjectType.ARINFOBALL.value:
            textures = ar_obj['model']['texture'].get('photos', [])
            return textures
        else:
            texture_fields = [ar_obj['model'].get(key) for key in ('texture', 'ios_texture', 'android_texture')]
            for texture in texture_fields:
                if texture and texture.get('url'):
                    return texture['url']
        return None

    def _download_file_with_ar_obj(self, ar_obj, url, index):
        try:
            file_path = self._download_file(ar_obj, url, index)
            if file_path:
                return (ar_obj, file_path, index)
            else:
                self.report({'ERROR'}, f"Failed to download file for {ar_obj['name']}")
                return (ar_obj, None, index)
        except Exception as e:
            print(f"Download failed for {ar_obj['name']}: {e}")
            return (ar_obj, None, index)

    def _download_file(self, ar_obj, url, index=0):
        parsed_url = urlparse(url)
        path = parsed_url.path
        file_name = os.path.basename(path)
        if not file_name:
            file_name = f"{ar_obj['id']}-{ar_obj['name']}_{index}"
        else:
            file_name = f"{ar_obj['id']}-{ar_obj['name']}_{index}{os.path.splitext(file_name)[1]}"
        file_path = os.path.join(self.set_save_path, file_name)
        try:
            file_path = self.client.download(url).name
            print(f"Downloaded {file_name} to {file_path}")
            return file_path
        except Exception as e:
            print(f"Failed to download file {url}: {e}")
            return None


    def _create_arinfoball_layers(self, empty_obj, fields, texture_paths):
        """
        創建多層資訊球環結構，並將所有平面設置為 parent_obj 的子級。
        """
        num_layers = fields['floor_count']
        num_planes = fields['face_count']
        plane_width = fields['face_width']
        plane_height = fields['floor_height']
        plane_gaps = fields['face_gap']
        layer_gap = fields['floor_gap']
        rotation_x_values = fields['floor_angles']
        
        all_planes = self._create_ring_of_planes(
            num_layers=num_layers, 
            num_planes=num_planes, 
            width=plane_width, 
            height=plane_height,
            plane_gaps=plane_gaps, 
            layer_gap=layer_gap, 
            rotation_x_values=rotation_x_values,
            image_paths=texture_paths,
            parent_obj=empty_obj  # 新增的參數，直接設置每個平面的父物件
        )
        return all_planes

    def _create_ring_of_planes(self, num_layers, num_planes, width, height, plane_gaps, layer_gap, rotation_x_values, image_paths, parent_obj=None):
        """
        創建多層環形平面結構，每層包含多個平面，並應用對應的圖片。可選擇設置父物件。
        """
        print(num_layers,num_planes,len(image_paths))
        if len(image_paths) != num_layers * num_planes:
            #raise ValueError("圖片數量必須等於層數與平面數的乘積")
            print('圖片數量必須等於層數與平面數的乘積')
        if isinstance(plane_gaps,(int, float)):
            plane_gaps = [plane_gaps] * num_layers
        elif len[plane_gaps] != num_layers:
            plane_gaps = [plane_gaps[0]] * num_layers

        angle_step = 2 * math.pi / num_planes
        rotation_x_values_radians = [math.radians(angle) for angle in rotation_x_values[::-1]]
        planes = []

        for layer_index in range(num_layers):
            radius = (width + plane_gaps[layer_index]) * num_planes / (2 * math.pi)
            for i in range(num_planes):
                angle = i * angle_step
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                z = layer_index * (height + layer_gap) - (height + layer_gap) * (num_layers - 1) / 2
                plane_name = f"Plane_L{layer_index + 1}_{i + 1}"
                rotation_z = angle + math.pi / 2
                image_path = image_paths[layer_index * num_planes + i]
                plane = self._create_plane(plane_name, width, height, (x, y, z), rotation_x_values_radians[layer_index], rotation_z, image_path)

                if parent_obj:
                    plane.parent = parent_obj  # 自動設置父物件
                planes.append(plane)
                print(f'完成P{layer_index}的{i}')

        return planes

    def _create_plane(self, name, width, height, location, rotation_x, rotation_z, image_path):
        # image_path = 'https://api.lig.com.tw/ar_asset/voa4l7bpqzvilb2ycylpv1btd4r9.png'
        bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=location)
        plane = bpy.context.active_object
        plane.name = name
        plane.scale = (width, height, 1)
        
        # 旋轉90度，使其垂直於XY平面
        plane.rotation_euler.x = math.radians(90) + rotation_x
        
        # 使plane與環形相切
        plane.rotation_euler.z = rotation_z
        
        # 將旋轉應用到plane對象上
        bpy.context.view_layer.objects.active = plane
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        
        # 為 plane 分配貼圖
        self._assign_material(plane, image_path)
        
        return plane

    def _assign_material(self, plane, image_path):
        material_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # 創建新材質
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        bsdf_node = material.node_tree.nodes["Principled BSDF"]
        
        # 加載本地圖片（不再需要 client.download）
        try:
            image = bpy.data.images.load(image_path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load image: {image_path}")
            return

        image_node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        image_node.image = image
        
        # 連接圖片節點到 BSDF 節點
        material.node_tree.links.new(image_node.outputs[0], bsdf_node.inputs["Base Color"])
        
        # 连接图片节点的 alpha 输出到 BSDF 节点的 alpha 输入
        material.node_tree.links.new(image_node.outputs[1], bsdf_node.inputs["Alpha"])
        
        # 將材質分配給對象
        if len(plane.data.materials) == 0:
            plane.data.materials.append(material)
        else:
            plane.data.materials[0] = material
            
        # 设置 Blend Mode 为 Alpha Blend
        material.blend_method = 'BLEND'

    def _create_empty_object(self, name, parent=None):
        collection = bpy.context.collection

        if name in bpy.data.objects:
            return bpy.data.objects[name]
        
        empty_obj = bpy.data.objects.new(name, None)
        collection.objects.link(empty_obj)

        empty_obj.location = (0, 0, 0)
        empty_obj.scale = (1, 1, 1)

        return empty_obj

    def _set_empty_object(self, empty_obj, location, rotation, scale):
        """設置空物件的位置、旋轉和縮放"""
        empty_obj.rotation_mode = 'XYZ'
        empty_obj.rotation_euler = rotation
        empty_obj.location = location
        empty_obj.scale = scale

    def _import_model(self, model_path, name, parent_empty):
        file_name = os.path.basename(model_path)
        folder_path = os.path.dirname(model_path)
        try:
            lower_model_path = model_path.lower()
            if lower_model_path.endswith(".glb"):
                bpy.ops.import_scene.gltf( 
                    filepath=model_path, 
                    export_import_convert_lighting_mode='SPEC', 
                    filter_glob='*.glb;*.gltf',
                    loglevel=20, 
                    import_pack_images=True, 
                    merge_vertices=True, 
                    import_shading='NORMALS', 
                    bone_heuristic='TEMPERANCE', 
                    guess_original_bind_pose=False, 
                    import_webp_texture=False
                )    
            elif lower_model_path.endswith((".mp4", ".mov")):
                bpy.ops.image.import_as_mesh_planes(relative=False, filepath=model_path, files=[{"name":file_name, "name":file_name}], directory=folder_path)   #for blender 4.3
                # bpy.ops.image.import_as_mesh_planes(relative=False, filepath="/Users/henry642/Downloads/1.png", files=[{"name":os.path.basename(model_path), "name":os.path.basename(model_path)}], directory=os.path.dirname(model_path), align_axis='+Z')
                video_obj = bpy.context.selected_objects[0]  
                if video_obj.type == 'MESH':
                    video_texture = video_obj.active_material.node_tree.nodes.get("Image Texture")
                    if video_texture and video_texture.image:
                        video_width = video_texture.image.size[0]
                        video_height = video_texture.image.size[1]
                        print(f'{name}影片解析度：{video_width}x{video_height}')

                        video_max_dim = max(video_width,video_height)
                        video_obj_dimx = video_width/video_max_dim
                        video_obj_dimy = video_height/video_max_dim
                        video_obj.dimensions = Vector((video_obj_dimx,video_obj_dimy,0))
                        video_obj.rotation_euler[0] = radians(90)
                        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                        print(f'{name} 建立完成')   
                        print(f'dimensions為{video_obj.dimensions}')
                    else:
                        print(f'無法獲取{name}的材質或影像資訊')                      
 
            elif lower_model_path.endswith((".png", ".jpg", ".jpeg", ".webp")):
                bpy.ops.image.import_as_mesh_planes(relative=False, filepath=model_path, files=[{"name":file_name, "name":file_name}], directory=folder_path)   #for blender 4.3
                # 將長寬值高者normalize 1公尺
                img_obj = bpy.context.selected_objects[0]
                if img_obj.type == 'MESH':                  
                    img_max_dim = max(img_obj.dimensions[0], img_obj.dimensions[1])
                    img_obj_dimx = img_obj.dimensions[0]/img_max_dim
                    img_obj_dimy = img_obj.dimensions[1]/img_max_dim
                    img_obj.dimensions = Vector((img_obj_dimx,img_obj_dimy,0))
                    img_obj.rotation_euler[0] = radians(90)
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                    print(f'{name} 建立完成')
            elif lower_model_path.endswith(".gif"):
                self._handle_gif_import(model_path, parent_empty.location)
            else:
                raise ValueError("Unsupported file format")
            model_objs = bpy.context.selected_objects
            for obj in model_objs:
                if obj.parent is None:
                    obj.parent = parent_empty
                    obj.matrix_parent_inverse = parent_empty.matrix_world.inverted()
            return model_objs
        except Exception as e:
            print(f"Failed to import model: {e}")
            return None

    def _setup_json_props(self, obj, ar_obj):
        """設置物件的 JSON 屬性"""
        if not hasattr(obj, "json_props"):
            return
        obj.json_props.json_data = json.dumps(ar_obj)
        sync_from_json(obj.name, ar_obj['model']['type'])

    def _transform_location(self, location):
        """轉換位置坐標（Y-Up 到 Z-Up）"""
        return (location['x'], location['z'] * -1, location['y'])

    def _transform_rotation(self, location):
        """轉換旋轉角度（Y-Up 到 Z-Up）"""
        return tuple(map(math.radians, (location['rotate_x'], location['rotate_z'], location['rotate_y']*-1)))

    def _transform_scale(self, zoom):
        """轉換縮放比例（Y-Up 到 Z-Up）"""
        return (zoom['x'], zoom['z'], zoom['y'])

    def _handle_gif_import(self, gif_path, plane_location):
        """處理 GIF 文件的導入"""
        try:
            temp_dir = self._prepare_gif_handling(gif_path)
            frame_paths = self._extract_frames_from_gif(gif_path, temp_dir)
            self._import_image_sequence_as_plane(frame_paths, plane_location)
        except Exception as e:
            print(f"Failed to handle GIF import: {e}")

    def _prepare_gif_handling(self, gif_path):
        """準備 GIF 文件的暫存路徑"""
        if not gif_path.lower().endswith(".gif"):
            raise ValueError("This is not a GIF file.")
        work_dir = os.path.join(os.path.dirname(gif_path), "temp_gif_frames")
        os.makedirs(work_dir, exist_ok=True)
        return work_dir

    def _extract_frames_from_gif(self, gif_path, output_dir):
        """從 GIF 文件中提取幀"""
        gif = Image.open(gif_path)
        frame_count = gif.n_frames
        frame_paths = []
        for frame in range(frame_count):
            gif.seek(frame)
            frame_path = os.path.join(output_dir, f"frame_{frame:03d}.png")
            gif.save(frame_path, "PNG")
            frame_paths.append(frame_path)

        return frame_paths

    def _import_image_sequence_as_plane(self, frame_paths, plane_location):
        try:
            # 添加平面
            bpy.ops.mesh.primitive_plane_add(size=1, location=plane_location)
            plane = bpy.context.selected_objects[0]
            # 创建材质
            material = bpy.data.materials.new(name="ImageSequenceMaterial")
            material.use_nodes = True
            plane.data.materials.append(material)   # 將材質附加到平面

            # 獲取材質節點樹
            node_tree = material.node_tree
            nodes = node_tree.nodes

            # 查找 Principled BSDF 和 Image Texture 节点
            for node in nodes:
                nodes.remove(node)
            
            tex_image = nodes.new(type="ShaderNodeTexImage")
            tex_image.location = (-300, 0)

            bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
            bsdf_node.location = (0, 0)

            output_node = nodes.new(type="ShaderNodeOutputMaterial")
            output_node.location = (300, 0)

            # 连接节点
            node_tree.links.new(tex_image.outputs["Color"], bsdf_node.inputs["Base Color"])
            node_tree.links.new(tex_image.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            node_tree.links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])
                        
            # 加載第一幀影像
            first_image = frame_paths[0]
            image = bpy.data.images.load(first_image)
            tex_image.image = image

            # 調整平面比例以匹配影像
            print(f'plane: {plane}')           
            print(f'image: {image}')   
            width, height = image.size
            aspect_ratio = width / height
            # 設定平面比例
            plane.scale = Vector((aspect_ratio, 1, 1))
            plane.rotation_euler[0] = radians(90)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            print(width,height)
            # self._adjust_image_dimensions(plane, image)
            # 確保所有影像路徑加入影像序列
            for frame_path in frame_paths:
                bpy.data.images.load(frame_path, check_existing=True)

            tex_image.image.source = 'SEQUENCE'
            tex_image.image_user.frame_start = 1
            tex_image.image_user.frame_duration = len(frame_paths)
            tex_image.image_user.use_cyclic = True
            tex_image.image_user.use_auto_refresh = True
            tex_image.image_user.frame_offset = -1

            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled_bsdf = node
            
            print("Principled BSDF 输入插槽:")
            for input in principled_bsdf.inputs:
                print(f"- {input.name}")

            print("Image Texture 输出插槽:")
            for output in tex_image.outputs:
                print(f"- {output.name}")

            material.blend_method = 'BLEND'
            print(f'成功匯入影像序列至單一平面，共{len(frame_paths)}張圖片')
        except Exception as e:
            print(f'函式內部發生錯誤：{e}')

    def _adjust_image_dimensions(plane, image):
        """
        調整平面的大小以匹配影像的長寬比例
        """
        # 計算影像比例
        width, height = image.size
        print(width,height)
        aspect_ratio = width / height

        # 設定平面比例
        plane.scale = Vector((aspect_ratio, 1, 1))
        plane.rotation_euler[0] = radians(90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)



























        # bpy.context.scene.cursor.location = (0, 0, 0) #cursor歸零
        # set_save_path = context.scene.save_path #儲存路徑

        # if set_save_path != "":
        #     if os.path.exists(set_save_path):
        #         print("輸出路徑: ", set_save_path)
        #     else:
        #         self.report({'ERROR'}, "Output path does not exist. Please reset it.")
        #         return {'CANCELLED'}
        # else:
        #     self.report({'ERROR'}, "Save path not set.")
        #     return {'CANCELLED'}

        # def create_empty_object(name, parent=None):
        #     # 取消選取所有物件，不使用 bpy.ops
        #     for obj in bpy.context.selected_objects:
        #         obj.select_set(False)
            
        #     # 創建空物件
        #     empty_obj = bpy.data.objects.new(name, None)
        #     bpy.context.collection.objects.link(empty_obj) #將empty_obj添加至當前collection
        #     empty_obj.location = (0, 0, 0)
        #     empty_obj.scale = (1, 1, 1)

        #     if parent is not None:
        #         empty_obj.parent = parent
        #     return empty_obj
            
        # def set_empty_object(empty_obj, location, rotation, scale):
        #     # 取消選取所有物件，避免使用 bpy.ops
        #     for obj in bpy.context.selected_objects:
        #         obj.select_set(False)

        #     empty_obj.rotation_mode = 'XYZ'  # 指定欧拉角的旋转模式
        #     empty_obj.rotation_euler = (radians(rotation[0]), radians(rotation[1]), radians(rotation[2]))  # 将度数转换为弧度
        #     empty_obj.location = location
        #     empty_obj.scale = scale
        #     #empty_obj.name = name   #henry  
        #     return empty_obj

        # def extract_frames_from_gif(gif_path, output_dir):
        #     """將 GIF 拆解為影像序列"""
        #     gif = Image.open(gif_path)
        #     frame_count = gif.n_frames
        #     frame_paths = []
        #     print(f'總共有{frame_count}個檔案')
        #     for frame in range(frame_count):
        #         gif.seek(frame)
        #         frame_path = os.path.join(output_dir, f"frame_{frame:03d}.png")
        #         gif.save(frame_path, "PNG")
        #         frame_paths.append(frame_path)
        #         print(f'第{frame}個gif檔案位置為{frame_path}')
                       
        #     return frame_paths

        # def prepare_gif_handling(gif_path):
        #     """檢查 GIF 文件並建立暫存路徑"""
        #     if not gif_path.lower().endswith(".gif"):
        #         raise ValueError("This is not a GIF file.")
        #     work_dir = os.path.join(os.path.dirname(gif_path), "temp_gif_frames")
        #     os.makedirs(work_dir, exist_ok=True)
        #     print(f"work_dir is {work_dir}")
        #     return work_dir

        # def adjust_image_dimensions(plane, image):
        #     """
        #     調整平面的大小以匹配影像的長寬比例
        #     """
        #     if image is None or image.size[0] == 0 or image.size[1] == 0:
        #         return

        #     # 計算影像比例
        #     width, height = image.size
        #     aspect_ratio = width / height

        #     # 設定平面比例
        #     plane.scale = Vector((aspect_ratio, 1, 1))
        #     plane.rotation_euler[0] = radians(90)
        #     bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # def import_image_sequence_as_plane(frame_paths, plane_location=(0, 0, 0)):
        #     """
        #     將影像序列應用到單一平面，並設置為動畫材質
        #     """
        #     try:
                    
        #         # 新增平面
        #         bpy.ops.mesh.primitive_plane_add(size=1, location=plane_location)
        #         # bpy.ops.mesh.primitive_plane_add(size=2, calc_uvs=True, enter_editmode=False, align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), scale=(0, 0, 0))
        #         plane = bpy.context.selected_objects[0]
        #         # 建立新材質
        #         material = bpy.data.materials.new(name="ImageSequenceMaterial")
        #         material.use_nodes = True  # 啟用節點
        #         plane.data.materials.append(material)  # 將材質附加到平面
        #         # 獲取材質節點樹
        #         node_tree = material.node_tree
        #         nodes = node_tree.nodes

        #         # 刪除默認的 BSDF 節點並重新創建
        #         for node in nodes:
        #             nodes.remove(node)
        #         output_node = nodes.new(type="ShaderNodeOutputMaterial")
        #         output_node.location = (300, 0)
        #         bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        #         bsdf_node.location = (0, 0)
        #           
        #         # 添加影像序列節點
        #         tex_image = nodes.new(type="ShaderNodeTexImage")
        #         tex_image.location = (-300, 0)
        #         # 加載第一幀影像
        #         first_frame_path = frame_paths[0]
        #         image = bpy.data.images.load(first_frame_path)
        #         tex_image.image = image
        #         # 調整平面比例以匹配影像
        #         adjust_image_dimensions(plane, image)

        #         # 確保所有影像路徑加入影像序列
        #         for frame_path in frame_paths:
        #             bpy.data.images.load(frame_path, check_existing=True)

        #         image.source = 'SEQUENCE'  # 設置為影像序列
        #         # image.frame_start = 1  # 動畫從第 1 幀開始
        #         nodes["Image Texture"].image_user.frame_start = 1
        #         nodes["Image Texture"].image_user.frame_duration = len(frame_paths)
        #         nodes["Image Texture"].image_user.use_cyclic = True
        #         nodes["Image Texture"].image_user.use_auto_refresh = True
        #         nodes["Image Texture"].image_user.frame_offset = -1

        #         # 連接影像節點到 BSDF 節點
        #         node_tree.links.new(tex_image.outputs["Color"], bsdf_node.inputs["Base Color"])
        #         node_tree.links.new(tex_image.outputs["Alpha"], bsdf_node.inputs["Alpha"])
        #         material.blend_method = 'BLEND'

        #         print(f"成功匯入影像序列至單一平面，共 {len(frame_paths)} 張圖片")
        #     except Exception as e:
        #         print(f"函式內部發生錯誤: {e}")

        # def handle_gif_import(gif_path, plane_location=(0, 0, 0)):
        #     """
        #     將 GIF 動畫拆解為影像序列並導入 Blender
        #     """    
        #     try:
        #         # 準備暫存資料夾
        #         temp_dir = prepare_gif_handling(gif_path)
                
        #         # 拆解 GIF 為影像序列
        #         frame_paths = extract_frames_from_gif(gif_path, temp_dir)
                
        #         # 匯入影像序列到平面
        #         import_image_sequence_as_plane(frame_paths, plane_location)
                
        #         # 可選：清理暫存影像
        #         # cleanup_temp_files(temp_dir)
        #         # print('4-完成影像暫存清理')
        #         print("GIF 匯入成功！")
        #     except Exception as e:
        #         print(f"GIF 匯入失敗: {e}")

        # def import_model(model_path, model_name, parent_empty):
        #     file_name = os.path.basename(model_path)
        #     folder_path = os.path.dirname(model_path)
        #     try:
        #         lower_model_path = model_path.lower()
        #         if lower_model_path.endswith(".glb"):
        #             # bpy.ops.import_scene.gltf(filepath="/var/folders/6z/97v_b4sx1bb1byv856nrq23r0000gn/T/f0433jf119t8eod5j7wntginq92x.glb", files=[{"name":"f0433jf119t8eod5j7wntginq92x.glb", "name":"f0433jf119t8eod5j7wntginq92x.glb"}], loglevel=20)
        #             bpy.ops.import_scene.gltf( 
        #                 filepath=model_path, 
        #                 export_import_convert_lighting_mode='SPEC', 
        #                 filter_glob='*.glb;*.gltf',
        #                 loglevel=20, 
        #                 import_pack_images=True, 
        #                 merge_vertices=True, 
        #                 import_shading='NORMALS', 
        #                 bone_heuristic='TEMPERANCE', 
        #                 guess_original_bind_pose=False, 
        #                 import_webp_texture=False
        #             )                        
        #             print(f'{model_name} glb建立完成')
        #         elif lower_model_path.endswith(".mp4") or lower_model_path.endswith(".mov"):
        #             bpy.ops.image.import_as_mesh_planes(relative=False, filepath=model_path, files=[{"name":file_name, "name":file_name}], directory=folder_path)   #for blender 4.3
        #             # bpy.ops.image.import_as_mesh_planes(relative=False, filepath="/Users/henry642/Downloads/1.png", files=[{"name":os.path.basename(model_path), "name":os.path.basename(model_path)}], directory=os.path.dirname(model_path), align_axis='+Z')
        #             video_obj = bpy.context.selected_objects[0]  
        #             if video_obj.type == 'MESH':
        #                 video_texture = video_obj.active_material.node_tree.nodes.get("Image Texture")
        #                 if video_texture and video_texture.image:
        #                     video_width = video_texture.image.size[0]
        #                     video_height = video_texture.image.size[1]
        #                     print(f'{model_name}影片解析度：{video_width}x{video_height}')

        #                     video_max_dim = max(video_width,video_height)
        #                     video_obj_dimx = video_width/video_max_dim
        #                     video_obj_dimy = video_height/video_max_dim
        #                     video_obj.dimensions = Vector((video_obj_dimx,video_obj_dimy,0))
        #                     print(f'dimensions為{video_obj.dimensions}')
        #                 else:
        #                     print(f'無法獲取{model_name}的材質或影像資訊')                      
        #             # Blender新建物件的初始數據與lightspace匹配
        #             video_obj.rotation_euler[0] = radians(90)
        #             bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        #             print(f'{model_name} 建立完成')                    

        #         elif lower_model_path.endswith(".png") or lower_model_path.endswith(".jpg") or lower_model_path.endswith(".jpeg") or lower_model_path.endswith(".webp"):                    
        #             # 將圖像導入平面
        #             # bpy.ops.import_image.to_plane(files=[{"name": os.path.basename(model_path), "relative_path": False}], directory=os.path.dirname(model_path), align_axis='Z+')
        #             bpy.ops.image.import_as_mesh_planes(relative=False, filepath=model_path, files=[{"name":file_name, "name":file_name}], directory=folder_path)   #for blender 4.3
        #             # 將長寬值高者normalize 1公尺
        #             img_obj = bpy.context.selected_objects[0]
        #             if img_obj.type == 'MESH':                  
        #                 img_max_dim = max(img_obj.dimensions[0], img_obj.dimensions[1])
        #                 img_obj_dimx = img_obj.dimensions[0]/img_max_dim
        #                 img_obj_dimy = img_obj.dimensions[1]/img_max_dim
        #                 img_obj.dimensions = Vector((img_obj_dimx,img_obj_dimy,0))
                    
        #             # Blender新建物件的初始數據與lightspace匹配
        #                 img_obj.rotation_euler[0] = radians(90)
        #                 bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        #                 print(f'{model_name} 建立完成')

        #             else:
        #                 print(f"Failed to normalize image size for {model_name}: {img_obj.name} is not a mesh")
        #                 return None

        #         elif lower_model_path.endswith(".gif"):
        #             # 特殊處理 GIF 檔案
        #             handle_gif_import(model_path, parent_empty.location)
        #             print(f'{model_name} GIF 處理完成')

        #         else:
        #             raise ValueError("Unsupported file format")
                    
        #         # 設置導入對象的父對象
        #         model_objs = bpy.context.selected_objects
        #         for model_obj in model_objs:
        #             if model_obj.parent is None:
        #                 set_parent(model_obj, parent_empty)

        #         return model_objs
          
        #     except ValueError as e:
        #         print(e)
        #         return None            

        # def set_parent(child, parent):
        #     child.parent = parent
        #     child.matrix_parent_inverse = parent.matrix_world.inverted() #讓設定父子階時不改變位置關係       
        
        # def import_objects(ar_obj,model_path,name,location,rotation,scale):
        #     if os.path.exists(model_path):
        #         # 創建一個空對象並將其設置為模型對象的父對象
        #         empty_obj = create_empty_object(name)  # name
        #         model_obj = import_model(model_path,name, empty_obj) # file , name , empty 
        #         set_empty_object(empty_obj, location, rotation, scale) # transform

        #         bpy.ops.loaddon.message('INVOKE_DEFAULT', message = '下載完成: {}'.format(name))

        #     else:
        #         print(f"Skipping missing file: {model_path}")
        
        # def assign_material(plane, image_path):
        #     material_name = os.path.splitext(os.path.basename(image_path))[0]
            
        #     # 創建新材質
        #     material = bpy.data.materials.new(name=material_name)
        #     material.use_nodes = True
        #     bsdf_node = material.node_tree.nodes["Principled BSDF"]
            
        #     # 加載圖片紋理
        #     image_file = client.download(image_path)
        #     image_path = image_file.name
        #     image_dir = os.path.dirname(image_file.name)
        #     image = bpy.data.images.load(image_path)
        #     image_node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        #     image_node.image = image
            
        #     # 連接圖片節點到 BSDF 節點
        #     material.node_tree.links.new(image_node.outputs[0], bsdf_node.inputs["Base Color"])
            
        #     # 连接图片节点的 alpha 输出到 BSDF 节点的 alpha 输入
        #     material.node_tree.links.new(image_node.outputs[1], bsdf_node.inputs["Alpha"])
            
        #     # 將材質分配給對象
        #     if len(plane.data.materials) == 0:
        #         plane.data.materials.append(material)
        #     else:
        #         plane.data.materials[0] = material
                
        #     # 设置 Blend Mode 为 Alpha Blend
        #     material.blend_method = 'BLEND'

        # def create_plane(name, width, height, location, rotation_x, rotation_z, image_path):
        #     # image_path = 'https://api.lig.com.tw/ar_asset/voa4l7bpqzvilb2ycylpv1btd4r9.png'
        #     bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=location)
        #     plane = bpy.context.active_object
        #     plane.name = name
        #     plane.scale = (width, height, 1)
            
        #     # 旋轉90度，使其垂直於XY平面
        #     plane.rotation_euler.x = math.radians(90) + rotation_x
            
        #     # 使plane與環形相切
        #     plane.rotation_euler.z = rotation_z
            
        #     # 將旋轉應用到plane對象上
        #     bpy.context.view_layer.objects.active = plane
        #     bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            
        #     # 為 plane 分配貼圖
        #     assign_material(plane, image_path)
            
        #     return plane

        # def create_ring_of_planes(num_layers, num_planes, width, height, plane_gaps, layer_gap, rotation_x_values, image_paths, parent_obj=None):
        #     """
        #     創建多層環形平面結構，每層包含多個平面，並應用對應的圖片。可選擇設置父物件。
        #     """
        #     print(num_layers,num_planes,len(image_paths))
        #     if len(image_paths) != num_layers * num_planes:
        #         #raise ValueError("圖片數量必須等於層數與平面數的乘積")
        #         print('圖片數量必須等於層數與平面數的乘積')

        #     angle_step = 2 * math.pi / num_planes
        #     rotation_x_values_radians = [math.radians(angle) for angle in rotation_x_values[::-1]]
        #     planes = []

        #     for layer_index in range(num_layers):
        #         radius = (width + plane_gaps[layer_index]) * num_planes / (2 * math.pi)
        #         for i in range(num_planes):
        #             angle = i * angle_step
        #             x = radius * math.cos(angle)
        #             y = radius * math.sin(angle)
        #             z = layer_index * (height + layer_gap) - (height + layer_gap) * (num_layers - 1) / 2
        #             plane_name = f"Plane_L{layer_index + 1}_{i + 1}"
        #             rotation_z = angle + math.pi / 2
        #             image_path = image_paths[layer_index * num_planes + i]
        #             plane = create_plane(plane_name, width, height, (x, y, z), rotation_x_values_radians[layer_index], rotation_z, image_path)

        #             if parent_obj:
        #                 plane.parent = parent_obj  # 自動設置父物件
        #             planes.append(plane)
        #             print(f'完成P{layer_index}的{i}')

        #     return planes

        # def extract_url(ar_obj):
        #     """從 ar_obj 中提取有效的 URL"""
        #     textures = [ar_obj['model'].get(key) for key in ('texture', 'ios_texture', 'android_texture')]      
        #     for texture in textures:
        #         if texture and texture.get('url'):
        #             return texture['url']
        #     return None

        # def save_data_to_json(file_path, data):
        #     """將數據保存為格式化的 JSON 文件"""
        #     try:
        #         with open(file_path, 'w') as f:
        #             print(json.dumps(data, ensure_ascii=False, indent=4), file=f)
        #     except (IOError, TypeError, ValueError) as e:
        #         print(f"保存數據時出錯: {e}")

        # def file_name_set(name):
        #     """生成文件名"""
        #     return f"{name}.json"

        # def process_arinfoballv1_object(ar_obj, context, name, location, rotation,scale, transparency, actions, events):
        #             """處理3D對象，提取必要數據並保存為 JSON 文件"""
        #             url = extract_url(ar_obj)
        #             if not url:
        #                 bpy.ops.loaddon.message('INVOKE_DEFAULT', message=f"No URL is found in {ar_obj['id']}")
        #                 return

        #             # 提取動畫參數
        #             arinfoballv1_params = extract_arinfoballv1_params(ar_obj['model'].get('fields', {}))

        #             # 設置文件路徑
        #             file_name = file_name_set(name)
        #             full_path = os.path.join(context.scene.save_path, file_name)

        #             # 構建數據字典
        #             data = {
        #                 'name': name,
        #                 'loading': name,
        #                 'type': ar_obj['model'].get('type'),
        #                 'location': location,
        #                 'rotation': rotation,
        #                 'scale': scale,
        #                 'transparency':transparency,
        #                 'ar_obj': ar_obj,
        #                 'actions': actions,
        #                 'events': events,
        #                 'url': url,  # 將提取到的 URL 加入字典
        #                 **arinfoballv1_params  # 展開動畫參數字典
        #             }

        #             # 保存數據
        #             save_data_to_json(full_path, data)

        #             if name in bpy.data.objects:
        #                 print(f"{name} 場景已有同名物件，將進行屬性更新")
        #                 obj = bpy.data.objects[name]
        #                 # 更新屬性：位置、旋轉、縮放等
        #                 obj.location = location
        #                 obj.rotation_euler = tuple(map(math.radians, rotation))
        #                 obj.scale = scale
        #                 # 確保物件被添加到指定集合
        #                 object_to_collection(obj, parent_collection)

        #             else:
        #                 # 若無相同名稱物件，下載並創建新物件
        #                 ar_file = client.download(url)
        #                 if ar_file:
        #                     empty_InfoBall = create_empty_object(name, parent=None)
        #                     location_cor = (ar_obj['location']['x'],ar_obj['location']['z']*-1,ar_obj['location']['y']++(arinfoballv1_params['plane_height'] + arinfoballv1_params['layer_gap'] / 2) * ar_obj['zoom']['y'])
        #                     set_empty_object(empty_InfoBall, location_cor, rotation, scale)

        #                     # 生成和附加層平面
        #                     create_info_sphere_layers(empty_InfoBall, arinfoballv1_params)
        #                     obj = bpy.data.objects.get(name)
        #                     if obj:
        #                         object_to_collection(obj, parent_collection)
        #                         print(f"資訊球 '{name}' 已成功導入並配置完成")
        #                 else:
        #                     bpy.ops.loaddon.message('INVOKE_DEFAULT', message=f"Unable to download model for {name}")

        # def create_info_sphere_layers(parent_obj, params):
        #     """
        #     創建多層資訊球環結構，並將所有平面設置為 parent_obj 的子級。
        #     """
        #     num_layers = params['num_layers']
        #     num_planes = params['num_planes']
        #     plane_width = params['plane_width']
        #     plane_height = params['plane_height']
        #     plane_gaps = params['plane_gaps']
        #     layer_gap = params['layer_gap']
        #     rotation_x_values = params['rotation_x_values']
        #     image_paths = params['image_paths']
            
        #     all_planes = create_ring_of_planes(
        #         num_layers=num_layers, 
        #         num_planes=num_planes, 
        #         width=plane_width, 
        #         height=plane_height,
        #         plane_gaps=plane_gaps, 
        #         layer_gap=layer_gap, 
        #         rotation_x_values=rotation_x_values,
        #         image_paths=image_paths,
        #         parent_obj=parent_obj  # 新增的參數，直接設置每個平面的父物件
        #     )
        #     return all_planes

        # client = LigDataApi.ApiClient.shared()
        # # 確保用戶已登錄
        # if not client.authenticated():  # 檢查是否已登錄
        #     self.report({'ERROR'}, "Login to LiG Cloud first")
        #     return {'CANCELLED'}                 
        # ar_objects = client.download_ar_objects(context.scene.lig_scene)   
        # parent_col_name = context.scene.lig_scene # 確保所有下載的AR對象被統一存放在parent_col collection中，方便管理
        # parent_collection = bpy.data.collections.get(parent_col_name) or CreateCollection.create_collection(parent_col_name)
        # ar_objects_count = len(ar_objects)
        # print("ar_objects 物件數量:",ar_objects_count)
        # for i, ar_obj in enumerate(ar_objects,1):
        #     print(f'ar_obj-{i}:{ar_obj}')

        # collection_name = parent_col_name  # 請替換為您的集合名稱
        # Collection_objects_count = count_objects_in_collection(collection_name)

        # if set_save_path != '':     
        #     if os.path.exists(set_save_path):  
        #         for ar_obj in ar_objects:  #ar_obj is dict
        #             download_url = extract_url(ar_obj)
        #             if not download_url:
        #                 self.report({'WARNING'}, f"No URL found for object {ar_obj['id']}")
        #                 continue                    
        #             # 設置文件路徑
        #             obj_name = str(ar_obj['id'])+"-"+ar_obj['name']
        #             obj_type = ar_obj['model']['type']
        #             file_name = f"{obj_name}.json"
        #             full_path = os.path.join(context.scene.save_path, file_name)
        #             # 保存數據
                    
        #             if obj_name in bpy.data.objects:  #如果物件已經存在，進行屬性更新
        #                 print(f"{obj_name} The scene already has an object with the same name and will be updated with new propertues.")
        #                 obj = bpy.data.objects[obj_name]
        #                 obj.location = (ar_obj['location']['x'],ar_obj['location']['z']*-1,ar_obj['location']['y'])
        #                 obj.rotation_euler = tuple(map(math.radians, (ar_obj['location']['rotate_x'],ar_obj['location']['rotate_z']*-1,ar_obj['location']['rotate_y'])))
        #                 obj.scale = (ar_obj['zoom']['x'],ar_obj['zoom']['z'],ar_obj['zoom']['y'])          
        #                 obj.json_props.json_data = json.dumps(ar_obj)
        #                 obj_name = obj.json_props.obj_name
        #                 sync_from_json(obj_name,obj_type)
        #                 save_json_to_file(obj, full_path)
        #             else:   # 若無相同名稱物件，下載並創建新物件
        #                 ar_file = client.download(download_url)
        #                 if ar_file:
        #                     model_path = ar_file.name
        #                     location = (ar_obj['location']['x'],ar_obj['location']['z']*-1,ar_obj['location']['y'])
        #                     rotation = tuple(map(math.radians, (ar_obj['location']['rotate_x'],ar_obj['location']['rotate_z']*-1,ar_obj['location']['rotate_y'])))
        #                     scale = (ar_obj['zoom']['x'],ar_obj['zoom']['z'],ar_obj['zoom']['y'])
        #                     if obj_type == ARObjectType.ARINFOBALL.value:
        #                         plane_height = ar_obj['model'].get('fields', {})['plane_height']
        #                         layer_gap = ar_obj['model'].get('fields', {})['layer_gap']
        #                         empty_InfoBall = create_empty_object(obj_name, parent=None)
        #                         location_cor = (ar_obj['location']['x'], ar_obj['location']['z']*-1, (ar_obj['location']['y']+ plane_height+ layer_gap / 2) * ar_obj['zoom']['y'])
        #                         set_empty_object(empty_InfoBall, location_cor, rotation, scale)             
        #                     else:
        #                         import_objects(ar_obj, model_path, obj_name, location, rotation, scale)
        #                     obj = bpy.data.objects.get(obj_name)
        #                     # Step1: ar_obj 寫進json_data
        #                     # 把ar_obj資料寫進 json_data裡面
        #                     # =====================================================
        #                     #完成json_data的初始化
        #                     # =====================================================
        #                     obj.json_props.json_data = json.dumps(ar_obj)  #把ar_obj轉為字串存到json_data完成初始化
        #                     # Step2: json_data資料寫進 props
        #                     sync_from_json(obj_name,obj_type)
        #                     print('json_data')
        #                     print(obj.json_props.json_data)
        #                     # step3: 存json檔
        #                     save_json_to_file(obj, full_path)
        #                     if obj:
        #                         object_to_collection(obj, parent_collection)
        #                 else:
        #                     bpy.ops.loaddon.message('INVOKE_DEFAULT', message=f"Unable to download model for {obj_name}")
                    
        #         return {'FINISHED'}
        #     else:
        #         self.report({'ERROR'}, 'The path entered does not exist.')
        #         return {'CANCELLED'}
            
        # elif set_save_path == '':
        #     self.report({'ERROR'}, 'Please set the save path first')
        #     return {'CANCELLED'}
        # context.area.tag_redraw()
        # self.report({'INFO'}, "Download completed.")
        # return {'FINISHED'}

class LiGJSONRefreshOperator(Operator): # get json from json file
    bl_idname = "lig.json_refresh"
    bl_label = "Json Refresh"
    bl_description = "Download the properties to objects' json"

    def execute(self, context):
        set_save_path = context.scene.save_path

        # 获取 id_name 集合
        id_name = context.scene.lig_scene
        if id_name not in bpy.data.collections:
            self.report({'INFO'}, f"集合 {id_name} 不存在")
            return {'CANCELLED'}
        
        collection = bpy.data.collections[id_name]

        # 遍历集合中的所有对象
        for obj in collection.objects:
            # 查找最父階物件（Root Parent）
            root_obj = obj
            while root_obj.parent:  # 不斷尋找父物件直到找到最頂層
                root_obj = root_obj.parent
            obj_name = root_obj.name
            # 選擇最父階物件
            bpy.context.view_layer.objects.active = root_obj  # 設置活動物件
            bpy.ops.object.select_all(action='DESELECT')  # 清除所有選擇
            root_obj.select_set(True)  # 選擇根物件
            obj_type = obj.json_props.model_type
            obj = bpy.data.objects.get(obj_name)
            
            # 构建 JSON 文件路径
            json_file = os.path.join(set_save_path, obj_name + ".json")
            # 检查 JSON 文件是否存在
            if os.path.exists(json_file):
                # 打开并读取 JSON 文件
                with open(json_file, 'r') as file:
                    data = json.load(file)
                # 将 JSON 数据转换为字符串并存储到对象的 json_props 属性中
                obj.json_props.json_data = json.dumps(data)
            else:
                # 文件不存在时，报告信息
                self.report({'INFO'}, f"文件 {json_file} 不存在")
            sync_from_json(obj_name,obj_type)
        self.report({'INFO'}, "下載完成")
            # 下载更新完成后自动执行 json_refresh 操作
        return {'FINISHED'}

class LiGJSONUpdata(Operator):  # Json update 
    bl_idname = "lig.json_update"
    bl_label = "Update JSON"
    bl_description = "update the properties if objects' property changed"
    # 從json_props 至 json_data 至 json file
    def execute(self, context):
        set_save_path = context.scene.save_path
        # 獲取集合名稱
        id_name = context.scene.lig_scene
        if id_name not in bpy.data.collections:
            self.report({'INFO'}, f"集合 {id_name} 不存在")
            return {'CANCELLED'}
        
        collection = bpy.data.collections[id_name]

        # 遍歷集合中的所有對象
        for obj in collection.objects:
            if obj and obj.json_props.json_data:  # 確保對象有 JSON 數據
                root_obj = obj
                while root_obj.parent:  # 不斷尋找父物件直到找到最頂層
                    root_obj = root_obj.parent
                obj_name = root_obj.name
                obj_type = obj.json_props.type
                json_file = os.path.join(set_save_path, obj_name + ".json")
                sync_to_json(obj_name,obj_type)
                save_json_to_file(obj,json_file)

        self.report({'INFO'}, "JSON 更新完成")
        return {'FINISHED'}

class LiGJSONUpLoad(Operator,LiGAccount): # Json upload to server
    bl_idname = "lig.json_upload"
    bl_label = "Upload JSON Data"
    bl_description = "Upload Json properties to server"

    def execute(self, context):
        set_save_path = context.scene.save_path  # 获取保存路径 '/Users/henry642/Documents/Blender/Json/'
        id_name = context.scene.lig_scene  # 获取 ID 名称（即 collection 名称）

        # 确保保存路径存在
        if not os.path.exists(set_save_path):
            self.report({'ERROR'}, "保存路径不存在")
            return {'CANCELLED'}

        # 检查 collection 是否存在
        if id_name not in bpy.data.collections:
            self.report({'ERROR'}, f"Collection '{id_name}' 不存在")
            return {'CANCELLED'}

        collection = bpy.data.collections[id_name]

        # 確保用戶已登錄
        client = LigDataApi.ApiClient.shared()
        if not client.authenticated():  # 檢查是否已登錄
            self.report({'ERROR'}, "Login to LiG Cloud first")
            return {'CANCELLED'}

        for obj in collection.objects:
            if obj.json_props.json_data:
                data = json.loads(obj.json_props.json_data)

                # 如果在JSON數據中存在'location'鍵，則更新其值
                if 'location' in data:
                    location = obj.location
                    location = [round(val, 4) for val in location]  # 四捨五入到小數點後二位
                    data['location']['x'] = location[0]

                # 如果在JSON數據中存在'rotation'鍵，則更新其值
                if 'rotation' in data:
                    rotation = [math.degrees(a) for a in obj.rotation_euler]
                    rotation = [round(val, 4) for val in rotation]  # 四捨五入到小數點後二位
                    data['rotation'] = rotation

                # 如果在JSON數據中存在'scale'鍵，則更新其值
                if 'scale' in data:
                    scale = obj.scale
                    scale = [round(val, 4) for val in scale]# 四捨五入到小數點後二位
                    data['scale'] = scale
                
                obj.json_props.json_data = json.dumps(data)

                # 生成文件路径
                file_path = os.path.join(set_save_path, f"{obj.name}.json")
                try:
                    with open(file_path, 'w') as file:
                        json.dump(data, file)
                except:
                    self.report({'ERROR'}, f"Failed to write to file: {file_path}")
                    return {'CANCELLED'}
        # 上傳至雲端
        client = LigDataApi.ApiClient.shared()
        for obj in collection.objects:
            if obj.json_props.json_data:
        
                data = json.loads(obj.json_props.json_data)                
                #位置、旋轉、縮放賦值
                location = obj.location
                location = [round(val, 5) for val in location]
                location_x, location_y, location_z = transform(*location, 0, 0, 0,1,1,1)[:3]

                rotation = [math.degrees(a) for a in obj.rotation_euler]
                rotation = [round(val, 4) for val in rotation]
                rotate_x, rotate_y, rotate_z= transform(0, 0, 0, *rotation,1,1,1)[3:6]

                scale = obj.scale
                scale = [round(val, 4) for val in scale]
                scale_x, scale_y, scale_z = transform(0, 0, 0, 0, 0, 0, *scale)[-3:]
                #henry-------------------------------------------------------------------
                #依照不同type parameters建立完整的json格式
                #取出JSON鍵值
                id_data = data.get('id')
                name = data.get('name')
                type_data = data['model'].get('type')
                configuration = data.get('configuration')
                created_time = data.get('created_at')
                updated_time = data.get('updated_at')
                light_id = data.get('light_id')
                ar_object_owner_id = data.get('ar_object_owner_id')
                ar_object_owner_type = data.get('ar_object_owner_type')
                texture_data = data['model'].get('texture')
                url_data = texture_data.get('url') if texture_data is not None else None
                url_id_data = texture_data.get('id') if texture_data is not None else None
                ios_texture = data['model'].get('ios_texture')
                android_texture = data['model'].get('android_texture')
                ios_texture_url = ios_texture.get('url') if ios_texture is not None else None
                ios_texture_id = ios_texture.get('id') if ios_texture is not None else None
                android_texture_url = android_texture.get('url') if android_texture is not None else None
                android_texture_id = android_texture.get('id') if android_texture is not None else None
                transparency = data.get('transparency')
                group = data.get('group')
                zone_id = data.get('zone_id')
                scene_id = data.get('scene_id')
                sub_events = data.get('sub_events')
                is_child = data.get('is_child')
                
                field = data['model']['fields']
                #general parameters
                is_ignore_data = field.get('is_ignore', False)
                is_hidden_data = field.get('is_hidden', False)
                is_occlusion = field.get('is_occlusion', False)    
                face_me_data = field.get('face_me', False)
                is_allow_pinch = field.get('is_allow_pinch', False)
                visible_distance_data = field.get('visible_distance',20.0)

                # image parameters(type=5)               
                pic_width = field.get('width',1)
                pic_height = field.get('height',1)                    
                # is_size_scale_lock = field.get('is_size_scale_lock', True) 
                is_size_scale_lock = True
                is_double_sided = field.get('is_double_sided', False)
                bloom_intensity_data = field.get('bloom_intensity', 0)
                bloom_intensity = field.get('bloom_intensity') if bloom_intensity_data is not None else None
                bloom_radius_data = field.get('bloom_radius',0)
                bloom_radius = field.get('bloom_radius') if bloom_radius_data is not None else None

                # 3D Model parameters(type=8)
                animation_speed = field.get('animation_speed')
                if field.get('end_frame')==0:
                    start_frame = None
                    end_frame = None
                else:
                    start_frame = field.get('start_frame', None)
                    end_frame = field.get('end_frame', None)
                fps = field.get('fps',24)
                multiply_number = field.get('multiply_number')
                multiply_radius = field.get('multiply_radius')
                multiply_range = field.get('multiply_range')
                multiply_is_zero_y = field.get('multiply_is_zero_y', False)
                
                # vedio fields(type=9)
                hue_angle_data = field.get('hue_angle',None)
                hue_range_data = field.get('hue_range',20.0)
                saturation_data = field.get('saturation',0.5)
                is_play_data = field.get('is_play',False)
                is_loop_play_data = field.get('is_loop_play', False)

                
                #ARInfoBall v1.0(type=13)
                floor_count = field.get('floor_count')
                face_count = field.get('face_count')
                floor_height = field.get('floor_height')
                face_width = field.get('face_width')
                floor_gap = field.get('floor_gap')
                face_gap = field.get('face_gap')
                speed = field.get('speed')
                floor_angles = field.get('floor_angles')
                face_gap_list = field.get('face_gap_list')
                photo_texture = field.get('texture')
                actions = data.get('actions',[])
                events  = data.get('events',[])

                # Particle(type=16) 
                particle_birth_rate = field.get('particle_birth_rate')
                particle_birth_rate_variation =field.get('particle_birth_rate_variation')
                particle_life_span = field.get('particle_life_span')
                particle_life_span_variation = field.get('particle_life_span_variation')
                particle_velocity = field.get('particle_velocity')
                particle_velocity_variation = field.get('particle_velocity_variation')
                
                if type_data == ARObjectType.ARINFOBALL.value:  #資訊球
                    params = {
                        'id': id_data,
                        'location': {
                            'x': location_x,
                            'y': location_y,
                            'z': location_z,
                            'rotate_x': rotate_x,
                            'rotate_y': rotate_y,
                            'rotate_z': rotate_z,
                        },
                        'zoom': {
                            'x': scale_x,
                            'y': scale_y,
                            'z': scale_z,
                        },
                        "configuration": configuration,
                        "created_at": created_time,
                        "updated_at": updated_time,
                        "light_id": light_id,
                        "ar_object_owner_id": ar_object_owner_id,
                        "ar_object_owner_type": ar_object_owner_type,
                        "model": {
                            "type": type_data,
                            "fields": {
                                "is_hidden": is_hidden_data,
                                "is_allow_pinch":is_allow_pinch,
                                "is_ignore": is_ignore_data,
                                "visible_distance": visible_distance_data,
                                "is_occlusion": is_occlusion,
                                "floor_count":floor_count,
                                "face_count":face_count,
                                "floor_height":floor_height,
                                "face_width":face_width,
                                "floor_gap":floor_gap,
                                "face_gap":face_gap,
                                "speed":speed,
                                "floor_angles":floor_angles,
                                "face_gap_list":face_gap_list,
                            },
                            "texture": photo_texture,
                            'ios_texture': None, 
                            'android_texture': None
                        },
                        'actions': actions, 
                        'transparency': transparency, 
                        'group': group, 
                        'zone_id': None, 
                        'events': None, 
                        'scene_id': scene_id, 
                        'sub_events': sub_events,
                        'is_child': is_child
                    }

                elif type_data == ARObjectType.MODEL_3D.value: #3D物件
                    params= {
                        "id": id_data,
                        "name": name,
                        "location": {
                            "y": location_y,
                            "rotate_y": rotate_y,
                            "z": location_z,
                            "x": location_x,
                            "rotate_x": rotate_x,
                            "rotate_z": rotate_z
                        },
                        "zoom": {
                            "x": scale_x,
                            "y": scale_y,
                            "z": scale_z
                        },
                        "configuration": configuration,
                        "created_at": created_time,
                        "updated_at": updated_time,
                        "light_id": light_id,
                        "ar_object_owner_id": ar_object_owner_id,
                        "ar_object_owner_type": ar_object_owner_type,
                        "model": {
                            "type": type_data,
                            "fields": {
                                "visible_distance": visible_distance_data,
                                "width": pic_width,
                                "height": pic_height,
                                "face_me": face_me_data,
                                "is_ignore": is_ignore_data,
                                "is_hidden": is_hidden_data,
                                "is_double_sided": is_double_sided,
                                "animation_speed": animation_speed,
                                "start_frame": start_frame,
                                "end_frame": end_frame,
                                "fps": fps,
                                "multiply_number": multiply_number,
                                "multiply_radius": multiply_radius,
                                "multiply_range": multiply_range,
                                "multiply_is_zero_y": multiply_is_zero_y,
                                "is_occlusion":is_occlusion,
                                "is_allow_pinch":is_allow_pinch
                            },
                            "texture": None,
                            # "texture": {
                            #     "url": url_data,
                            #     "id": url_id_data
                            # },
                            "ios_texture": {
                                "url": ios_texture_url,
                                "id": ios_texture_id
                            },
                            "android_texture": {
                                "url": android_texture_url,
                                "id": android_texture_id
                            }
                        },
                        "actions": actions,
                        "transparency": transparency,
                        "group": group,
                        "zone_id": zone_id,
                        "events": events,
                        "scene_id": scene_id,
                        "sub_events": sub_events,
                        "is_child": is_child
                    }

                elif type_data == ARObjectType.IMAGE.value: #圖片
                    params = {
                        "id": id_data,
                        "name": name,
                        "location": {
                            "y": location_y,
                            "rotate_y": rotate_y,
                            "z": location_z,
                            "x": location_x,
                            "rotate_x": rotate_x,
                            "rotate_z": rotate_z
                        },
                        "zoom": {
                            "x": scale_x,
                            "y": scale_y,
                            "z": scale_z
                        },
                        "configuration": configuration,
                        "created_at": created_time,
                        "updated_at": updated_time,
                        "light_id": light_id,
                        "ar_object_owner_id": ar_object_owner_id,
                        "ar_object_owner_type": ar_object_owner_type,
                        "model": {
                            "type": type_data,
                            "fields": {
                                "width": pic_width,
                                "height": pic_height,
                                "face_me": face_me_data,
                                "is_ignore": is_ignore_data,
                                "visible_distance": visible_distance_data,
                                "is_hidden": is_hidden_data,
                                "is_size_scale_lock": is_size_scale_lock,
                                "is_double_sided": is_double_sided,
                                "is_allow_pinch":is_allow_pinch,
                                "bloom_intensity":bloom_intensity,
                                "bloom_radius":bloom_radius,  
                            },
                            "texture": {
                                "url": url_data,
                                "id": url_id_data,
                                "content_type": "image/png"
                            },
                            "ios_texture": {
                                "url": ios_texture_url,
                                "id": ios_texture_id,
                                "content_type": "image/png"
                            },
                            "android_texture": {
                                "url": android_texture_url,
                                "id": android_texture_id,
                                "content_type": "image/png"
                            }
                        },
                        "actions": actions,
                        "transparency": transparency,
                        "group": group,
                        "zone_id": zone_id,
                        "events": events,
                        "scene_id": scene_id,
                        "sub_events": sub_events,
                        "is_child": is_child
                    }

                elif type_data == ARObjectType.VIDEO.value: #影片
                    params = {
                        "id": id_data,
                        "name": name,
                        "location": {
                            "x": location_x,
                            "y": location_y,
                            "z": location_z,
                            "rotate_x": rotate_x,
                            "rotate_y": rotate_y,
                            "rotate_z": rotate_z
                        },
                        "zoom": {
                            "x": scale_x,
                            "y": scale_y,
                            "z": scale_z
                        },
                        "configuration": configuration,
                        "created_at": created_time,
                        "updated_at": updated_time,
                        "light_id": light_id,
                        "ar_object_owner_id": ar_object_owner_id,
                        "ar_object_owner_type": ar_object_owner_type,
                        "model": {
                            "type": type_data,
                            "fields": {
                                "face_me": face_me_data,
                                "is_ignore": is_ignore_data,
                                "visible_distance": visible_distance_data,
                                "hue_angle":hue_angle_data,
                                "hue_range": hue_range_data,
                                "saturation": saturation_data,
                                "is_play": is_play_data,
                                "is_hidden": is_hidden_data,
                                "is_loop_play": is_loop_play_data,
                                "is_allow_pinch":is_allow_pinch
                            },
                            "texture": {
                                "url": url_data,
                                "id": url_id_data
                            },
                            "ios_texture": {
                                "url": ios_texture_url,
                                "id": ios_texture_id
                            },
                            "android_texture": {
                                "url": android_texture_url,
                                "id": android_texture_id
                            }
                        },
                        "actions": actions,
                        "transparency": transparency,
                        "group": group,
                        "zone_id": zone_id,
                        "events": events,
                        "scene_id": scene_id,
                        "sub_events": sub_events,
                        "is_child": is_child
                    }

                elif type_data == ARObjectType.PARTICLE.value: #粒子效果
                    params = {
                        "id": id_data,
                        "name": name,
                        "location": {
                            "y": location_y,
                            "rotate_y": rotate_y,
                            "z": location_z,
                            "x": location_x,
                            "rotate_x": rotate_x,
                            "rotate_z": rotate_z
                        },
                        "zoom": {
                            "x": scale_x,
                            "y": scale_y,
                            "z": scale_z
                        },
                        "configuration": configuration,
                        "created_at": created_time,
                        "updated_at": updated_time,
                        "light_id": light_id,
                        "ar_object_owner_id": ar_object_owner_id,
                        "ar_object_owner_type": ar_object_owner_type,
                        "model": {
                            "type": type_data,
                            "fields": {
                                "particle_birth_rate": particle_birth_rate,
                                "particle_birth_rate_variation": particle_birth_rate_variation,
                                "particle_life_span": particle_life_span,
                                "particle_life_span_variation": particle_life_span_variation,
                                "particle_velocity": particle_velocity,
                                "particle_velocity_variation": particle_velocity_variation,
                                "is_occlusion": is_occlusion,
                                "is_hidden": is_hidden_data,
                                "is_ignore": is_ignore_data,
                                "face_me": face_me_data,
                                "is_double_sided": is_double_sided,
                                "is_allow_pinch":is_allow_pinch
                            },
                            "texture": {
                                "url": url_data,
                                "id": url_id_data
                            },
                            "ios_texture": {
                                "url": ios_texture_url,
                                "id": ios_texture_id
                            },
                            "android_texture": {
                                "url": android_texture_url,
                                "id": android_texture_id
                            }
                        },
                        "actions": actions,
                        "transparency": transparency,
                        "group": group,
                        "zone_id": zone_id,
                        "events": events,
                        "scene_id": scene_id,
                        "sub_events": sub_events,
                        "is_child": is_child
                    }

                else:
                    params = {
                        'id': id_data,
                        'location': {
                            'x': location_x,
                            'y': location_y,
                            'z': location_z,
                            'rotate_x': rotate_x,
                            'rotate_y': rotate_y,
                            'rotate_z': rotate_z,
                        },
                        'zoom': {
                            'x': scale_x,
                            'y': scale_y,
                            'z': scale_z,
                        },
                        "model": {
                            "type": type_data,
                            "fields": field,
                            "texture": {
                                "url": url_data,
                                "id": url_id_data
                            },
                            "ios_texture": {
                                "url": ios_texture_url,
                                "id": ios_texture_id,
                            },
                            "android_texture": {
                                "url": android_texture_url,
                                "id": android_texture_id,
                            }
                        },
                        #"actions": actions,
                        #"evnets": events
                    }

                obj.json_props.json_data = json.dumps(params)
                file_path = os.path.join(set_save_path, f"{obj.name}.json")
                save_json_to_file(obj, file_path)              
                print(f'params: {params}')
                client.upload(params)
        self.report({'INFO'}, "LiG Cloud 上傳成功")
        return {'FINISHED'}

class LIG_OT_CopyEvents(Operator):    #Copy events from the selected object
    bl_idname = "lig.copy_events"
    bl_label = "Copy Events"

    def execute(self, context):
        global copied_events
        obj = context.object

        if obj and hasattr(obj, "json_props") and obj.json_props.json_data:
            json_data = json.loads(obj.json_props.json_data)
            copied_events = json_data.get("events", [])
            if copied_events:
                self.report({'INFO'}, "Events copied successfully.")
                return {'FINISHED'}

        self.report({'WARNING'}, "No events to copy.")
        return {'CANCELLED'}

class LIG_OT_PasteEvents(Operator):   # Paste events to the selected object
    bl_idname = "lig.paste_events"
    bl_label = "Paste Events"

    def execute(self, context):
        global copied_events
        obj = context.object

        if not copied_events:
            self.report({'WARNING'}, "No events to paste.")
            return {'CANCELLED'}

        if obj and hasattr(obj, "json_props") and obj.json_props.json_data:
            json_data = json.loads(obj.json_props.json_data)
            print("Before Paste:", json.dumps(json_data, ensure_ascii=False, indent=4))
            json_data["events"] = copied_events
            obj.json_props.json_data = json.dumps(json_data, ensure_ascii=False, indent=4)
            # Debug
            print("After Paste:", json.dumps(json_data, ensure_ascii=False, indent=4))
            # 刷新 Blender UI
            # 更新視圖層以反映數據變化，但保留右側工具欄
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'TOOLS':  # 保持右側工具欄
                            area.tag_redraw()

            self.report({'INFO'}, "Events pasted successfully.")
            return {'FINISHED'}

        self.report({'ERROR'}, "Failed to paste events.")
        return {'CANCELLED'}

class LIG_OT_CleanEvents(Operator):   # Clean copied events
    bl_idname = "lig.clean_events"
    bl_label = "Clean Events Paste"

    def execute(self, context):
        global copied_events
        if copied_events:
            copied_events = None
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()  # 刷新 UI，但保留工具欄

            self.report({'INFO'}, "Copied events cleared successfully.")
            # 刷新 Blender UI
            # bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)

            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No copied events to clear.")
            return {'CANCELLED'}

class LIG_OT_Alignment(Operator): # Align selected objects on the chosen axis
    bl_idname = "lig.alignment"
    bl_label = "Align Objects"

    axis: bpy.props.StringProperty()    # type: ignore

    def execute(self, context):
        global alignment_value, alignment_axis

        selected_objects = context.selected_objects
        if len(selected_objects) < 2:
            self.report({'WARNING'}, "Select at least two objects to align.")
            return {'CANCELLED'}

        # 獲取所選物件在指定軸上的最大值
        max_value = max(getattr(obj.location, self.axis.lower()) for obj in selected_objects)

        # 將所有物件的指定軸對齊到最大值
        for obj in selected_objects:
            setattr(obj.location, self.axis.lower(), max_value)

        alignment_value = max_value
        alignment_axis = self.axis

        # 更新視圖
        bpy.ops.view3d.view_selected()
        bpy.context.view_layer.update()

        self.report({'INFO'}, f"Aligned objects on {self.axis} axis.")
        return {'FINISHED'}

class LIG_OT_ApplyAlignment(Operator):    # Apply new alignment value
    bl_idname = "lig.apply_alignment"
    bl_label = "Apply Alignment"

    def execute(self, context):
        global alignment_value, alignment_axis

        if alignment_value is None or alignment_axis is None:
            self.report({'WARNING'}, "No alignment value to apply.")
            return {'CANCELLED'}

        new_value = context.scene.alignment_input

        # 更新所選物件的對齊值
        for obj in context.selected_objects:
            setattr(obj.location, alignment_axis.lower(), new_value)

        alignment_value = new_value
        bpy.context.view_layer.update()

        self.report({'INFO'}, f"Applied new {alignment_axis} alignment value.")
        return {'FINISHED'}

class LiGJSONFrameSelectedOperator(Operator): # 新增到移動到中心視角(2024/12/16)
    bl_idname = "lig.frame_selected"
    bl_label = "Frame Selected"
    bl_description = "Move the view to the selected object's center"

    def execute(self, context):
        # 確保有選取的物件
        if context.object:
            # 使用 Blender 的內建操作來框選物件
            bpy.ops.view3d.view_selected(use_all_regions=False)
            self.report({'INFO'}, "View moved to selected object's center")
        else:
            self.report({'WARNING'}, "No object selected")
        return {'FINISHED'}
                      
class LiGSetupOperator(Operator): # update user scenes from server 從服務器更新用戶場景
    bl_idname = "lig.setup"
    bl_label = "Create default lig collection and refresh scene list"

    def execute(self, context):

        context.scene.lig_scenes.clear()
        for scene in LigDataApi.ApiClient.shared().scene_list():
            context.scene.lig_scenes.add().name = '%d %s' % (scene['id'], scene['name'],)
        # bpy.ops.chack.images_plane()
        bpy.ops.file.autopack_toggle()#檔案自動打包
       
        return { 'FINISHED' }

class OBJECT_OT_ApplyParticleEffect(Operator):
    bl_idname = "object.apply_particle_effect"
    bl_label = "Apply Particle Effect"
    bl_description = "Generate particle effect based on the properties"

    def execute(self, context):
        props = context.object.particle_props

        # 创建粒子系统
        bpy.ops.object.particle_system_add()
        particle_system = context.object.particle_systems[-1]
        settings = particle_system.settings

        # 设置粒子参数
        settings.count = int(props.particle_birth_rate)
        settings.lifetime = props.particle_life_span
        settings.normal_factor = props.particle_velocity

        # 添加随机性
        settings.use_random_lifetime = True
        settings.lifetime_random = props.particle_life_span_variation
        settings.use_random_velocity = True
        settings.velocity_random = props.particle_velocity_variation

        self.report({'INFO'}, "Particle effect applied!")
        return {'FINISHED'}

class LiGLogoutOperator(Operator):
    bl_idname = "lig.logout_operator"
    bl_label = "Logout LiG Cloud"
    #bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        LigDataApi.ApiClient.shared().logout()
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        addon_prefs.token = ''
        return { 'FINISHED' }

class LiGLoginOperator(Operator):
    bl_idname = "lig.login_operator"
    bl_label = "登入 LiG Cloud"
    #bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        lig_client = LigDataApi.ApiClient.shared()
        ret = lig_client.login(addon_prefs.email, addon_prefs.password)
        if not ret:
            self.report({'ERROR'}, 'Unable to login LiG CLoud. %r' % lig_client.errors)
            return { 'CANCELLED' }
        addon_prefs.token = lig_client.get_token()
        return { 'FINISHED' }

class ChackImagePlane(Operator): #確保 image as planes的addon有安裝
    bl_idname = "chack.images_plane"
    bl_label = "Enable Images as Planes"

    def execute(self, context):
        addons = bpy.context.preferences.addons
        if 'io_import_images_as_planes' not in addons:
            bpy.ops.preferences.addon_enable(module='io_import_images_as_planes')

        return {'FINISHED'}
    
class CheckLogin_out(Operator): #檢查登入狀態
    bl_idname = "chack.login_out"
    bl_label = "Login out"
    def id_logout():
        bpy.ops.lig.logout_operator()
        #print("Logout")

    def id_login():
        bpy.ops.lig.login_operator()
        #print("Login")
    
    bpy.app.timers.register(id_logout, first_interval=1.0)
    bpy.app.timers.register(id_login, first_interval=2.0)

class MessageOperator(Operator):
    bl_idname = "loaddon.message"
    bl_label = "訊息顯示"

    message: bpy.props.StringProperty(default='')   # type: ignore

    def execute(self, context):
        self.report({'INFO'}, self.message)
        print(self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.message)

class KeyLocRot(Operator):  #製作路徑Json
    bl_idname = "object.key_loc_rot"
    bl_label = "keyframe export"

    def execute(self, context):
        selection = bpy.context.selected_objects
        set_save_path = context.scene.save_path #儲存路徑
        if set_save_path != '':
            if selection:
                frame_start = float('inf')
                frame_end = float('-inf')

                for obj in selection:
                    if obj.animation_data and obj.animation_data.action:
                        action = obj.animation_data.action

                        for fcurve in action.fcurves:
                            for keyframe in fcurve.keyframe_points:
                                frame = keyframe.co[0]
                                frame_start = min(frame, frame_start)
                                frame_end = max(frame, frame_end)

                # 如果找到了有效的起始和結束幀，進行烘焙
                if frame_start != float('inf') and frame_end != float('-inf'):
                    bpy.ops.nla.bake(frame_start=int(frame_start), frame_end=int(frame_end), bake_types={'OBJECT'})
                    ki = key_loc_rot()
                    ki.key(context)
                    print('錄製關鍵幀')
                else:
                    bpy.ops.loaddon.message('INVOKE_DEFAULT', message = '選取的物體沒有關鍵幀')
                    print('選取的物體沒有關鍵幀')
            else:
                # 這裡的 loaddon 操作似乎是特定於某個插件或自訂模組的，所以它可能不在所有Blender安裝中都可用
                bpy.ops.loaddon.message('INVOKE_DEFAULT', message = '沒有選取物件')
                print('沒有選取物件')
        else:
            bpy.ops.loaddon.message('INVOKE_DEFAULT', message = '請先設定儲存路徑')
            print('請先設定儲存路徑')

        return {'FINISHED'}

class key_loc_rot:
        #獲取當前選擇
        def key(self,context):  
                selection = bpy.context.selected_objects
                scene = bpy.context.scene
                startFrame = scene.frame_start
                endFrame = scene.frame_end
                # currentFrame = scene.frame_current
                selection_name = bpy.context.selected_objects[0].name

                file_name = key_set(selection_name)
                full_path = os.path.join(context.scene.save_path, file_name)
                
                file = open(full_path, "w")
                file.write("---\n")
                file.write("- id: 1\n")
                file.write("  values: {}\n")
                file.write("  actions:\n")
                loc_list = []
                rot_list = []

                #遍歷所選對象
                for sel in selection:
                    #循環遍歷所有動畫幀
                    for i in range(endFrame-startFrame+1):

                        frame = i + startFrame
                        scene.frame_set(frame)
                        rot = sel.rotation_euler
                        loc = sel.location
                        print(loc, rot)
                        loc_list.append([loc.x,loc.y,loc.z])
                        rot_list.append([rot.x,rot.y,rot.z])
                        delta_loc_x  = loc_list[i][0] - loc_list[i-1][0]
                        delta_loc_y  = loc_list[i][1] - loc_list[i-1][1]
                        delta_loc_z  = loc_list[i][2] - loc_list[i-1][2]

                        delta_rot_x  = rot_list[i][0] - rot_list[i-1][0]
                        delta_rot_y  = rot_list[i][1] - rot_list[i-1][1]
                        delta_rot_z  = rot_list[i][2] - rot_list[i-1][2]
                        time = 0.041666666666667
                        print(delta_loc_x)

                        file.write("  - id: 3\n")
                        file.write("    values:\n")
                        file.write("      direction_x: %f\n" % (delta_loc_x))
                        file.write("      direction_y: %f\n" % (delta_loc_z))
                        file.write("      direction_z: %f\n" % (delta_loc_y*-1))
                        file.write("      group: %i\n" % (frame))
                        file.write("      time: %f\n" % (time*5))
                        file.write("  - id: 13\n")
                        file.write("    values:\n")
                        file.write("      direction_x: %f\n" % (degrees(delta_rot_x)))
                        file.write("      direction_y: %f\n" % (degrees(delta_rot_z)))
                        file.write("      direction_z: %f\n" % (degrees(delta_rot_y)*-1))
                        file.write("      group: %i\n" % (frame))
                        file.write("      time: %f\n" % (time*5))
                
                bpy.ops.loaddon.message('INVOKE_DEFAULT', message = '關鍵幀存檔完成 / ' + file_name)
                print('關鍵幀存檔完成 / ' + file_name)

                # close the file
                file.close()

                #恢復原始幀（不必要）
                # scene.frame_set(currentFrame)

class LIGASSET_OP_Upload(Operator): #新增檔案
    bl_idname = "ligasset.op_upload"
    bl_label = "上傳 Lig-Asset"

    def execute(self, context):
        # 首先检查 context.scene.ligasset_upload_texts 是否为空
        if not context.scene.ligasset_upload_texts:
            self.report({'INFO'}, "沒有路徑輸入框，請新增至少一個。")
            print("沒有路徑輸入框，請新增至少一個。")
            return {'CANCELLED'}
        
        # 检查每个 item.text 是否为空
        for item in context.scene.ligasset_upload_texts:
            if not item.text:  # 如果 item.text 为空
                self.report({'INFO'}, "有路徑欄位為空，請確保所有路徑欄位都有指定路徑。")
                print("有路徑欄位為空，請確保所有路徑欄位都有指定路徑。")
                return {'CANCELLED'}
        
        # /Users/henry642/Desktop/OnBoard/HARTi Demo Site/3D/中企署服務台的小光子.glb
        assets_list = [item.text for item in context.scene.ligasset_upload_texts]
        assets_str = "[ " + ", ".join(f'"{item}"' for item in assets_list) + " ]"
        # [,"/Users/henry642/Desktop/OnBoard/HARTi Demo Site/3D/中企署服務台的小光子.glb",]
        assets_str = assets_str.replace("\\", "/")
        LigDataApi.ApiClient.shared().upload_files(assets_list)
        
        self.report({'INFO'}, "已上傳完畢。")
        print("已上傳完畢。")
        return {'FINISHED'}

class LIGASSET_OP_AddTextField(Operator):
    bl_idname = "ligasset.add_textfield"
    bl_label = "新增路徑欄位"

    def execute(self, context):
        context.scene.ligasset_upload_texts.add()
        return {'FINISHED'}

class LIGASSET_OP_RemoveTextField(Operator):
    bl_idname = "ligasset.remove_textfield"
    bl_label = "移除路徑欄位"

    def execute(self, context):
        if context.scene.ligasset_upload_texts:
            context.scene.ligasset_upload_texts.remove(len(context.scene.ligasset_upload_texts) - 1)
        return {'FINISHED'}


class CreateCollection:
    @staticmethod
    def collection_exists(name):
        return name in bpy.data.collections

    @staticmethod
    def create_collection(name, parent=None):
        if not CreateCollection.collection_exists(name):
            new_collection = bpy.data.collections.new(name)
            if parent:
                parent.children.link(new_collection)
            else:
                bpy.context.scene.collection.children.link(new_collection)
            return new_collection
        else:
            print(f"'{name}' 已存在")
            return bpy.data.collections[name]
collection_creator = CreateCollection()

#共用函式區---------------------------------------------------------------------------------------------------------------------

def register_events(obj):
    # 清空現有的 events
    obj.events.clear()

    # 添加測試數據
    event1 = obj.events.add()
    event1.id = "E1"
    action1 = event1.actions.add()
    action1.name = "Move"
    action1.type = "Translate"
    
    action2 = event1.actions.add()
    action2.name = "Rotate"
    action2.type = "Spin"

    event2 = obj.events.add()
    event2.id = "E2"
    action3 = event2.actions.add()
    action3.name = "Jump"
    action3.type = "Vertical"

classes = (
    LiGDownloader,
    SceneProperty,
    ScenesProperty,
    LiGScenePanel,
    LiGPreferences,
    LiGSetupOperator,
    LiGLogoutOperator,
    LiGLoginOperator,
    # ChackImagePlane,
    CheckLogin_out,
    MessageOperator,
    ARJsonProperties,
    LiGJSONUpLoad,
    LiGJSONUpdata,
    KeyLocRot,
    LiGJSONRefreshOperator,
    LiG3DVIEWJSONPanel, 
    #ObjActionPanel,
    LIGASSET_UploadItem,
    # LIGASSET_PT_Upload,
    # LIGASSET_OP_AddTextField,
    # LIGASSET_OP_RemoveTextField,
    # LIGASSET_OP_Upload,
    LiGToggleProperties,
    TargetObjectItem,    
    #ProgressOperator,
    LIG_PT_JsonPanel,
    LiG_PT_BasicPanel,
    LiGJSONFrameSelectedOperator,
    # LiGAction,
    # LiGEvent,
    # LiGEventActionPanel,
    ActionValuePropertyGroup,
    ActionPropertyGroup,
    ActionsPropertyGroup,
    ActionPanel,
    LIG_OT_CopyEvents,
    LIG_OT_PasteEvents,
    LIG_OT_CleanEvents,
    LIG_OT_Alignment,
    LIG_OT_ApplyAlignment,
    LiG_PT_ObjSelection,
    LiG_PT_OBJAlignment,
    EventOperation,
    OBJECT_OT_ApplyParticleEffect,
)

def register():
    install_packages()
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file.append(menu_func_import)
    bpy.types.Scene.lig_scene = StringProperty(name='LiG Scene ID', subtype='NONE')
    bpy.types.Scene.lig_scenes = CollectionProperty(type=ScenesProperty)

    default_save_path = os.path.expanduser("~/Documents/Blender/Json/")
    
    if not os.path.exists(default_save_path):
        os.makedirs(default_save_path)

    # 定義 Scene 類型的屬性
    bpy.types.Scene.ligasset_upload_texts = bpy.props.CollectionProperty(type=LIGASSET_UploadItem)
    bpy.types.Scene.lig_toggle_props = bpy.props.PointerProperty(type=LiGToggleProperties)
    bpy.types.Scene.save_path = bpy.props.StringProperty(
        name="Saving Directory",
        description="輸出檔案的路徑",
        default=default_save_path,  # 设置默认值为用户文档目录
        # default=r"",
        maxlen=1024,
        subtype='DIR_PATH'
    )
    bpy.types.Scene.json_path = bpy.props.StringProperty(
        name="檔案路徑",
        description="開啟檔案的路徑",
        # default=r"",
        default=default_save_path,  # 设置默认值为用户文档目录
        maxlen=1024,
        subtype='DIR_PATH',
        update=update_json_path  # 指定更新函数
    )
    bpy.types.Scene.alignment_input = bpy.props.FloatProperty(
    name="Alignment Value",
    default=0.0,
    description="New alignment value"
    )
    # 定義 Object 類型的屬性
    bpy.types.Object.json_props = PointerProperty(type=ARJsonProperties)
    bpy.types.Object.actions_props = bpy.props.PointerProperty(type=ActionsPropertyGroup)

    # 使用延遲計時器，確保界面已加載
    bpy.app.timers.register(refresh_ui)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file.remove(menu_func_import)
    del bpy.types.Scene.save_path
    del bpy.types.Scene.json_path
    del bpy.types.Object.json_props
    del bpy.types.Scene.ligasset_upload_texts
    del bpy.types.Object.actions_props

def refresh_ui():
    for area in bpy.context.window_manager.windows[0].screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    return None  # 不重複執行

if __name__ == "__main__":
    register()
