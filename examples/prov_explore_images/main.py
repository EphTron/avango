import avango
import avango.script
from avango.script import field_has_changed
import avango.gua
import avango.gua.lod
import avango.daemon
import examples_common.navigator
from examples_common.GuaVE import GuaVE

import subprocess

from src.localized_image import LocalizedImageController
from src.picker import Picker

from src.MultiUserViewingSetup import MultiUserViewingSetup

from src.SpheronInput import DualSpheronInput
from src.SpheronNavigation import SpheronNavigation


def start():
    # setup scene graph
    graph = avango.gua.nodes.SceneGraph(Name="scenegraph")

    # Create basic loaders
    mesh_loader = avango.gua.nodes.TriMeshLoader()
    lod_loader = avango.gua.lod.nodes.LodLoader()

    # setup scene
    transform_node = setup_scene(graph, mesh_loader, lod_loader)

    #### Create app logic below here ####

    # Create localized image controller
    localized_image_controller = LocalizedImageController(graph,
        transform_node, 
        "/home/ephtron/Documents/master-render-files/salem/salem_atlas.aux",
        "/home/ephtron/Documents/master-render-files/salem/salem.atlas")
        # "/opt/3d_models/lamure/provenance/salem/salem_atlas.aux",
        # "/opt/3d_models/lamure/provenance/salem/salem.atlas")

    projector = localized_image_controller.get_projector()

    #### Create app logic above here ####

    hostname = subprocess.Popen(["hostname"], stdout=subprocess.PIPE, universal_newlines=True).communicate()[0]
    hostname = hostname.strip("\n")

    if hostname == "hydra":        
        ## DLP wall 4-user setup
        viewingSetup = MultiUserViewingSetup(
            SCENEGRAPH = graph,
            WINDOW_RESOLUTION = avango.gua.Vec2ui(3840*2, 2160),
            SCREEN_DIMENSIONS = avango.gua.Vec2(4.91, 2.78),
            TRACKING_TRANSMITTER_OFFSET = avango.gua.make_trans_mat(0.0,-1.445,2.0),
            DISPLAY_STRING_LIST = [":0.0", ":0.1", ":0.2", ":0.3"], # number of available GPUs (users)
            LEFT_POSITION = avango.gua.Vec2ui(0, 0),
            LEFT_RESOLUTION = avango.gua.Vec2ui(3840, 2160),
            RIGHT_POSITION = avango.gua.Vec2ui(3840, 0),
            RIGHT_RESOLUTION = avango.gua.Vec2ui(3840, 2160),
            )
        viewingSetup.init_user(HEADTRACKING_SENSOR_STATION = "tracking-dbl-glasses-A")
        # viewingSetup.init_user(HEADTRACKING_SENSOR_STATION = "tracking-dbl-glasses-B")
        # viewingSetup.init_user(HEADTRACKING_SENSOR_STATION = "tracking-dbl-glasses-C")
        # viewingSetup.init_user(HEADTRACKING_SENSOR_STATION = "tracking-dbl-glasses-D")      

        spheron_input = DualSpheronInput(
            DEVICE_STATION1 = "device-new-spheron-right",
            DEVICE_STATION2 = "device-new-spheron-left",
            TRANSLATION_FACTOR = 0.2,
            ROTATION_FACTOR = 10.0,
            #SCALE_FACTOR = 1.0,
            )

        navigation = SpheronNavigation(
            #INITIAL_MODE = 1, # groundfollowing navigation mode
            REFERENCE_TRACKING_STATION = "tracking-new-spheron",
            TRANSMITTER_OFFSET = avango.gua.make_trans_mat(0.0,0.045,0.0), # transformation into tracking coordinate system        
            )
        navigation.assign_input(spheron_input)  
        viewingSetup.navigation_node.Transform.connect_from(navigation.get_platform_matrix_field())

        # add prototyp lense
        dynamic_quad = mesh_loader.create_geometry_from_file("dynamic_quad", "data/objects/plane2.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
        dynamic_quad.Material.value.set_uniform("Metalness", 0.0)
        dynamic_quad.Material.value.set_uniform("Emissivity", 1.0)
        dynamic_quad.Material.value.set_uniform("Roughness", 1.0)
        # dynamic_quad.Material.connect_from(projector.Material)
        # projector.Material.value.EnableVirtualTexturing.value = True
        # dynamic_quad.Material.value.EnableVirtualTexturing.value = True

        dynamic_quad.Transform.value = avango.gua.make_trans_mat(0.0, 0.2, 0) *\
                                       avango.gua.make_rot_mat(90.0, 1.0, 0.0, 0.0) * \
                                       avango.gua.make_scale_mat(0.25)
        localized_image_controller.set_tracked_element(dynamic_quad)

        pointer_tracking_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        pointer_tracking_sensor.Station.value = "tracking-dbl-pointer-1"
        pointer_tracking_sensor.TransmitterOffset.value = avango.gua.make_trans_mat(0.0,-1.445,2.0)
        pointer_tracking_sensor.ReceiverOffset.value = avango.gua.make_identity_mat()
        
        pointer_node = avango.gua.nodes.TransformNode(Name = "pointer_node")
        pointer_node.Transform.connect_from(pointer_tracking_sensor.Matrix)
        pointer_node.Children.value.append(dynamic_quad)

        viewingSetup.navigation_node.Children.value.append(pointer_node)
        projector.Transform2.connect_from(dynamic_quad.WorldTransform)

        print_graph(graph.Root.value)

        ## start application/render loop
        viewingSetup.run(locals(), globals())
    else:
        
        # config window size
        width = 1920;
        height = int(width * 9.0 / 16.0)
        size = avango.gua.Vec2ui(width, height)

        # setup view
        cam, screen = setup_camera(graph, size)

          # create backend for virtual texture and vt update
        vt_backend = avango.gua.VTBackend()
        vt_backend.add_camera(cam)
        vt_backend.start_backend()

        # setup_picker(mesh_loader, cam, graph)

        # add light nodes
        spot_light_1 = avango.gua.nodes.LightNode(Name="spot_light_1",
                                                  Type=avango.gua.LightType.SPOT,
                                                  Color=avango.gua.Color(1.0, 1.0, 1.0),
                                                  EnableShadows=True,
                                                  ShadowMapSize=1024,
                                                  ShadowOffset=0.002,
                                                  ShadowMaxDistance=10,
                                                  Falloff=1.5,
                                                  ShadowNearClippingInSunDirection=0.1,
                                                  ShadowFarClippingInSunDirection=10.0,
                                                  Softness=2,
                                                  Brightness=20)
        spot_light_1.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0) * \
                                       avango.gua.make_rot_mat(-90, 1, 0, 0) * \
                                       avango.gua.make_scale_mat(4)
        # graph.Root.value.Children.value.append(spot_light_1)
        screen.Children.value.append(spot_light_1)
        spot_light_1.Transform.value = cam.Transform.value * avango.gua.make_trans_mat(0.0,0.0,0.7)

        # add prototyp lense
        # dynamic_quad = mesh_loader.create_geometry_from_file("dynamic_quad", "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS)
        # dynamic_quad.Material.value.set_uniform("Metalness", 0.0)
        # dynamic_quad.Material.value.set_uniform("Emissivity", 1.0)
        # dynamic_quad.Material.value.set_uniform("Roughness", 1.0)
        
        # projector.Material.value.EnableVirtualTexturing.value = True
        # dynamic_quad.Material.value.EnableVirtualTexturing.value = True
        # dynamic_quad.Material.value.EnableBackfaceCulling.value = True
        # projector.set_projection_object(dynamic_quad)

        # dynamic_quad.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 2.1) *\
        #                                avango.gua.make_rot_mat(90.0, 1.0, 0.0, 0.0) * \
        #                                avango.gua.make_scale_mat(0.00001)
        # print_graph(graph.Root.value)
        # screen.Children.value.append(dynamic_quad)
        # localized_image_controller.set_tracked_element(dynamic_quad)

        loader = avango.gua.nodes.DynamicTriangleLoader()
        dynamic_lense = loader.create_empty_geometry(
            "dynamic_lense", 
            "empty_name_2.lob", 
            avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)

        transform = avango.gua.make_trans_mat(0.0, 0.0, 0.0)
        size = 0.5

        # pos = transform * avango.gua.Vec3( size, size, 0.0)
        # uv  = avango.gua.Vec2(1.0, 0.0)
        # print(type(uv.x))
        # dynamic_lense.push_vertex(pos.x, pos.y, pos.z, 1.0, 0.0, 0.0, 1.0, int(uv.x), int(uv.y) )
        # print("tes")
        
        # pos = transform * avango.gua.Vec3(-size, -size, 0.0)
        # uv  = avango.gua.Vec2(0.0, 1.0)
        # dynamic_lense.push_vertex(pos.x, pos.y, pos.z, 1.0, 0.0, 0.0, 1.0, int(uv.x), int(uv.y))
        # print('dddd')

        # pos = transform * avango.gua.Vec3( size, -size, 0.0)
        # uv  = avango.gua.Vec2(1.0, 1.0)
        # dynamic_lense.push_vertex(pos.x, pos.y, pos.z, 1.0, 0.0, 0.0, 1.0, int(uv.x), int(uv.y))
        # print('sdfsdf')

        dynamic_lense.push_vertex(-2.0,  2.0, -2.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.1);
        dynamic_lense.push_vertex( 2.0, -2.0, -2.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.1);
        dynamic_lense.push_vertex( 2.0,  2.0, -2.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.2);

        # pos = transform * avango.gua.Vec3( size, size, 0.0)
        # uv  = avango.gua.Vec2(1.0, 0.0)
        # dynamic_lense.push_vertex(pos.x, pos.y, pos.z, 1.0, 0.0, 0.0, 1.0, uv.x, uv.y)
        
        # pos = transform * avango.gua.Vec3(-size, size, 0.0)
        # uv  = avango.gua.Vec2(0.0, 0.0)
        # dynamic_lense.push_vertex(pos.x, pos.y, pos.z, 1.0, 0.0, 0.0, 1.0, uv.x, uv.y)

        # pos = transform * avango.gua.Vec3(-size, -size, 0.0)
        # uv  = avango.gua.Vec2(0.0, 1.0)
        # dynamic_lense.push_vertex(pos.x, pos.y, pos.z, 1.0, 0.0, 0.0, 1.0, uv.x, uv.y)

        # screen.Children.value.append(dynamic_lense)
        graph.Root.value.Children.value.append(dynamic_lense)

        # setup render passes
        setup_render_passes(cam)

        # setup Window
        win = setup_window(size)

        # setup navigator
        navi = setup_navigator(cam)
        projector.Transform2.connect_from(navi.OutTransform)
        projector.Button0.connect_from(navi.Mouse.ButtonLeft)
        # tn.Transform.connect_from(navi.)
        # vtprojector.Transform.connect_from(navi.OutTransform)

        # setup viewer with scenegraph
        setup_viewer(graph, win)


def print_graph(root_node):
  stack = [(root_node, 0)]
  while stack:
    node, level = stack.pop()
    print("│   " * level + "├── {0} <{1}>".format(
      node.Name.value, node.__class__.__name__))
    stack.extend(
      [(child, level + 1) for child in reversed(node.Children.value)])


def setup_scene(graph, mesh_loader, lod_loader):
    # add transform node for plod object
    trans_node = avango.gua.nodes.TransformNode(Name="scene_trans")
    trans_node.Transform.value = avango.gua.make_trans_mat(0, 0.0, 0) * \
                                 avango.gua.make_rot_mat(-90.0, 1.0, 0.0, 0.0)
    plod_trans_node = avango.gua.nodes.TransformNode(Name="scene")
    # plod_trans_node.Transform.value = avango.gua.make_trans_mat(0, 0, 0.0)
    graph.Root.value.Children.value.append(trans_node)
    trans_node.Children.value.append(plod_trans_node)

    # configure lod loader 
    lod_loader.UploadBudget.value = 64
    lod_loader.RenderBudget.value = 2048
    lod_loader.OutOfCoreBudget.value = 4096

    # load salem point cloud
    plod_node = lod_loader.load_lod_pointcloud(
        "/home/ephtron/Documents/master-render-files/salem/salem_02.bvh", avango.gua.LoaderFlags.DEFAULTS)
        # "/opt/3d_models/lamure/provenance/salem/salem_02.bvh", avango.gua.LoaderFlags.DEFAULTS)

    # plod_node.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 1.0, 1.0, 1.0))
    plod_node.Material.value.set_uniform("Emissivity", 1.0)
    plod_node.ShadowMode.value = 1
    plod_trans_node.Children.value.append(plod_node)

    # floor = mesh_loader.create_geometry_from_file("floor",
    #                                               "data/objects/plane.obj",
    #                                               avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE
    #                                               )

    # floor.Transform.value = avango.gua.make_trans_mat(0, -0.4, 0) * avango.gua.make_scale_mat(4, 1, 4) 
    # # floor.ShadowMode.value = 1
    # graph.Root.value.Children.value.append(floor)

    

    return trans_node


def setup_camera(graph, size):
    screen = avango.gua.nodes.ScreenNode(Name="screen",
                                         Width=4.8,
                                         Height=2.7)
    screen.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, -2.5)

    camera = avango.gua.nodes.CameraNode(Name="cam",
                                         LeftScreenPath="/cam/screen",
                                         RightScreenPath="/cam/screen",
                                         SceneGraph="scenegraph",
                                         Resolution=size,
                                         OutputWindowName="window",
                                         EyeDistance=0.2,
                                         EnableStereo=False,
                                         Children=[screen],
                                         Transform=avango.gua.make_trans_mat(0.0, 0.0, 2.0))
    graph.Root.value.Children.value.append(camera)

    return camera, screen

def setup_picker(mesh_loader, camera, graph):
    # setup pick ray
    pick_ray = avango.gua.nodes.RayNode(Name = "pick_ray")
    pick_ray.Transform.value = avango.gua.make_trans_mat(0.0, -0.15, 0.0) * \
                               avango.gua.make_scale_mat(1.0, 1.0, 1.0)

    ray_geom = mesh_loader.create_geometry_from_file(
        "ray_geom",
        "data/objects/cylinder.obj",
        avango.gua.LoaderFlags.DEFAULTS)
  
    ray_geom.Transform.value = avango.gua.make_scale_mat(0.01, 0.01, 10)
    pick_ray.Children.value.append(ray_geom)

    picker = Picker()
    picker.SceneGraph.value = graph
    picker.Ray.value = pick_ray
    camera.Children.value.append(pick_ray)

def setup_render_passes(camera):
    res_pass = avango.gua.nodes.ResolvePassDescription()
    res_pass.EnableSSAO.value = False
    res_pass.SSAOIntensity.value = 3.0
    res_pass.SSAOFalloff.value = 20.0
    res_pass.SSAORadius.value = 10.0
    res_pass.EnvironmentLightingColor.value = avango.gua.Color(0.1, 0.7, 0.6)
    res_pass.ToneMappingMode.value = avango.gua.ToneMappingMode.UNCHARTED
    res_pass.Exposure.value = 1.0
    # res_pass.BackgroundMode.value = avango.gua.BackgroundMode.CUBEMAP_TEXTURE
    res_pass.BackgroundTexture.value = "awesome_skymap"
    res_pass.BackgroundColor.value = avango.gua.Color(0.40, 0.5, 0.6)
    # res_pass.VignetteColor.value = avango.gua.Vec4(0, 0, 0, 1)

    plod_pass = avango.gua.lod.nodes.PLodPassDescription()
    plod_pass.SurfelRenderMode.value = avango.gua.lod.RenderFlags.HQ_TWO_PASS
    # plod_pass.SurfelRenderMode.value = avango.gua.lod.RenderFlags.LQ_ONE_PASS

    pipeline_description = avango.gua.nodes.PipelineDescription(
        Passes=[
                # avango.gua.nodes.TriMeshPassDescription(),
                plod_pass,
                avango.gua.nodes.DynamicTrianglePassDescription(),
                # avango.gua.nodes.DeferredVirtualTexturingPassDescription(),
                # avango.gua.nodes.SkyMapPassDescription(OutputTextureName="awesome_skymap"),
                avango.gua.nodes.LightVisibilityPassDescription(),
                res_pass,
                # avango.gua.nodes.DebugViewPassDescription()
                ],
        EnableABuffer=False)

    camera.PipelineDescription.value = pipeline_description

   

def setup_window(size):
    print('################## WINDOW 1')
    window = avango.gua.nodes.Window(Size=size,
                                     Title="shadows",
                                     LeftResolution=size,
                                     RightResolution=size,
                                     EnableVsync=True,
                                     # StereoMode=avango.gua.StereoMode.MONO)
                                     )
    avango.gua.register_window("window", window)
    print('################## WINDOW 2')

    return window

def setup_navigator(camera):
    navigator = examples_common.navigator.Navigator()
    navigator.StartLocation.value = camera.Transform.value.get_translate()
    print('Start Location:', navigator.StartLocation.value)
    navigator.OutTransform.connect_from(camera.Transform)

    navigator.RotationSpeed.value = 0.2
    navigator.MotionSpeed.value = 0.04

    camera.Transform.connect_from(navigator.OutTransform)
    return navigator

def setup_viewer(graph, window):
    viewer = avango.gua.nodes.Viewer()
    # viewer.DesiredFPS.value = 200
    viewer.SceneGraphs.value = [graph]
    viewer.Windows.value = [window]

    timer = avango.nodes.TimeSensor()

    guaVE = GuaVE()
    guaVE.start(locals(), globals())

    viewer.run()


### helper functions ###

## print the subgraph under a given node to the console
def print_graph(root_node):
    stack = [(root_node, 0)]
    while stack:
        node, level = stack.pop()
        print("│   " * level + "├── {0} <{1}>".format(
          node.Name.value, node.__class__.__name__))
        stack.extend(
          [(child, level + 1) for child in reversed(node.Children.value)])

## print all fields of a fieldcontainer to the console
def print_fields(node, print_values = False):
    for i in range(node.get_num_fields()):
        field = node.get_field(i)
        print("→ {0} <{1}>".format(field._get_name(), field.__class__.__name__))
    if print_values:
        print("  with value '{0}'".format(field.value))



if __name__ == '__main__':


    a = avango.gua.Vec3(1.073,  0.915,  5.322) 
    b = [avango.gua.Vec3(0.117,  1.234,  -0.167)]
    b.append(avango.gua.Vec3(0.265,  1.199,  -0.168))
    b.append(avango.gua.Vec3(0.395,  1.143,  -0.169))
    b.append(avango.gua.Vec3(0.578,  1.092,  -0.172))

    start()
