# -*- coding: utf-8 -*-
"""
GeoStudio - 3D OpenGL Point Cloud Canvas
High-performance OpenGL viewport for orbit, pan, pitch, and zoom point rendering.
"""

import numpy as np
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *


class GLPointCloudCanvas(QOpenGLWidget):
    """High-performance OpenGL 3D Viewport with Orbit, Pan, Pitch, Tilt, and Zoom."""

    camera_changed = pyqtSignal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pts_xyz = None
        self.current_colors = None
        self.rgb_colors = None
        self.z_colors = None
        self.class_colors = None
        self.intensity_colors = None

        self.rot_x = 45.0
        self.rot_z = -30.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.zoom_dist = 300.0
        self.z_exaggeration = 1.5
        self.point_size = 3.5
        self.show_grid = True
        self.show_bbox = True
        self.bg_color = (0.0, 0.0, 0.0, 1.0)

        self._last_pos = QPoint()

    def set_point_data(self, pts_xyz, rgb_colors, z_colors, class_colors, intensity_colors, mode="auto"):
        self.pts_xyz = pts_xyz
        self.rgb_colors = rgb_colors
        self.z_colors = z_colors
        self.class_colors = class_colors
        self.intensity_colors = intensity_colors

        if mode == "auto":
            if rgb_colors is not None and not np.all(rgb_colors == 0):
                self.current_colors = rgb_colors
            else:
                self.current_colors = z_colors
        elif mode == "rgb" and rgb_colors is not None:
            self.current_colors = rgb_colors
        elif mode == "class" and class_colors is not None:
            self.current_colors = class_colors
        elif mode == "intensity" and intensity_colors is not None:
            self.current_colors = intensity_colors
        else:
            self.current_colors = z_colors

        if pts_xyz is not None and len(pts_xyz) > 0:
            max_extent = float(np.max(np.abs(pts_xyz)))
            self.zoom_dist = max(50.0, max_extent * 2.2)
            self.pan_x = 0.0
            self.pan_y = 0.0

        self.update()

    def set_color_mode(self, mode_str: str):
        if mode_str == "RGB" and self.rgb_colors is not None:
            self.current_colors = self.rgb_colors
        elif mode_str == "Elevation":
            self.current_colors = self.z_colors
        elif mode_str == "Classification" and self.class_colors is not None:
            self.current_colors = self.class_colors
        elif mode_str == "Intensity" and self.intensity_colors is not None:
            self.current_colors = self.intensity_colors
        else:
            self.current_colors = self.z_colors
        self.update()

    def set_point_size(self, size: float):
        self.point_size = size
        self.update()

    def set_z_exaggeration(self, exag: float):
        self.z_exaggeration = exag
        self.update()

    def set_background_theme(self, theme: str):
        if theme == "Dark Slate":
            self.bg_color = (0.06, 0.09, 0.16, 1.0)
        elif theme == "Studio Gray":
            self.bg_color = (0.12, 0.15, 0.20, 1.0)
        elif theme == "Sky Blue":
            self.bg_color = (0.53, 0.75, 0.92, 1.0)
        else:
            self.bg_color = (0.97, 0.98, 0.99, 1.0)
        self.update()

    def reset_view(self):
        self.rot_x = 45.0
        self.rot_z = -30.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        if self.pts_xyz is not None and len(self.pts_xyz) > 0:
            max_extent = float(np.max(np.abs(self.pts_xyz)))
            self.zoom_dist = max(50.0, max_extent * 2.2)
        self.update()

    def set_top_view(self):
        self.rot_x = 0.0
        self.rot_z = 0.0
        self.update()

    def set_isometric_view(self):
        self.rot_x = 54.735
        self.rot_z = -45.0
        self.update()

    # ── OpenGL Pipeline ─────────────────────────────────────────
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(*self.bg_color)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, max(1, h))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / max(1.0, float(h)), 1.0, 500000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClearColor(*self.bg_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(self.pan_x, self.pan_y, -self.zoom_dist)
        glRotatef(self.rot_x, 1.0, 0.0, 0.0)
        glRotatef(self.rot_z, 0.0, 0.0, 1.0)

        if self.show_grid:
            self._draw_grid()

        if self.pts_xyz is not None and len(self.pts_xyz) > 0:
            glPointSize(float(self.point_size))

            glPushMatrix()
            glScalef(1.0, 1.0, float(self.z_exaggeration))

            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)

            glVertexPointer(3, GL_FLOAT, 0, self.pts_xyz)

            if self.current_colors is not None and len(self.current_colors) == len(self.pts_xyz):
                glColorPointer(3, GL_FLOAT, 0, self.current_colors)
            else:
                glColorPointer(3, GL_FLOAT, 0, self.z_colors)

            glDrawArrays(GL_POINTS, 0, len(self.pts_xyz))

            glDisableClientState(GL_COLOR_ARRAY)
            glDisableClientState(GL_VERTEX_ARRAY)

            if self.show_bbox:
                self._draw_bounding_box()

            glPopMatrix()

    def _draw_grid(self):
        glLineWidth(1.0)
        glColor4f(0.3, 0.4, 0.5, 0.25)
        grid_size = 250.0
        step = 25.0

        glBegin(GL_LINES)
        x = -grid_size
        while x <= grid_size:
            glVertex3f(x, -grid_size, 0.0)
            glVertex3f(x, grid_size, 0.0)
            glVertex3f(-grid_size, x, 0.0)
            glVertex3f(grid_size, x, 0.0)
            x += step
        glEnd()

        # Center Axes (X=Red, Y=Green, Z=Blue)
        glLineWidth(2.5)
        glBegin(GL_LINES)
        glColor3f(0.9, 0.2, 0.2); glVertex3f(0, 0, 0); glVertex3f(40, 0, 0)
        glColor3f(0.2, 0.8, 0.2); glVertex3f(0, 0, 0); glVertex3f(0, 40, 0)
        glColor3f(0.2, 0.5, 0.9); glVertex3f(0, 0, 0); glVertex3f(0, 0, 40)
        glEnd()

    def _draw_bounding_box(self):
        if self.pts_xyz is None or len(self.pts_xyz) == 0:
            return
        min_v = np.min(self.pts_xyz, axis=0)
        max_v = np.max(self.pts_xyz, axis=0)

        glColor4f(0.4, 0.6, 0.8, 0.35)
        glLineWidth(1.2)

        x0, y0, z0 = min_v
        x1, y1, z1 = max_v

        glBegin(GL_LINE_LOOP); glVertex3f(x0, y0, z0); glVertex3f(x1, y0, z0); glVertex3f(x1, y1, z0); glVertex3f(x0, y1, z0); glEnd()
        glBegin(GL_LINE_LOOP); glVertex3f(x0, y0, z1); glVertex3f(x1, y0, z1); glVertex3f(x1, y1, z1); glVertex3f(x0, y1, z1); glEnd()
        glBegin(GL_LINES)
        glVertex3f(x0, y0, z0); glVertex3f(x0, y0, z1)
        glVertex3f(x1, y0, z0); glVertex3f(x1, y0, z1)
        glVertex3f(x1, y1, z0); glVertex3f(x1, y1, z1)
        glVertex3f(x0, y1, z0); glVertex3f(x0, y1, z1)
        glEnd()

    # ── Interactive Mouse Navigation ────────────────────────────
    def mousePressEvent(self, event):
        self._last_pos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self._last_pos.x()
        dy = event.y() - self._last_pos.y()

        if event.buttons() & Qt.LeftButton:
            self.rot_x = max(-89.0, min(89.0, self.rot_x + dy * 0.4))
            self.rot_z += dx * 0.4
            self.update()

        elif (event.buttons() & Qt.MidButton) or ((event.buttons() & Qt.LeftButton) and (event.modifiers() & Qt.ShiftModifier)):
            factor = self.zoom_dist * 0.0015
            self.pan_x += dx * factor
            self.pan_y -= dy * factor
            self.update()

        elif event.buttons() & Qt.RightButton:
            self.zoom_dist = max(5.0, self.zoom_dist - dy * (self.zoom_dist * 0.008))
            self.update()

        self._last_pos = event.pos()

    def wheelEvent(self, event):
        num_degrees = event.angleDelta().y() / 8.0
        num_steps = num_degrees / 15.0
        zoom_factor = 1.15 ** (-num_steps)
        self.zoom_dist = max(2.0, self.zoom_dist * zoom_factor)
        self.update()
