import numpy as np
from path import path

from safe_cv import cv


class TransformTest(object):
    def __init__(self, in_file):
        self.in_file = path(in_file)

    def get_rotated_image(self, in_image, rotate_degrees):
        rotated = cv.CreateImage((in_image.width, in_image.height), 8, in_image.channels)
        map_mat = cv.CreateMat(2, 3, cv.CV_32FC1)
        cv.GetRotationMatrix2D((rotated.width * 0.5, rotated.height * 0.5),
                                rotate_degrees, 1., map_mat)
        cv.WarpAffine(in_image, rotated, map_mat)
        return rotated, map_mat

    def get_affine_image(self, in_image, map_mat):
        warped = cv.CreateImage((in_image.width, in_image.height), 8,
                                in_image.channels)
        a = [(0, 0), (in_image.width, in_image.height), (in_image.width, 0)]
        b = self.transform(a, map_mat)
        warped_mat = cv.CreateMat(2, 3, cv.CV_32FC1)
        cv.GetAffineTransform(a, b, warped_mat)
        cv.WarpAffine(in_image, warped, warped_mat, flags=cv.CV_WARP_INVERSE_MAP)
        return warped, warped_mat

    def transform(self, points, map_mat):
        np_map = np.asarray(map_mat)
        get_transform_point = lambda x:\
            tuple(np_map.dot(np.array((points[x][0], points[x][1], 1))\
            .transpose()))
        return map(get_transform_point, range(len(points)))

    def get_perspective_image(self, in_image, map_mat):
        warped = cv.CreateImage((in_image.width, in_image.height), 8,
                                in_image.channels)
        a = [(0,0), (in_image.width, in_image.height), (in_image.width, 0),
                (0, in_image.height)]
        b = self.transform(a, map_mat)
        warped_mat = cv.CreateMat(2, 3, cv.CV_32FC1)
        cv.GetAffineTransform(a, b, warped_mat)
        cv.WarpAffine(in_image, warped, warped_mat, flags=cv.CV_WARP_INVERSE_MAP)
        return warped, warped_mat

    def test_affine_transform(self, rotate_degrees, out_file_prefix=None):
        if out_file_prefix is None:
            out_file_prefix = self.in_file.parent.joinpath(self.in_file.namebase)
        original = cv.LoadImageM(self.in_file)
        rotated, map_mat = self.get_rotated_image(original, rotate_degrees)
        cv.SaveImage('%s-affine_rotated%s' % (out_file_prefix, self.in_file.ext),
                        rotated)

        warped, warped_mat = self.get_affine_image(rotated, map_mat)
        cv.SaveImage('%s-affine_warped%s' % (out_file_prefix, self.in_file.ext),
                        warped)

    def test_perspective_transform(self, rotate_degrees, out_file_prefix=None):
        if out_file_prefix is None:
            out_file_prefix = self.in_file.parent.joinpath(self.in_file.namebase)
        original = cv.LoadImageM(self.in_file)
        rotated, map_mat = self.get_rotated_image(original, rotate_degrees)
        cv.SaveImage('%s-perspective_rotated%s' % (out_file_prefix, self.in_file.ext),
                        rotated)

        warped = cv.CreateImage((original.width, original.height), 8, original.channels)
        warped, warped_mat = self.get_perspective_image(rotated, map_mat)
        cv.SaveImage('%s-perspective_warped%s' % (out_file_prefix, self.in_file.ext),
                        warped)
