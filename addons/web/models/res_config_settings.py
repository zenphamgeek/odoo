# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    web_app_name = fields.Char('Web App Name', config_parameter='web.web_app_name')

    login_hero_title = fields.Char(
        'Tiêu đề Hero Đăng nhập',
        config_parameter='insilos.login_hero_title',
        default='Xóa Bỏ Ốc Đảo Dữ Liệu • Hợp Nhất Doanh Nghiệp',
    )
    login_hero_subtitle = fields.Char(
        'Phụ đề Hero Đăng nhập',
        config_parameter='insilos.login_hero_subtitle',
        default='Biểu tượng 3 trụ cột Silo liên kết biểu trưng cho sự giải phóng và đồng bộ hóa tức thời giữa Sản Xuất (MES), Chuỗi Cung Ứng (SCM) và Quản Trị Tài Chính Chủ Quyền (FI/CO).',
    )
    login_hero_3d_mode = fields.Selection([
        ('insilos_icon', 'Biểu tượng 3D Insilos Icon (3 Silos & Data Bridge)'),
        ('digital_twin', '3D Digital Twin Equipment (V-LIFT 2500E)'),
        ('cyber_mesh', '3D Cybernetic Mesh Topology'),
    ], string='Chế độ 3D Interactive Hero', config_parameter='insilos.login_hero_3d_mode', default='insilos_icon')
    login_hero_show_3d = fields.Boolean(
        'Kích hoạt 3D Interactive Snippet',
        config_parameter='insilos.login_hero_show_3d',
        default=True,
    )
