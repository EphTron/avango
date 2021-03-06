import avango
import avango.script
from avango.script import field_has_changed
import avango.gua
import avango.gua.lod



class LocalizedImageQuad:
    def __init__(self, graph, dt_node, quad_id, view, atlas_tile, atlas):
        self.dt_node = dt_node
        self.graph = graph
        self.id = quad_id
        self.view = view

        self.transform = avango.gua.make_rot_mat(-90.0, 1.0, 0.0, 0.0) * self.view.get_transform()
        # self.transform = self.view.get_transform()
        self.rotation = avango.gua.make_rot_mat(self.transform.get_rotate_scale_corrected())
        # HARDCODED TRANSFORM TODO
        # transform_pos = avango.gua.make_rot_mat(-90.0, 1.0, 0.0, 0.0) * self.transform.get_translate()
        # transforma = avango.gua.make_rot_mat(-90.0, 1.0, 0.0, 0.0) * self.transform
        # transform_pos = self.dt_node.Transform.value * self.transform.get_translate()
        self.position = avango.gua.Vec3(self.transform.get_translate()[0], 
                                        self.transform.get_translate()[1], 
                                        self.transform.get_translate()[2])
        _rot_mat = avango.gua.make_rot_mat(self.transform.get_rotate_scale_corrected())
        _abs_dir = _rot_mat * avango.gua.Vec3(0.0,0.0,-1.0)
        self.direction = avango.gua.Vec3(_abs_dir.x,_abs_dir.y,_abs_dir.z) # cast to vec3
        
        self.frustum = None
        self.indicator = None

        mat = avango.gua.nodes.Material()
        loader = avango.gua.nodes.TriMeshLoader()
        # self.indicator = loader.create_geometry_from_file("img_indicator_"+ str(quad_id), "data/objects/cube.obj")
        # self.indicator.Material.value = mat
        # self.indicator.Transform.value = self.transform * \
        #                          avango.gua.make_scale_mat(0.001, 0.001, 2.0)
        # self.show_ind_flag = False
        self.select_ind_flag = False

        # self.graph.Root.value.Children.value.append(self.indicator)

        self.atlas_tile = atlas_tile
        self.atlas = atlas
        self.quad_vertices = []
        self.min_uv = avango.gua.Vec2(0.0, 0.0)
        self.max_uv = avango.gua.Vec2(1.0, 1.0)

        self.setup()
        self.create_quad()
        self.init_camera_setup()

        screen_transform = avango.gua.make_trans_mat(self.position) * self.rotation * avango.gua.make_trans_mat(0.0, 0.0, -0.1) *\
            avango.gua.make_rot_mat(90.0, 1.0, 0.0, 0.0) * avango.gua.make_scale_mat(self.img_w_half, self.img_h_half, self.img_h_half)
        # self.frustum = avango.gua.make_perspective_frustum(self.transform, screen_transform, 0.05, 3.0)


    def init_camera_setup(self):
        group_node = avango.gua.nodes.TransformNode(Name = "quad_"+str(self.id))
        self.graph.Root.value.Children.value.append(group_node)

        screen_transform = avango.gua.make_trans_mat(self.position)  * self.rotation * avango.gua.make_trans_mat(0.0, 0.0, -0.1) # *\
            # avango.gua.make_rot_mat(90.0, 1.0, 0.0, 0.0) #* avango.gua.make_scale_mat(self.img_w_half, self.img_h_half, self.img_h_half)
        screen = avango.gua.nodes.ScreenNode(
          Name = "dummyscreen"+str(self.id),
          Width = self.img_w_half,
          Height = self.img_h_half,
          Transform = screen_transform
        )
        group_node.Children.value.append(screen)

        cam = avango.gua.nodes.CameraNode(
          LeftScreenPath = screen.Path.value,
          RightScreenPath = screen.Path.value,
          SceneGraph = "scenegraph",
          Transform = self.transform
        )
        group_node.Children.value.append(cam)
        # print(cam.Transform.value, screen_transform)

        self.frustum = cam.get_frustum(self.graph, avango.gua.CameraMode.CENTER)
        group_node.Children.value.remove(cam)
        del cam
        group_node.Children.value.remove(screen)
        del screen
        self.graph.Root.value.Children.value.remove(group_node)
        del group_node
        

    def get_frustum(self):
        #self.frustum = self.cam.get_frustum(self.graph, avango.gua.CameraMode.CENTER)
        #   print('frusturm exists', self.group_node.Name.value)
        screen_transform = avango.gua.make_trans_mat(self.position)  * self.rotation * avango.gua.make_trans_mat(0.0, 0.0, -1.1) 
        pos = screen_transform.get_translate()
        # print(self.frustum.contains(avango.gua.Vec3(0.0,1.0,0.0)))
        # print(self.frustum.contains(pos))
        # print(self.frustum.Corners.value[0], self.frustum.Corners.value[1], self.frustum.Corners.value[2],  self.frustum.Corners.value[3])        
        

    def set_selected(self, selected, show):
        if show and self.show_ind_flag == False:
            # self.indicator.Transform.value = self.transform * \
            #                      avango.gua.make_scale_mat(0.001, 0.001, 2.0)
            self.graph.Root.value.Children.value.append(self.indicator)
            self.show_ind_flag = True

        elif show == False and self.show_ind_flag:
            self.graph.Root.value.Children.value.remove(self.indicator)
            self.show_ind_flag = False

        mat = self.indicator.Material.value

        if show:
            unselected_col = avango.gua.Vec4(0.2, 0.2, 0.6, 1.0)
            selected_col = avango.gua.Vec4(0.2, 1.0, 1.0, 1.0)
            if selected:
                mat.set_uniform("Color", selected_col)            
            else:
                
                mat.set_uniform("Color", unselected_col)

            mat.set_uniform("Roughness", 1.0)
            mat.set_uniform("Emissivity", 1.0)
            mat.set_uniform("Metalness", 0.0)

            self.indicator.Material.value = mat
            
        return mat

    def setup(self):
        self.aspect_ratio = self.view.get_image_height() / self.view.get_image_width()
        # print('aspect_ratio', self.aspect_ratio)

        # focal_length = view.get_focal_length() // Problem: Return 0 carl said not perfect yet
        self.focal_length = 0.1
        self.img_w_half = self.focal_length * 0.5
        self.img_h_half = self.img_w_half * self.aspect_ratio
        # print('img_w_half', self.img_w_half)
        # print('img_h_half', self.img_h_half)
        
        self.atlas_width  = self.atlas.get_width()
        self.atlas_height = self.atlas.get_height()

        # scale factor from image space to vt atlas space
        # float factor = get_atlas_scale_factor();
        self.factor = 0.950787

        self.tile_h = self.atlas_tile.get_width() / self.atlas_width * self.factor
        self.tile_w = self.atlas_tile.get_width() / self.atlas_height * self.factor

        self.tile_pos_x = self.atlas_tile.get_x() / self.atlas_height * self.factor
        self.tile_pos_y = self.atlas_tile.get_y() / self.atlas_tile.get_height() * self.tile_h + (1 - self.factor)

    def create_quad(self):
        transform = self.view.get_transform() #* avango.gua.make_rot_mat(180.0, 0.0, 1.0,0.0)

        pos = transform * avango.gua.Vec3(self.img_w_half, self.img_h_half, -self.focal_length)
        uv  = avango.gua.Vec2(self.tile_pos_x, self.tile_pos_y)
        t1_v1 = LocalizedImageVertex(self.dt_node, self.id * 6, pos, uv)
        
        pos = transform * avango.gua.Vec3(-self.img_w_half, -self.img_h_half, -self.focal_length)
        uv  = avango.gua.Vec2(self.tile_pos_x + self.tile_w, self.tile_pos_y + self.tile_h)
        t1_v2 = LocalizedImageVertex(self.dt_node, self.id * 6 + 1, pos, uv)
        
        pos = transform * avango.gua.Vec3(self.img_w_half, -self.img_h_half, -self.focal_length)
        uv  = avango.gua.Vec2(self.tile_pos_x, self.tile_pos_y + self.tile_h)
        t1_v3 = LocalizedImageVertex(self.dt_node, self.id * 6 + 2, pos, uv)
        
        pos = transform * avango.gua.Vec3(self.img_w_half, self.img_h_half, -self.focal_length)
        uv  = avango.gua.Vec2(self.tile_pos_x, self.tile_pos_y)
        t2_v4 = LocalizedImageVertex(self.dt_node, self.id * 6 + 3, pos, uv)
        
        pos = transform * avango.gua.Vec3(-self.img_w_half, self.img_h_half, -self.focal_length)
        uv  = avango.gua.Vec2(self.tile_pos_x + self.tile_w, self.tile_pos_y )
        t2_v5 = LocalizedImageVertex(self.dt_node, self.id * 6 + 4, pos, uv)

        pos = transform * avango.gua.Vec3(-self.img_w_half, -self.img_h_half, -self.focal_length)
        uv  = avango.gua.Vec2(self.tile_pos_x + self.tile_w, self.tile_pos_y + self.tile_h)
        t2_v6 = LocalizedImageVertex(self.dt_node, self.id * 6 + 5, pos, uv)

        self.min_uv = avango.gua.Vec2(self.tile_pos_x, self.tile_pos_y)
        self.max_uv = avango.gua.Vec2(self.tile_pos_x + self.tile_w, self.tile_pos_y + self.tile_h)

        self.quad_vertices = [t1_v1, t1_v2, t1_v3, t2_v4, t2_v5, t2_v6]


class LocalizedImageVertex:
    def __init__(self, node, vertex_id, pos, uv):
        self.vertex_id = vertex_id
        self.dt_node = node 
        self.color = (1.0, 0.0, 0.0, 1.0)
        self.pos = pos
        self.uv = uv
        self.dt_node.push_vertex(self.pos.x, self.pos.y, self.pos.z, 1.0, 0.0, 0.0, 1.0, self.uv.x, self.uv.y)
        # self.dt_node.push_vertex(*self.pos, 1.0, 0.0, 0.0, 1.0, *self.uv)
        # print()

    def update(self, pos=None, uv=None):
        pass
    
# def get_atlas_scale_factor():
    
    # atlas_width  = atlas.get_width()
    # atlas_height = atlas.get_height()
    # auto atlas = new vt::pre::AtlasFile(settings_.atlas_file_.c_str());
    # uint64_t image_width    = atlas->getImageWidth();
    # uint64_t image_height   = atlas->getImageHeight();

    # // tile's width and height without padding
    # uint64_t tile_inner_width  = atlas->getInnerTileWidth();
    # uint64_t tile_inner_height = atlas->getInnerTileHeight();

    # // Quadtree depth counter, ranges from 0 to depth-1
    # uint64_t depth = atlas->getDepth();

    # double factor_u  = (double) image_width  / (tile_inner_width  * std::pow(2, depth-1));
    # double factor_v  = (double) image_height / (tile_inner_height * std::pow(2, depth-1));

    # return std::max(factor_u, factor_v);
