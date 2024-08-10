import numpy as np
import scipy


class Link:
    def __init__(self, name, length, bounds=None):
        if bounds is None:
            self.bounds = (-np.inf, np.inf)
        else:
            self.bounds = bounds
        self.name = name
        self.length = length
        self.axis_length = length
        self.has_rotation = False
        self.has_translation = False
        self.joint_type = None

    def __repr__(self):
        return "Link name={} bounds={}".format(self.name, self.bounds)

    def get_link_frame_matrix(self, parameters):
        raise NotImplementedError


class OriginLink(Link):
    def __init__(self):
        Link.__init__(self, name="Base link", length=1)
        self.has_rotation = False
        self.has_translation = False
        self.joint_type = "fixed"

    def get_link_frame_matrix(self, theta):
        return np.eye(4)


class URDFLink(Link):
    def __init__(
        self,
        name: str,
        origin_translation: np.ndarray,
        origin_orientation: np.ndarray,
        rotation: np.ndarray = None,
        bounds=None,
        joint_type: str = "revolute",
    ):
        Link.__init__(self, name=name, bounds=bounds, length=np.linalg.norm(origin_translation))
        self.origin_translation = np.array(origin_translation)
        self.origin_orientation = np.array(origin_orientation)
        if rotation is not None:
            self.rotation = np.array(rotation)
            self.has_rotation = True
        else:
            self.rotation = None
            self.has_rotation = False

        if joint_type == "revolute":
            if not (self.has_rotation and not self.has_translation):
                raise ValueError(
                    "Joint type is 'revolute' but rotation axis = {} and translation axis = {}".format(
                        self.has_rotation, self.has_translation
                    )
                )
        elif joint_type == "prismatic":
            if not (not self.has_rotation and self.has_translation):
                raise ValueError(
                    "Joint type is 'prismatic' but rotation axis = {} and translation axis = {}".format(
                        self.has_rotation, self.has_translation
                    )
                )
        elif joint_type == "fixed":
            if not (not self.has_rotation and not self.has_translation):
                raise ValueError(
                    "Joint type is 'fixed' but rotation axis = {} and translation axis = {}".format(
                        self.has_rotation, self.has_translation
                    )
                )
        else:
            raise ValueError("Unknown joint type: {}".format(joint_type))
        self.joint_type = joint_type

    def __repr__(self):
        return """URDF Link {} :
    Type : {}
    Bounds : {}
    Origin Translation : {}
    Origin Orientation : {}
    Rotation : {}""".format(
            self.name, self.joint_type, self.bounds, self.origin_translation, self.origin_orientation, self.rotation
        )

    def get_link_frame_matrix(self, parameters):
        if self.joint_type == "revolute":
            theta = parameters
            mu = None
        elif self.joint_type == "prismatic":
            theta = None
            mu = parameters
        elif self.joint_type == "fixed":
            theta = None
            mu = None
        else:
            raise ValueError

        frame_matrix = np.eye(4)
        frame_matrix = np.dot(frame_matrix, homogeneous_translation_matrix(*self.origin_translation))
        frame_matrix = np.dot(frame_matrix, cartesian_to_homogeneous(rpy_matrix(*self.origin_orientation)))

        if self.has_rotation:
            frame_matrix = np.dot(frame_matrix, cartesian_to_homogeneous(axis_rotation_matrix(self.rotation, theta)))

        return frame_matrix


class Chain:
    def __init__(self, links, active_links_mask=None, name="chain"):
        self.name = name
        self.links = links

        if active_links_mask is not None:
            if len(active_links_mask) != len(self.links):
                raise ValueError(
                    "Your active links mask length of {} is different from the number of your links, which is {}".format(
                        len(active_links_mask), len(self.links)
                    )
                )
            self.active_links_mask = np.array(active_links_mask)
        else:
            self.active_links_mask = np.array([True] * len(links))

        if self.active_links_mask[-1] is True:
            # print("active_link_mask[-1] is True, but it should be set to False. Overriding and setting to False")
            self.active_links_mask[-1] = False

        for link_index, (link_active, link) in enumerate(zip(self.active_links_mask, self.links)):
            if link.joint_type == "fixed" and link_active:
                ...
                # print("Link {} (index: {}) is of type 'fixed' but set as active in the active_links_mask. In practice, this fixed link doesn't provide any transformation so is as it were inactive".format(link.name, link_index))

    def forward_kinematics(self, joints, full_kinematics=False):
        frame_matrix = np.eye(4)

        if full_kinematics:
            frame_matrixes = []

        if len(self.links) != len(joints):
            raise ValueError(
                "Your joints vector length is {} but you have {} links".format(len(joints), len(self.links))
            )

        for index, (link, joint_parameters) in enumerate(zip(self.links, joints)):
            frame_matrix = np.dot(frame_matrix, np.asarray(link.get_link_frame_matrix(joint_parameters)))
            if full_kinematics:
                frame_matrixes.append(frame_matrix)

        if full_kinematics:
            return frame_matrixes
        else:
            return frame_matrix

    def inverse_kinematics(
        self, target_position=None, target_orientation=None, orientation_mode=None, initial_position=None, **kwargs
    ):
        frame_target = np.eye(4)

        if orientation_mode is not None:
            if orientation_mode == "X":
                frame_target[:3, 0] = target_orientation
            elif orientation_mode == "Y":
                frame_target[:3, 1] = target_orientation
            elif orientation_mode == "Z":
                frame_target[:3, 2] = target_orientation
            elif orientation_mode == "all":
                frame_target[:3, :3] = target_orientation
            else:
                raise ValueError("Unknown orientation mode: {}".format(orientation_mode))

        if target_position is None:
            no_position = True
        else:
            no_position = False
            frame_target[:3, 3] = target_position

        if initial_position is None:
            initial_position = [0] * len(self.links)  # Set default initial positions

        return inverse_kinematic_optimization(
            self,
            target=frame_target,
            starting_nodes_angles=initial_position,
            orientation_mode=orientation_mode,
            no_position=no_position,
            **kwargs
        )

    def active_to_full(self, active_joints, initial_position):
        full_joints = np.array(initial_position, copy=True, dtype=np.float64)
        np.place(full_joints, self.active_links_mask, active_joints)
        return full_joints

    def active_from_full(self, joints):
        return np.compress(self.active_links_mask, joints, axis=0)


def inverse_kinematic_optimization(chain, target, starting_nodes_angles, **kwargs):
    target = target[:3, -1]

    def optimize_basis(x):
        y = chain.active_to_full(x, starting_nodes_angles)
        fk = chain.forward_kinematics(y)
        return fk

    def optimize_target_function(fk):
        target_error = fk[:3, -1] - target
        return target_error

    if kwargs.get("orientation_mode") is None:

        def optimize_function(x):
            fk = optimize_basis(x)
            target_error = optimize_target_function(fk)
            return target_error

    else:
        raise NotImplementedError("Only position-based IK is supported in this minimized version.")

    if starting_nodes_angles is None:
        raise ValueError("starting_nodes_angles must be specified")

    real_bounds = chain.active_from_full([link.bounds for link in chain.links])

    res = scipy.optimize.least_squares(
        optimize_function, chain.active_from_full(starting_nodes_angles), bounds=np.moveaxis(real_bounds, -1, 0)
    )

    return chain.active_to_full(res.x, starting_nodes_angles)


def axis_rotation_matrix(axis, theta):
    [x, y, z] = axis
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array(
        [
            [x * x * (1 - c) + c, x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
            [y * x * (1 - c) + z * s, y * y * (1 - c) + c, y * z * (1 - c) - x * s],
            [x * z * (1 - c) - y * s, y * z * (1 - c) + x * s, z * z * (1 - c) + c],
        ]
    )


def rpy_matrix(roll, pitch, yaw):
    return np.dot(rz_matrix(yaw), np.dot(ry_matrix(pitch), rx_matrix(roll)))


def rx_matrix(theta):
    return np.array([[1, 0, 0], [0, np.cos(theta), -np.sin(theta)], [0, np.sin(theta), np.cos(theta)]])


def ry_matrix(theta):
    return np.array([[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], [-np.sin(theta), 0, np.cos(theta)]])


def rz_matrix(theta):
    return np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])


def homogeneous_translation_matrix(trans_x, trans_y, trans_z):
    return np.array([[1, 0, 0, trans_x], [0, 1, 0, trans_y], [0, 0, 1, trans_z], [0, 0, 0, 1]])


def cartesian_to_homogeneous(cartesian_matrix):
    dimension_x, dimension_y = cartesian_matrix.shape
    homogeneous_matrix = np.eye(dimension_x + 1)
    homogeneous_matrix[:-1, :-1] = cartesian_matrix
    return homogeneous_matrix
