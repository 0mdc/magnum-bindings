#
#   This file is part of Magnum.
#
#   Copyright © 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
#               2020, 2021, 2022 Vladimír Vondruš <mosra@centrum.cz>
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the "Software"),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included
#   in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#   THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#

import array
import sys
import unittest

from magnum import *

class PixelStorage_(unittest.TestCase):
    def test_init(self):
        a = PixelStorage()
        self.assertEqual(a.alignment, 4)
        self.assertEqual(a.row_length, 0)
        self.assertEqual(a.image_height, 0)
        self.assertEqual(a.skip, Vector3i())

    def test_properties(self):
        a = PixelStorage()
        a.alignment = 1
        a.row_length = 64
        a.image_height = 256
        a.skip = (3, 1, 2)
        self.assertEqual(a.alignment, 1)
        self.assertEqual(a.row_length, 64)
        self.assertEqual(a.image_height, 256)
        self.assertEqual(a.skip, Vector3i(3, 1, 2))

class Image(unittest.TestCase):
    def test_init_empty(self):
        storage = PixelStorage()
        storage.alignment = 1
        a = Image2D(storage, PixelFormat.RGB8_UNORM)
        self.assertEqual(a.storage.alignment, 1)
        self.assertEqual(a.size, Vector2i())
        self.assertEqual(a.format, PixelFormat.RGB8_UNORM)

        b = Image2D(PixelFormat.R8I)
        self.assertEqual(b.storage.alignment, 4)
        self.assertEqual(b.size, Vector2i())
        self.assertEqual(b.format, PixelFormat.R8I)

    @unittest.skip("No way to create a non-empty Image at the moment")
    def test_data_access(self):
        # Tested in test_gl_gl.Framebuffer.test_read_image instead
        a = Image2D(PixelFormat.R8I, Vector2i(3, 17)) # TODO
        a_refcount = sys.getrefcount(a)

        data = a.data
        self.assertEqual(len(data), 3*17*1)
        self.assertIs(data.owner, a)
        self.assertEqual(sys.getrefcount(a), a_refcount + 1)

        del data
        self.assertEqual(sys.getrefcount(a), a_refcount)

    def test_data_access_empty(self):
        a = Image2D(PixelFormat.R8I)
        a_refcount = sys.getrefcount(a)

        data = a.data
        self.assertEqual(len(data), 0)
        self.assertIs(data.owner, None)
        self.assertEqual(sys.getrefcount(a), a_refcount)

    @unittest.skip("No way to create a non-empty Image at the moment")
    def test_pixels_access(self):
        # Tested in test_gl_gl.Framebuffer.test_read_image instead
        a = Image2D(PixelFormat.RG32UI, Vector2i(3, 17)) # TODO
        a_refcount = sys.getrefcount(a)

        pixels = a.pixels
        self.assertEqual(pixels.size, (3, 17))
        self.assertEqual(pixels.stride, (17*8, 8))
        self.assertEqual(pixels.format, '2I')
        self.assertIs(pixels.owner, a)
        self.assertEqual(sys.getrefcount(a), a_refcount + 1)

        del pixels
        self.assertEqual(sys.getrefcount(a), a_refcount)

    def test_pixels_access_empty(self):
        a = Image2D(PixelFormat.RGB8I)
        a_refcount = sys.getrefcount(a)

        pixels = a.pixels
        self.assertEqual(pixels.size, (0, 0))
        self.assertEqual(pixels.stride, (0, 3))
        self.assertEqual(pixels.format, '3b')
        self.assertIs(pixels.owner, None)
        self.assertEqual(sys.getrefcount(a), a_refcount)

    def test_pixels_access_unsupported_format(self):
        a = Image2D(PixelFormat.DEPTH32F)

        with self.assertRaisesRegex(NotImplementedError, "access to this pixel format is not implemented yet, sorry"):
            a.pixels

class ImageView(unittest.TestCase):
    def test_init(self):
        # 2x4 RGB pixels, padded for alignment
        data = (b'rgbRGB  '
                b'abcABC  '
                b'defDEF  '
                b'ijkIJK  ')
        data_refcount = sys.getrefcount(data)

        a = ImageView2D(PixelFormat.RGB8_UNORM, (2, 4), data)
        self.assertEqual(a.storage, PixelStorage())
        self.assertEqual(a.size, Vector2i(2, 4))
        self.assertEqual(a.format, PixelFormat.RGB8_UNORM)
        self.assertEqual(a.pixel_size, 3)
        self.assertEqual(a.owner, data)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        del a
        self.assertEqual(sys.getrefcount(data), data_refcount)

    def test_init_storage(self):
        # 2x2x2 RGB pixels
        data = (b'rgbRGB'
                b'abcABC'
                b'defDEF'
                b'ijkIJK')
        data_refcount = sys.getrefcount(data)

        storage = PixelStorage()
        storage.alignment = 2
        a = ImageView3D(storage, PixelFormat.RGB8_UNORM, (2, 2, 2), data)
        self.assertEqual(a.storage.alignment, 2)
        self.assertEqual(a.size, Vector3i(2, 2, 2))
        self.assertEqual(a.format, PixelFormat.RGB8_UNORM)
        self.assertEqual(a.pixel_size, 3)
        self.assertEqual(a.owner, data)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        del a
        self.assertEqual(sys.getrefcount(data), data_refcount)

    def test_init_empty(self):
        a = MutableImageView1D(PixelFormat.RG16UI, 32)
        self.assertEqual(a.storage.alignment, 4)
        self.assertEqual(a.size, 32)
        self.assertEqual(a.owner, None)

        storage = PixelStorage()
        storage.alignment = 2
        b = ImageView2D(storage, PixelFormat.R32F, (8, 8))
        self.assertEqual(b.storage.alignment, 2)
        self.assertEqual(b.size, Vector2i(8, 8))
        self.assertEqual(b.owner, None)

    def test_init_mutable(self):
        # 2x4 RGB pixels, padded for alignment
        data = bytearray(b'rgbRGB  '
                         b'abcABC  '
                         b'defDEF  '
                         b'ijkIJK  ')
        data_refcount = sys.getrefcount(data)

        a = MutableImageView2D(PixelFormat.RGB8_UNORM, (2, 4), data)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        # Back to immutable
        b = ImageView2D(a)
        self.assertEqual(b.size, Vector2i(2, 4))
        self.assertEqual(b.format, PixelFormat.RGB8_UNORM)
        self.assertEqual(b.pixel_size, 3)
        self.assertEqual(len(b.data), 32)
        self.assertIs(b.owner, data)
        self.assertEqual(sys.getrefcount(data), data_refcount + 2)

    @unittest.skip("No way to create a non-empty Image at the moment")
    def test_init_image(self):
        # Tested in test_gl_gl.Framebuffer.test_read_image instead
        a = Image2D(PixelFormat.R32F, Vector2i(3, 17)) # TODO
        a_refcount = sys.getrefcount(a)

        view = ImageView2D(a)
        self.assertEqual(view.size, (3, 17))
        self.assertIs(view.owner, a)
        self.assertEqual(sys.getrefcount(a), a_refcount + 1)

        del view
        self.assertEqual(sys.getrefcount(a), a_refcount)

        mview = MutableImageView2D(a)
        self.assertEqual(mview.size, (3, 17))
        self.assertIs(mview.owner, a)
        self.assertEqual(sys.getrefcount(a), a_refcount + 1)

        del mview
        self.assertEqual(sys.getrefcount(a), a_refcount)

    def test_init_image_empty(self):
        a = Image2D(PixelFormat.R32F)
        a_refcount = sys.getrefcount(a)

        view = ImageView2D(a)
        self.assertEqual(view.size, (0, 0))
        self.assertIs(view.owner, None)
        self.assertEqual(sys.getrefcount(a), a_refcount)

        mview = MutableImageView2D(a)
        self.assertEqual(mview.size, (0, 0))
        self.assertIs(mview.owner, None)
        self.assertEqual(sys.getrefcount(a), a_refcount)

    def test_data_access(self):
        # 2x4 RGB pixels, padded for alignment
        data = (b'rgbRGB  '
                b'abcABC  '
                b'defDEF  '
                b'ijkIJK  ')
        data_refcount = sys.getrefcount(data)

        a = ImageView2D(PixelFormat.RGB8_UNORM, (2, 4), data)
        a_refcount = sys.getrefcount(a)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        a_data = a.data
        self.assertEqual(len(a_data), 32)
        self.assertEqual(a_data[9], 'b')
        self.assertEqual(a_data[20], 'E')
        self.assertIs(a_data.owner, data)
        # The data references the original data as an owner, not the view
        self.assertEqual(sys.getrefcount(a), a_refcount)
        self.assertEqual(sys.getrefcount(data), data_refcount + 2)

        del a_data
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

    def test_mutable_data_access(self):
        # 2x4 RGB pixels, padded for alignment
        data = bytearray(b'rgbRGB  '
                         b'abcABC  '
                         b'defDEF  '
                         b'ijkIJK  ')
        data_refcount = sys.getrefcount(data)

        a = MutableImageView2D(PixelFormat.RGB8_UNORM, (2, 4), data)
        a_refcount = sys.getrefcount(a)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        a_data = a.data
        self.assertEqual(len(a_data), 32)
        self.assertEqual(a_data[9], 'b')
        self.assertEqual(a_data[20], 'E')
        self.assertIs(a_data.owner, data)
        # The data references the original data as an owner, not the view
        self.assertEqual(sys.getrefcount(a), a_refcount)
        self.assertEqual(sys.getrefcount(data), data_refcount + 2)

        a_data[9] = '_'
        a_data[20] = '_'
        self.assertEqual(data, b'rgbRGB  '
                               b'a_cABC  '
                               b'defD_F  '
                               b'ijkIJK  ')

        del a_data
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

    def test_set_data(self):
        # 2x4 RGB pixels, padded for alignment
        data = (b'rgbRGB  '
                b'abcABC  '
                b'defDEF  '
                b'ijkIJK  ')
        data_refcount = sys.getrefcount(data)

        a = ImageView2D(PixelFormat.RGB8_UNORM, (2, 4), data)
        self.assertIs(a.owner, data)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        data2 = (b'ijkIJK  '
                 b'defDEF  '
                 b'abcABC  '
                 b'rgbRGB  ')
        data2_refcount = sys.getrefcount(data2)

        # Replacing the data should disown the original object and point to the
        # new one
        a.data = data2
        self.assertEqual(bytes(a.data), (
            b'ijkIJK  '
            b'defDEF  '
            b'abcABC  '
            b'rgbRGB  '))
        self.assertIs(a.owner, data2)
        self.assertEqual(sys.getrefcount(data), data_refcount)
        self.assertEqual(sys.getrefcount(data2), data2_refcount + 1)

    def test_pixels_access(self):
        # 2x4 RGB pixels, padded for alignment
        data = (b'rgbRGB  '
                b'abcABC  '
                b'defDEF  '
                b'ijkIJK  ')
        data_refcount = sys.getrefcount(data)

        a = ImageView2D(PixelFormat.RGB8UI, (2, 4), data)
        a_refcount = sys.getrefcount(a)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        pixels = a.pixels
        self.assertEqual(pixels.size, (4, 2))
        self.assertEqual(pixels.stride, (8, 3))
        self.assertEqual(pixels.format, '3B')
        self.assertEqual(pixels[1, 0].g, ord('b'))
        self.assertEqual(pixels[2, 1].g, ord('E'))
        self.assertIs(pixels.owner, data)
        # The data references the original data as an owner, not the view
        self.assertEqual(sys.getrefcount(a), a_refcount)
        self.assertEqual(sys.getrefcount(data), data_refcount + 2)

        del pixels
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

    def test_mutable_pixels_access(self):
        # 2x4 RGB pixels, padded for alignment
        data = bytearray(b'rgbRGB  '
                         b'abcABC  '
                         b'defDEF  '
                         b'ijkIJK  ')
        data_refcount = sys.getrefcount(data)

        a = MutableImageView2D(PixelFormat.RGB8UI, (2, 4), data)
        a_refcount = sys.getrefcount(a)
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

        pixels = a.pixels
        self.assertEqual(pixels.size, (4, 2))
        self.assertEqual(pixels.stride, (8, 3))
        self.assertEqual(pixels.format, '3B')
        self.assertEqual(pixels[1, 0].g, ord('b'))
        self.assertEqual(pixels[2, 1].g, ord('E'))
        self.assertIs(pixels.owner, data)
        # The data references the original data as an owner, not the view
        self.assertEqual(sys.getrefcount(a), a_refcount)
        self.assertEqual(sys.getrefcount(data), data_refcount + 2)

        pixels[1, 0] = Vector3(ord('a'), ord('_'), ord('c'))
        pixels[2, 1] = Vector3(ord('D'), ord('_'), ord('F'))
        self.assertEqual(data, b'rgbRGB  '
                               b'a_cABC  '
                               b'defD_F  '
                               b'ijkIJK  ')

        del pixels
        self.assertEqual(sys.getrefcount(data), data_refcount + 1)

    def test_pixels_access_direct(self):
        data = array.array('f', [1.0, 2.0, 3.0, 4.0])
        a = MutableImageView2D(PixelFormat.RG32F, (2, 1), data)

        pixels = a.pixels
        self.assertEqual(pixels.size, (1, 2))
        self.assertEqual(pixels.stride, (16, 8))
        self.assertEqual(pixels.format, '2f')
        self.assertEqual(pixels[0, 1], Vector2(3.0, 4.0))

        pixels[0, 1] *= 0.25
        self.assertEqual(pixels[0, 1], Vector2(0.75, 1.0))

    def test_pixels_access_cast(self):
        # 0.0, 1.0, 2.0, 3.0; values taken from Magnum's HalfTest.cpp
        # TODO clean up once array supports half-floats (ugh)
        data = array.array('H', [0x0000, 0x3c00, 0x4000, 0x4200])
        a = MutableImageView2D(PixelFormat.RG16F, (2, 1), data)

        pixels = a.pixels
        self.assertEqual(pixels.size, (1, 2))
        self.assertEqual(pixels.stride, (8, 4))
        self.assertEqual(pixels.format, '2e')
        self.assertEqual(pixels[0, 1], Vector2(2.0, 3.0))

        pixels[0, 1] *= 0.25
        self.assertEqual(pixels[0, 1], Vector2(0.5, 0.75))

    def test_pixels_access_srgb(self):
        # Values taken from Magnum's ColorTest::fromIntegralSrgb()
        data1 = array.array('B', [0xf3, 0x2a, 0x80, 0x23, 0xff, 0x00, 0xff, 0x00])
        data2 = array.array('B', [0xf3, 0x2a, 0x80, 0xff, 0x00, 0xff, 0, 0])
        data3 = array.array('B', [0xf3, 0x2a, 0xff, 0x00, 0, 0, 0, 0])
        data4 = array.array('B', [0xf3, 0xff, 0, 0, 0, 0, 0, 0])
        rgba = MutableImageView2D(PixelFormat.RGBA8_SRGB, (2, 1), data1)
        rgb = MutableImageView2D(PixelFormat.RGB8_SRGB, (2, 1), data2)
        rg = MutableImageView2D(PixelFormat.RG8_SRGB, (2, 1), data3)
        r = MutableImageView2D(PixelFormat.R8_SRGB, (2, 1), data4)

        rgba_pixels = rgba.pixels
        rgb_pixels = rgb.pixels
        rg_pixels = rg.pixels
        r_pixels = r.pixels
        self.assertEqual(rgba_pixels.format, '4B')
        self.assertEqual(rgb_pixels.format, '3B')
        self.assertEqual(rg_pixels.format, '2B')
        self.assertEqual(r_pixels.format, 'B')
        self.assertEqual(rgba_pixels[0, 0], Vector4(0.896269, 0.0231534, 0.215861, 0.137255))
        self.assertEqual(rgb_pixels[0, 0], Vector3(0.896269, 0.0231534, 0.215861))
        self.assertEqual(rg_pixels[0, 0], Vector2(0.896269, 0.0231534))
        # Python compares floats with an unnecessary precision compared to
        # Magnum's op== on vector types
        self.assertEqual(r_pixels[0, 0], 0.8962693810462952)
        self.assertEqual(rgba_pixels[0, 1], Vector4(1.0, 0.0, 1.0, 0.0))
        self.assertEqual(rgb_pixels[0, 1], Vector3(1.0, 0.0, 1.0))
        self.assertEqual(rg_pixels[0, 1], Vector2(1.0, 0.0))
        self.assertEqual(r_pixels[0, 1], 1.0)

        rgba_pixels[0, 0] *= 0.5
        rgb_pixels[0, 0] *= 0.5
        rg_pixels[0, 0] *= 0.5
        r_pixels[0, 0] *= 0.5
        self.assertEqual(rgba_pixels[0, 0], Vector4(0.450786, 0.0116122, 0.107023, 0.0705882))
        self.assertEqual(rgb_pixels[0, 0], Vector3(0.450786, 0.0116122, 0.107023))
        self.assertEqual(rg_pixels[0, 0], Vector2(0.450786, 0.0116122))
        # Python compares floats with an unnecessary precision compared to
        # Magnum's op== on vector types
        self.assertEqual(r_pixels[0, 0], 0.4507858455181122)

    def test_pixels_access_unsupported_format(self):
        data = array.array('f', [1.0, 2.0, 3.0, 4.0])
        a = ImageView2D(PixelFormat.DEPTH32F, (2, 2), data)

        with self.assertRaisesRegex(NotImplementedError, "access to this pixel format is not implemented yet, sorry"):
            a.pixels
