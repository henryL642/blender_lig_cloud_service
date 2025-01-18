# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

bl_info = {
    "name": "LiG AR Cloud",
    "author": "Plain Wu <plainwu@gmail.com>",
    "version": (0, 1, 0),
    "blender": (2, 83, 2),
    "location": "File > Import-Export",
    "description": "Import-Export AR objects from LiG Cloud",
    "warning": "",
    #"doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/lig.html",
    "support": 'TESTING',
    "category": "Import-Export",
}

import base64
import os
import os.path
import re
import bpy
import requests
from urllib3.exceptions import HTTPError
import tempfile
import math
from math import pi
from mathutils import Vector

from bpy_extras.image_utils import load_image

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
    Operator,
    AddonPreferences,
    PropertyGroup,
    UIList,
    Panel,
)

from bpy_extras.object_utils import (
    object_data_add,
)


class LiGDownloader(Operator):
    bl_idname = "lig.download"
    bl_label = "Download AR Objects from LiG Cloud"

    def execute(self, context):
        def compute_size(size):
            px, py = size
            if px > py:
                y = 1
                x = px / py
            else:
                x = 1
                y = py / px
            return (x, y)

        def clean_node_tree(node_tree):
            """Clear all nodes in a shader node tree except the output.

            Returns the output node
            """
            nodes = node_tree.nodes
            for node in list(nodes):  # copy to avoid altering the loop's data source
                if not node.type == 'OUTPUT_MATERIAL':
                    nodes.remove(node)

            return node_tree.nodes[0]

        def create_cycles_texnode(context, node_tree, image):
            tex_image = node_tree.nodes.new('ShaderNodeTexImage')
            tex_image.image = image
            tex_image.show_texture = True
            #self.apply_texture_options(tex_image, img_spec)
            tex_image.extension = 'CLIP'
            return tex_image

        def clean_node_tree(node_tree):
            """Clear all nodes in a shader node tree except the output.

            Returns the output node
            """
            nodes = node_tree.nodes
            for node in list(nodes):  # copy to avoid altering the loop's data source
                if not node.type == 'OUTPUT_MATERIAL':
                    nodes.remove(node)

            return node_tree.nodes[0]

        def import_image(context, image_file, ar_obj):
            height = 1 # 1m

            filename = os.path.basename(image_file.name)
            image = load_image(filename, os.path.dirname(image_file.name), check_existing=True, force_reload=True)
            size = tuple(image.size)
            bpy.ops.mesh.primitive_plane_add('INVOKE_REGION_WIN')
            plane = context.active_object
            bpy.ops.object.mode_set(mode='OBJECT')
            width, height = compute_size(size)
            plane.dimensions = width, height, 0.0

            material = bpy.data.materials.new(name=filename)
            material.use_nodes = True
            material.blend_method = 'BLEND'
            node_tree = material.node_tree
            out_node = clean_node_tree(node_tree)
            text_image = create_cycles_texnode(context, node_tree, image)

            core_shader = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
            node_tree.links.new(core_shader.inputs[0], text_image.outputs[0])
            node_tree.links.new(out_node.inputs[0], core_shader.outputs[0])
            plane.data.materials.append(material)
            return plane

        def save_setting(obj, ar_obj):
            obj.lig_ar_obj.ar_id = ar_obj['id']
            obj.lig_ar_obj.model_type = ar_obj['model']['type']
            obj.lig_ar_obj.managed = True
            obj.lig_ar_obj.scale_x = ar_obj['zoom']['x']
            obj.lig_ar_obj.scale_y = ar_obj['zoom']['y']
            obj.lig_ar_obj.scale_z = ar_obj['zoom']['z']
            obj.name = ar_obj['name']
            obj.location = Vector((ar_obj['location']['x'], ar_obj['location']['y'], ar_obj['location']['z']))
            obj.rotation_euler.rotate_axis('X', math.radians(ar_obj['location']['rotate_x'] + 90.0))
            obj.rotation_euler.rotate_axis('Y', math.radians(ar_obj['location']['rotate_y']))
            obj.rotation_euler.rotate_axis('Z', math.radians(ar_obj['location']['rotate_z']))
            #obj.scale = Vector((ar_obj['zoom']['x'] * obj.scale[0], ar_obj['zoom']['y'] * obj.scale[1], ar_obj['zoom']['z'] * obj.scale[2]))

        def move_obj_to_lig_coll(obj, master_coll, lig_coll):
            lig_coll.objects.link(obj)
            try:
                master_coll.objects.unlink(obj)
                return True
            except:
                return False


        # Find lig coll
        #master_coll = bpy.context.scene.collection
        lig_coll = None
        if 'lig' in bpy.data.collections:
            lig_coll = bpy.data.collections['lig']
        else:
            self.report({'ERROR'}, 'Please client setup first!')
            return {'CANCELLED'}
        master_coll = bpy.data.scenes['Scene'].collection
        first_coll = bpy.data.collections['Collection']

        client = ApiClient.shared()
        ar_objects = client.download_ar_objects(context.scene.lig_scene)
        for ar_obj in ar_objects:
            # Check if exists
            found = False
            for obj in lig_coll.objects:
                if obj.lig_ar_obj.ar_id == int(ar_obj['id']):
                    found = True
                    break
            if found:
                continue

            # Determine url
            if ar_obj['model']['texture']:
                url = ar_obj['model']['texture']['url']
            elif ar_obj['model']['ios_texture']:
                url = ar_obj['model']['ios_texture']['url']
            elif ar_obj['model']['android_texture']:
                url = ar_obj['model']['android_texture']['url']
            else:
                self.report({'ERROR'}, 'No URL is found in %r' % ar_obj['id'])
                continue

            ar_file = client.download(url)
            if not ar_file:
                self.report({'ERROR'}, 'URL %r is NOT accessible' % url)
                return {'CANCELLED'}

            obj = None
            try:
                if '.glb' in url:
                    current_objs = set(bpy.context.scene.objects)

                    # Import GLB or usdz or scn
                    bpy.ops.import_scene.gltf(filepath=ar_file.name)

                    imported_objs = set(bpy.context.scene.objects) - current_objs
                    first_one = True
                    for obj in imported_objs:
                        move_obj_to_lig_coll(obj, master_coll, lig_coll)
                        save_setting(obj, ar_obj)
                        if first_one:
                            first_one = False
                        else:
                            obj.lig_ar_obj.ar_id = -1
                            obj.lig_ar_obj.managed = False

                elif re.search('\.(png|jpg|jpeg)$', url, re.IGNORECASE):
                    obj = import_image(context, ar_file, ar_obj)
                    move_obj_to_lig_coll(obj, first_coll, lig_coll)
                    save_setting(obj, ar_obj)
            finally:
                ar_file.close()

        context.view_layer.update()
        return {'FINISHED'}


#VIEW3D_MT_object_context_menu

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
        try:
            r = requests.post('https://api.lightgen.space/api/login', json={"user": {"email": email, "password": pwd}})
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
        return {'Authorization': 'Bearer ' + self.token, 'User-Agent': 'Blender LiG Plugin Client'}

    def download_ar_objects(self, scene_id):
        if ' ' in str(scene_id):
            scene_id = scene_id.split()[0]
        r = requests.get('https://api.lig.com.tw/api/ar_objects_from_scene/' + scene_id, headers=self.auth_headers())
        if not r:
            return

        ar_objects = r.json()['ar_objects']
        return ar_objects

    def download(self, url):
        r = requests.get(url)
        if r.status_code != 200:
            return None

        fn = os.path.join(tempfile.gettempdir(), os.path.basename(url))
        tf = open(fn, 'wb+')
        if not tf:
            return None

        tf.write(r.content)
        return tf

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
        def radians_to_degree(deg):
            return deg * 180 / pi
        data = {
            "location": {
                "x": obj.location[0],
                "y": obj.location[1],
                "z": obj.location[2],
                "rotate_x": radians_to_degree(obj.rotation_euler[0]) - 90,
                "rotate_y": radians_to_degree(obj.rotation_euler[1]),
                "rotate_z": radians_to_degree(obj.rotation_euler[2]),
            },
            "model": {
                "type": obj.lig_ar_obj.model_type,
                "fields": {},
            },
        }
        r = requests.patch('https://api.lig.com.tw/api/ar_objects/%r' % obj.lig_ar_obj.ar_id, json=data, headers=self.auth_headers())
        return r

    def scene_list(self):
        r = requests.get('https://api.lig.com.tw/api/scenes', headers=self.auth_headers())
        if not r:
            return []

        return r.json()['scenes']


class LiGObject(PropertyGroup):
    ar_id: IntProperty(name='Identifier', default=0)
    model_type: IntProperty(name='AR Model type', default=0)
    scale_x: FloatProperty(name='Scale X', default=1.0)
    scale_y: FloatProperty(name='Scale Y', default=1.0)
    scale_z: FloatProperty(name='Scale Z', default=1.0)
    managed: BoolProperty(name='Managed by LiG Cloud', default=False)


class SceneProperty(PropertyGroup):
    lid: StringProperty(name='LiG Scene ID', subtype='NONE')


class ScenesProperty(PropertyGroup):
    name: StringProperty(name='LiG Scene', subtype='NONE')


class LiGPreferences(AddonPreferences):
    bl_idname = __name__

    email: StringProperty(name="Light Space account(email)", subtype='NONE',)
    password: StringProperty(name="Password", subtype='PASSWORD',)
    token: StringProperty(name="Access Token", subtype='NONE',)

    def draw(self, context):
        layout = self.layout
        layout.label(text='LiG Cloud accounts')
        if self.token:
            layout.label(text='User: ' + self.email)
            layout.operator(LiGLogoutOperator.bl_idname)
        else:
            layout.prop(self, 'email')
            layout.prop(self, 'password')
            layout.operator(LiGLoginOperator.bl_idname)


class LiGScenePanel(Panel):
    bl_label = "LiG Cloud"
    bl_idname = "OBJECT_PT_lig_scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.operator(LiGSetupOperator.bl_idname, text='Refresh Scene List')
        if len(context.scene.lig_scenes) > 0:
            layout.prop_search(context.scene, "lig_scene", context.scene, "lig_scenes", icon='NODE')
        if context.scene.lig_scene:
            layout.operator(LiGDownloader.bl_idname, text='Download AR Objects')
            layout.operator(LiGUploader.bl_idname, text='Upload AR Objects')


class LiGObjectPanel(Panel):
    bl_label = "LiG AR Object"
    bl_idname = "OBJECT_PT_lig_obj"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.lig_ar_obj, 'ar_id')
        row = layout.row()
        row.prop(obj.lig_ar_obj, 'managed')
        row = layout.row()
        row.prop(obj.lig_ar_obj, 'model_type')
        row = layout.row()
        row.prop(obj.lig_ar_obj, 'scale_x')
        row = layout.row()
        row.prop(obj.lig_ar_obj, 'scale_y')
        row = layout.row()
        row.prop(obj.lig_ar_obj, 'scale_z')

class LiGSetupOperator(Operator):
    bl_idname = "lig.setup"
    bl_label = "Create default lig collection and refresh scene list"

    def execute(self, context):
        # Create lig scene collection
        lig_coll = None
        if 'lig' in bpy.data.collections:
            lig_coll = bpy.data.collections['lig']
        else:
            lig_coll = bpy.data.collections.new('lig')
            bpy.context.scene.collection.children.link(lig_coll)

        context.scene.lig_scenes.clear()
        for scene in ApiClient.shared().scene_list():
            context.scene.lig_scenes.add().name = '%d %s' % (scene['id'], scene['name'],)
        return { 'FINISHED' }

class LiGLogoutOperator(Operator):
    bl_idname = "lig.logout_operator"
    bl_label = "Logout LiG Cloud"
    #bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ApiClient.shared().logout()
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        addon_prefs.token = ''
        return { 'FINISHED' }


class LiGLoginOperator(Operator):
    bl_idname = "lig.login_operator"
    bl_label = "Login LiG Cloud"
    #bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        lig_client = ApiClient.shared()
        ret = lig_client.login(addon_prefs.email, addon_prefs.password)
        if not ret:
            self.report({'ERROR'}, 'Unable to login LiG CLoud. %r' % lig_client.errors)
            return { 'CANCELLED' }
        addon_prefs.token = lig_client.get_token()

        return { 'FINISHED' }


class LiGUploader(Operator):
    bl_idname = "lig.uploader"
    bl_label = "Upload ArObjects to LiG Cloud"
    #bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if 'lig' not in bpy.data.collections:
            self.report({'ERROR'}, 'Please client setup first!')
            return {'CANCELLED'}
        lig_coll = bpy.data.collections['lig']

        client = ApiClient.shared()
        for obj in lig_coll.objects:
            if not obj.lig_ar_obj.managed:
                continue
            # Only upload location and rotation
            res = client.sync_with_server(obj, self)
            if res.status_code != 200:
                self.report({'ERROR'}, 'ArObject (%r) data failed in uploading. %r' % (obj.lig_ar_obj.ar_id, res.text))

        return { 'FINISHED' }


def menu_func_import(self, context):
    pass
    #self.layout.operator(LiGLoginOperator.bl_idname, text="LiG Cloud")


def menu_func_export(self, context):
    pass
    #self.layout.operator(LiGUploader.bl_idname, text="LiG Cloud")


classes = (
    LiGDownloader,
    LiGUploader,
    SceneProperty,
    ScenesProperty,
    LiGScenePanel,
    LiGObjectPanel,
    LiGObject,
    LiGPreferences,
    LiGSetupOperator,
    LiGLogoutOperator,
    LiGLoginOperator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file.append(menu_func_import)
    #bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    #bpy.types.Scene.lig_scene = PointerProperty(type=SceneProperty)
    bpy.types.Scene.lig_scene = StringProperty(name='LiG Scene ID', subtype='NONE')
    bpy.types.Scene.lig_scenes = CollectionProperty(type=ScenesProperty)
    bpy.types.Object.lig_ar_obj = PointerProperty(type=LiGObject)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file.remove(menu_func_import)
    #bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
