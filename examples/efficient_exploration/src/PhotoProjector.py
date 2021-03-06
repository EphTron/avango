import avango
import avango.script
import avango.gua
from avango.script import field_has_changed

import random
import math
import time


class PhotoProjector(avango.script.Script):

    Material = avango.gua.SFMaterial()
    # Material1 = avango.gua.MFMaterial()
    Transform = avango.gua.SFMatrix4()
    Graph = avango.gua.SFSceneGraph()
    Texture = avango.SFString()
    Number = avango.SFInt()

    number_of_instances = 0

    def __init__(self):
        self.super(PhotoProjector).__init__()
        print('### INIT PhotoProjector')
        self.always_evaluate(True)
        self.is_initialized = False

    def my_constructor(self, parent_node, quad_node, quad_parent_node, images=None):
        self.id = PhotoProjector.number_of_instances
        PhotoProjector.number_of_instances += 1

        self.parent_node = parent_node

        self.projection_quad = quad_node
        self.quad_parent_node = quad_parent_node

        self.images = images
        for image in self.images:
            print(image)

        self.min_tex_coords = avango.gua.Vec2(0.0, 0.0)
        self.max_tex_coords = avango.gua.Vec2(0.1, 0.1)
        self.selected_photo_id = None
        self.last_photo_id = None
        self.frame_count = 0

        self.offset = avango.gua.make_identity_mat()
        loader = avango.gua.nodes.TriMeshLoader()
        self.group_node = avango.gua.nodes.TransformNode(Name = "projector_group_" + str(self.id),
                                                         Transform = avango.gua.make_trans_mat(0.0,0.0,0.0))
        self.group_node.Transform.value = avango.gua.make_trans_mat(0.0,0.0,0.0)
        self.group_node.Transform.connect_from(self.Transform)

        self.geometry = loader.create_geometry_from_file("projector_geometry_"+str(self.id), "data/objects/projector.obj", 
          avango.gua.LoaderFlags.NORMALIZE_SCALE |
          avango.gua.LoaderFlags.NORMALIZE_POSITION)

        self.Number.value = self.id
        print('my number',self.Number.value)
        self.geometry.Transform.value = avango.gua.make_scale_mat(0.3)
        self.group_node.Children.value.append(self.geometry)

        self.screen = avango.gua.nodes.ScreenNode(
          Name = "screen_" + str(self.id),
          Width = 0.1,
          Height = 0.1,
          Transform = avango.gua.make_trans_mat(0.0, 0.0, -0.1)
        )
        self.group_node.Children.value.append(self.screen)
        # print('creating cam', self.id)
        self.cam = avango.gua.nodes.CameraNode(
          Name="c_"+str(self.id),
          # LeftScreenPath = "/net/multi_view_trans_node/quad_trans_"+str(self.id)+"/projector_group_" + str(self.id) + "/photo_projector_" + str(self.id),
          LeftScreenPath = "/projector_group_" + str(self.id) + "/screen_" + str(self.id),
          # LeftScreenPath = "/quad_trans_"+str(self.id) +"/projector_group_" + str(self.id) + "/photo_projector_" + str(self.id),
          SceneGraph = "scenegraph",
          Transform = avango.gua.make_trans_mat(0.0,0.0,0.0)
        )
        self.group_node.Children.value.append(self.cam)

        self.shader_name = "proj_mat_"+str(self.id)

        my_mat = avango.gua.nodes.Material(
          ShaderName = self.shader_name
        )
        self.Material.value = my_mat
        # self.Material1.value.append(my_mat)


        self.Graph.value = avango.gua.nodes.SceneGraph(Name = "dummy"+str(self.id))
        print('photo projector material=', self.Material)
        shader_discription_name = 'shader_disc_'+str(self.id)
        print(shader_discription_name)

        self.material = self.Material
        print(self.id, ' own mat', self.material)


        proj_mat_desc = avango.gua.nodes.MaterialShaderDescription(Name=shader_discription_name)
        print('photo projector material==', self.Material)
        proj_mat_desc.load_from_file("data/materials/Projective_VT_Material"+str(self.id)+".gmd")

        # proj_mat_desc.EnableVirtualTexturing.value = True

        
        # if self.projection_quad:
        #     self.projection_quad.Material.connect_from(self.Material)
        #     print('Connected material', self.Material.value)
        #     print('quad ', self.projection_quad.Name.value, 'material:', self.projection_quad.Material.value)
        self.parent_node.Children.value.append(self.group_node)
        avango.gua.register_material_shader(proj_mat_desc, self.shader_name)
        print('photo projector material4', self.Material)

    def set_projection_quad(self, quad_node, quad_parent_node):
        if self.projection_quad is not None:
            self.projection_quad.Material.disconnect_from(self.Material)
        self.projection_quad = quad_node
        self.quad_parent_node = quad_parent_node
        self.projection_quad.Material.connect_from(self.Material)

    def set_texture_coords(self, min_uv, max_uv):
        self.min_tex_coords = min_uv
        self.max_tex_coords = max_uv

    @field_has_changed(Transform)
    def update_matrices(self):
        # print('updated matrices')
        print(self.selected_photo_id)
        frustum = self.cam.get_frustum(self.Graph.value, avango.gua.CameraMode.CENTER)

        projection_matrix = frustum.ProjectionMatrix.value
        view_matrix = frustum.ViewMatrix.value
        
        self.Material.value.set_uniform("projective_texture_matrix", projection_matrix)
        self.Material.value.set_uniform("view_texture_matrix", view_matrix) 
        self.Material.value.set_uniform("Emissivity", 1.0)
        self.Material.value.set_uniform("Roughness", 1.0)
        self.Material.value.set_uniform("Metalness", 0.0)
        self.Material.value.set_uniform("view_port_min", avango.gua.Vec2(self.min_tex_coords))
        self.Material.value.set_uniform("view_port_max", avango.gua.Vec2(self.max_tex_coords))
        print(self.min_tex_coords)
        print(self.max_tex_coords)
        print(self.screen.Name.value, self.screen.Width.value, self.screen.WorldTransform.value.get_translate() )
        print(self.cam.Name.value, self.cam.WorldTransform.value.get_translate() )
        # self.Material1.value[self.id].set_uniform("projective_texture_matrix", projection_matrix)
        # self.Material1.value[self.id].set_uniform("view_texture_matrix", view_matrix) 
        # self.Material1.value[self.id].set_uniform("Emissivity", 1.0)
        # self.Material1.value[self.id].set_uniform("Roughness", 1.0)
        # self.Material1.value[self.id].set_uniform("Metalness", 0.0)
        # self.Material1.value[self.id].set_uniform("view_port_min", avango.gua.Vec2(self.min_tex_coords))
        # self.Material1.value[self.id].set_uniform("view_port_max", avango.gua.Vec2(self.max_tex_coords))

    @field_has_changed(Texture)
    def update_texture(self):
        # print('setup texture')
        self.Material.value.set_uniform("projective_texture", self.Texture.value)
        self.Material.value.set_uniform("Emissivity", 1.0)
        self.Material.value.EnableVirtualTexturing.value = True
        # self.Material1.value[self.id].set_uniform("projective_texture", self.Texture.value)
        # self.Material1.value[self.id].set_uniform("Emissivity", 1.0)
        # self.Material1.value[self.id].EnableVirtualTexturing.value = True
      
    def update_images(self, image_id):
        if self.images:
            self.selected_photo_id = image_id
            if self.selected_photo_id < len(self.images):
                # print('updated projection image', image_id)
                self.min_tex_coords = self.images[self.selected_photo_id].min_uv
                # print('set min uv coords', self.min_tex_coords)
                self.max_tex_coords = self.images[self.selected_photo_id].max_uv
                self.screen.Width.value = self.images[self.selected_photo_id].img_w_half * 2
                self.screen.Height.value = self.images[self.selected_photo_id].img_h_half * 2
            else:
                print('Photo Projector Error: Not enough images - set images')
            print('Updated image', image_id)
          
    def update_perspective(self, min_uv, max_uv, image_width, image_height, image_id=None):
        self.min_tex_coords = min_uv
        self.max_tex_coords = max_uv
        self.screen.Width.value = image_width
        self.screen.Height.value = image_height
        # photo id not necessary
        self.selected_photo_id = image_id

    def evaluate(self):
        self.frame_count += 1
        self.frame_count = self.frame_count % 120
        if self.frame_count == 0:
            self.selected_photo_id += 1
            self.update_images(self.selected_photo_id)
        if self.last_photo_id != self.selected_photo_id:
            self.update_matrices()
            self.last_photo_id = self.selected_photo_id

    
