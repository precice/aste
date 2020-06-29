import unittest
import mesh_io
import numpy as np


class MiscTests(unittest.TestCase):
    def test_edge_cell_type(self):
        type1 = mesh_io.get_cell_type(2)
        self.assertIsNotNone(type1)
        type2 = mesh_io.get_cell_type((1, 2))
        self.assertIsNotNone(type2)
        self.assertEqual(type1, type2)

    def test_triangle_cell_type(self):
        type1 = mesh_io.get_cell_type(3)
        self.assertIsNotNone(type1)
        type2 = mesh_io.get_cell_type((1, 2, 3))
        self.assertIsNotNone(type2)
        self.assertEqual(type1, type2)

    def test_unknown_cell_type(self):
        type1 = mesh_io.get_cell_type(1)
        self.assertIsNone(type1)
        type2 = mesh_io.get_cell_type((1, 2, 3, 4, 5))
        self.assertIsNone(type2)

    def test_cell_types_different(self):
        type1 = mesh_io.get_cell_type(2)
        type2 = mesh_io.get_cell_type(3)
        self.assertNotEqual(type1, type2)


class MeshTests(unittest.TestCase):
    def test_empty_mesh(self):
        mesh = mesh_io.Mesh()
        self.assertEqual(mesh.points.size, 0)
        self.assertEqual(mesh.data.size, 0)
        self.assertEqual(mesh.edges.size, 0)
        self.assertEqual(mesh.triangles.size, 0)
        self.assertEqual(len(mesh.cells), 0)
        self.assertEqual(mesh.celltypes.size, 0)

    def test_load_simple(self):
        mesh = mesh_io.Mesh.load("tests/simple.txt")
        self.assertEqual(mesh.points.size, 4 * 3)
        self.assertEqual(mesh.points.shape, (4, 3))
        self.assertSequenceEqual(
            mesh.points.tolist(),
            [[0, 0, 0], [0, 1.0, 0], [0, 0, 1.0], [0, 1.0, 1.0]])

        self.assertEqual(mesh.data.size, 4)
        self.assertEqual(mesh.data.shape, (4, ))
        self.assertSequenceEqual(mesh.data.tolist(), [0.0, 0.1, -0.2, 5.2])

        self.assertEqual(mesh.edges.size, 0)
        self.assertEqual(mesh.triangles.size, 0)
        self.assertEqual(len(mesh.cells), 0)
        self.assertEqual(mesh.celltypes.size, 0)

    def test_load_edges(self):
        mesh = mesh_io.Mesh.load("tests/edges.txt")
        self.assertEqual(mesh.points.size, 4 * 3)
        self.assertEqual(mesh.points.shape, (4, 3))
        self.assertSequenceEqual(
            mesh.points.tolist(),
            [[0, 0, 0], [0, 1.0, 0], [0, 0, 1.0], [0, 1.0, 1.0]])

        self.assertEqual(mesh.data.size, 4)
        self.assertEqual(mesh.data.shape, (4, ))
        self.assertSequenceEqual(mesh.data.tolist(), [0, 0, 0, 0])

        self.assertEqual(mesh.edges.size, 4 * 2)
        self.assertEqual(mesh.edges.shape, (4, 2))
        self.assertSequenceEqual(mesh.edges.tolist(),
                                 [[0, 1], [0, 2], [1, 3], [2, 3]])

        self.assertEqual(mesh.triangles.size, 0)

        self.assertEqual(len(mesh.cells), 4)
        self.assertSequenceEqual(mesh.cells, mesh.edges.tolist())

        edgetype = mesh_io.get_cell_type(2)
        self.assertEqual(mesh.celltypes.size, 4)
        self.assertEqual(mesh.celltypes.shape, (4, ))
        self.assertTrue(np.all(mesh.celltypes == edgetype))

    def test_load_triangles(self):
        mesh = mesh_io.Mesh.load("tests/triangles.txt")
        self.assertEqual(mesh.points.size, 4 * 3)
        self.assertEqual(mesh.points.shape, (4, 3))
        self.assertSequenceEqual(mesh.points.tolist(),
                                 [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                  [0.0, 0.0, 1.0], [0.0, 1.0, 1.0]])

        self.assertEqual(mesh.data.size, 4)
        self.assertEqual(mesh.data.shape, (4, ))
        self.assertSequenceEqual(mesh.data.tolist(), [0, 0, 0, 0])

        self.assertEqual(mesh.edges.size, 0)

        self.assertEqual(mesh.triangles.size, 2 * 3)
        self.assertEqual(mesh.triangles.shape, (2, 3))
        self.assertSequenceEqual(mesh.triangles.tolist(),
                                 [[0, 1, 2], [1, 3, 2]])

        self.assertEqual(len(mesh.cells), 2)
        self.assertSequenceEqual(mesh.cells, mesh.triangles.tolist())

        triangletype = mesh_io.get_cell_type(3)
        self.assertEqual(mesh.celltypes.size, 2)
        self.assertEqual(mesh.celltypes.shape, (2, ))
        self.assertTrue(np.all(mesh.celltypes == triangletype))

    def test_append(self):
        mesh1 = mesh_io.Mesh(points=[[0, 0, 0], [1, 1, 1]],
                             data=[0.1, 1.2],
                             edges=[[0, 1]])
        mesh1.validate()
        mesh2 = mesh_io.Mesh(points=[[2, 2, 2], [3, 3, 3]],
                             data=[0.3, 1.4],
                             edges=[[0, 1]])
        mesh2.validate()
        mesh1.append(mesh2)

        self.assertEqual(mesh1.points.size, 4 * 3)
        self.assertEqual(mesh1.points.shape, (4, 3))
        self.assertSequenceEqual(mesh1.points.tolist(),
                                 [[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]])

        self.assertEqual(mesh1.data.size, 4)
        self.assertEqual(mesh1.data.shape, (4, ))
        self.assertSequenceEqual(mesh1.data.tolist(), [0.1, 1.2, 0.3, 1.4])

        self.assertEqual(mesh1.edges.size, 2 * 2)
        self.assertEqual(mesh1.edges.shape, (2, 2))
        self.assertSequenceEqual(mesh1.edges.tolist(), [[0, 1], [2, 3]])

        self.assertEqual(mesh1.triangles.size, 0)

        self.assertEqual(len(mesh1.cells), 2)
        self.assertSequenceEqual(mesh1.cells, mesh1.edges.tolist())

        edgetype = mesh_io.get_cell_type(2)
        self.assertEqual(mesh1.celltypes.size, 2)
        self.assertEqual(mesh1.celltypes.shape, (2, ))
        self.assertTrue(np.all(mesh1.celltypes == edgetype))
