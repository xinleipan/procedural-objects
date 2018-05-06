"""Hammer generator.
"""

import os
import random

import numpy as np

from bodies.body import Body
from links.link import Link
from links.scad_link import ScadCubeLink
from links.scad_link import ScadCylinderLink
from links.scad_link import ScadPolygonLink
from utils.transformations import matrix3_from_euler


LATERAL_FRICTION_RANGE = [0.2, 1.0]
SPINNING_FRICTION_RANGE = [0.2, 1.0]
INERTIA_FRICTION_RANGE = [0.2, 1.0]

HANDLE_CONFIG = {
        'mass_range': [0.5, 1.0],
        'size_range': [[0.1, 0.1], [0.2, 0.2], [1, 1]],
        'lateral_friction_range': LATERAL_FRICTION_RANGE,
        'spinning_friction_range': SPINNING_FRICTION_RANGE,
        'inertia_friction_range': INERTIA_FRICTION_RANGE,
        }

HEAD_CONFIG = {
        'mass_range': [0.5, 1.0],
        'size_range': [[0.1, 0.1], [0.2, 0.2], [1, 1]],
        'lateral_friction_range': LATERAL_FRICTION_RANGE,
        'spinning_friction_range': SPINNING_FRICTION_RANGE,
        'inertia_friction_range': INERTIA_FRICTION_RANGE,
        }


def transform_point(point, rotation, translation):
    """Rigid transformation of a point.

    Args:
        point: A 3-dimensional vector.
        rotation: The rotation in Euler angles.
        translation: The translation as a 3-dimensional vector.

    Returns:
        The transformed point as a 3-dimensional vector.
    """
    roll = rotation[0]
    pitch = rotation[1]
    yaw = rotation[2]
    rotation_matrix = matrix3_from_euler(roll, pitch, yaw)

    return rotation_matrix.dot(point) + np.array(translation)


class Hammer(Body):
    """Hammer generator.

    A hammer is defined as a two-part object composed of a handle and a head.
    """

    def __init__(self, name, obj_paths=None, random_flip=True):
        """Initialize.

        Args:
            name: The name of the body.
            obj_paths: If None, use OpenScad to gnerate objects; otherwise
                sample objects from obj_paths.
            random_flip: If true, randomly flip the parts along the three axes.
        """
        with open('templates/hammer.xml', 'r') as f:
            self.template = f.read()

        if obj_paths is None:
            self.handle_generators = [
                    ScadCubeLink(name='handle', **HANDLE_CONFIG),
                    ScadCylinderLink(name='handle', **HANDLE_CONFIG),
                    ScadPolygonLink(name='handle', **HANDLE_CONFIG),
                    ]

            self.head_generators = [
                    ScadCubeLink(name='head', **HEAD_CONFIG),
                    ScadCylinderLink(name='head', **HEAD_CONFIG),
                    ScadPolygonLink(name='head', **HEAD_CONFIG),
                    ]
        else:
            self.handle_generators = [
                    Link(
                        name='handle',
                        obj_paths=obj_paths,
                        **HANDLE_CONFIG)
                    ]

            self.head_generators = [
                    Link(
                        name='head',
                        obj_paths=obj_paths,
                        **HEAD_CONFIG)
                    ]

        self.random_flip = random_flip

        self.name = name

    def generate(self, path):
        """Generate a body.

        Args:
            path: The folder to save the URDF and OBJ files.
        """
        handle_generator = random.choice(self.handle_generators)
        head_generator = random.choice(self.head_generators)

        # Generate links.
        handle_data = handle_generator.generate(path)
        head_data = head_generator.generate(path)

        # Modify links' positions and orientations.
        rotation, transition = self.sample_head_transformation(
                handle_data, head_data)
        center = [head_data['x'], head_data['y'], head_data['z']]
        center = transform_point(center, rotation, transition)
        head_data['x'] = center[0]
        head_data['y'] = center[1]
        head_data['z'] = center[2]
        head_data['roll'] = rotation[0]
        head_data['pitch'] = rotation[1]
        head_data['yaw'] = rotation[2]

        # TODO(kuanfang): Random flipping.
        if self.random_flip:
            pass

        # Genearte the URDF files.
        handle_urdf = handle_generator.convert_data_to_urdf(handle_data)
        head_urdf = head_generator.convert_data_to_urdf(head_data)
        urdf = self.template.format(
                name=self.name,
                handle_link=handle_urdf,
                head_link=head_urdf,
                handle_name=handle_data['name'],
                head_name=head_data['name'],
                )

        # Write URDF to file.
        urdf_filename = os.path.join(path, '%s.urdf' % (self.name))
        with open(urdf_filename, 'w') as f:
            f.write(urdf)

    def sample_head_transformation(self, handle_data, head_data):
        """Sample the transformation for the head pose.

        Args:
            handle_data: The data dictionary of the handle.
            head_data: The data dictionary of the head.

        Returns:
            rotation: The rotation as Euler angles.
            translation: The translation vector.
        """
        # The orthogonal T-Shape hammer.
        rotation = [0.5 * np.pi, 0, 0]
        translation = [0, 0, 0.5 * handle_data['size_z']]

        return rotation, translation
