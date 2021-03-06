# -*- Mode:Python -*-

##########################################################################
#                                                                        #
# This file is part of AVANGO.                                           #
#                                                                        #
# Copyright 1997 - 2009 Fraunhofer-Gesellschaft zur Foerderung der       #
# angewandten Forschung (FhG), Munich, Germany.                          #
#                                                                        #
# AVANGO is free software: you can redistribute it and/or modify         #
# it under the terms of the GNU Lesser General Public License as         #
# published by the Free Software Foundation, version 3.                  #
#                                                                        #
# AVANGO is distributed in the hope that it will be useful,              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the           #
# GNU General Public License for more details.                           #
#                                                                        #
# You should have received a copy of the GNU Lesser General Public       #
# License along with AVANGO. If not, see <http://www.gnu.org/licenses/>. #
#                                                                        #
##########################################################################
'''
A distributed viewer setup: This Python scripts starts an
avango.osg.simpleviewer and connects to the distribution group "testgroup". If
there is another instance loading some geometry under this node this model
should also appear in the client.  (see also simpleviewer-srv.py)
'''

import avango
import avango.script
import avango.gua
import avango.gua.lod
from avango.script import field_has_changed

from examples_common.GuaVE import GuaVE

#avango.enable_logging(4, "client.log")

## print the subgraph under a given node to the console
def print_graph(root_node):
    stack = [(root_node, 0)]
    while stack:
        node, level = stack.pop()
        print("│   " * level + "├── {0} <{1}>".format(
          node.Name.value, node.__class__.__name__))
        stack.extend(
          [(child, level + 1) for child in reversed(node.Children.value)])

class NetInit(avango.script.Script):
    NetChildren = avango.gua.MFNode()
    WindowName = avango.SFString()
    Viewer = avango.gua.nodes.Viewer()

    def __init__(self):
      self.super(NetInit).__init__()
      self.always_evaluate(True)
      self.is_initialized = False

    def my_constructor(self, scenegraph):
      self.scenegraph = scenegraph
      print('setup!')

    def evaluate(self):
      if len(self.NetChildren.value) > 0 and self.is_initialized:
        node = self.scenegraph["/net/multi_view_trans_node"]

        
        # print(node.Name.value)
        # print(node.WorldTransform.value)
        #node.clear_vertices()
        #node.push_vertex(1, 0, 0, 1, 0, 0)
        #node.push_vertex(-1, 0, 0, 1, 0, 0)

    @field_has_changed(NetChildren)
    def update(self):      
      if len(self.NetChildren.value) > 0 and not self.is_initialized:
        print("JAAAA  ")
        print_graph(self.scenegraph.Root.value)
        node = self.scenegraph["/net/multi_view_trans_node/multi_window_vis"]
        if node:
          print(node.Name.value)
          print('VT flag',node.Material.value.EnableVirtualTexturing.value )
          print("!!!!!!!!!!!!", node.Material.value.m_serializedUniforms.value)
          #node.Material.value.EnableVirtualTexturing.value = True
          node.Material.value.set_uniform("vt_images", atlas_path)
        # print('######################', node.Name.value)
        # node.RenderVolumetric.value = False
        self.is_initialized = True
        cam = self.scenegraph["/net/client_navigation/client_cam"]
        vt_backend.add_camera(cam)
        vt_backend.start_backend()

nettrans = avango.gua.nodes.NetTransform(Name="net",
                                         # specify role, ip, and port
                                         # Groupname="AVCLIENT|141.54.147.59|7432")
                                         Groupname="AVCLIENT|141.54.147.60|7432")
                                         # Groupname="AVCLIENT|127.0.0.1|7432")

# aux_path = "/home/ephtron/Documents/master-render-files/salem/salem_atlas.aux"
# atlas_path = "/home/ephtron/Documents/master-render-files/salem/salem.atlas"
# aux_path = "/opt/3d_models/lamure/provenance/salem/salem_atlas.aux"
# atlas_path = "/opt/3d_models/lamure/provenance/salem/salem.atlas"
# atlas_path = '/home/senu8384/Desktop/master-thesis/data/study/trial_a_tex.atlas'
atlas_path = '/home/senu8384/Desktop/master-thesis/data/study/test-study/test_trial_all.atlas'
# atlas_path = '/home/senu8384/Desktop/master-thesis/data/study/test-study/test_trial_all.atlas'
atlas_path = "/home/senu8384/Desktop/master-thesis/data/study/condition-real/cr-head-version1/cr_head_version1_tex.atlas"


graph = avango.gua.nodes.SceneGraph(Name="scenegraph")
graph.Root.value.Children.value = [nettrans]

size = avango.gua.Vec2ui(7680, 4320)
# size = avango.gua.Vec2ui(800, 600)

# window = avango.gua.nodes.GlfwWindow(Size=size,
window = avango.gua.nodes.Window(Size=size,
                                 LeftResolution=size,
                                 Title="client_window")
avango.gua.register_window("client_window", window)

logger = avango.gua.nodes.Logger(EnableWarning=False)

vt_backend = avango.gua.VTBackend()

viewer = avango.gua.nodes.Viewer()
viewer.SceneGraphs.value = [graph]
viewer.Windows.value = [window]

init = NetInit()
init.my_constructor(graph)
init.WindowName.value = "client_window"
init.Viewer = viewer
init.NetChildren.connect_from(nettrans.Children)

guaVE = GuaVE()
guaVE.start(locals(), globals())

viewer.run()

