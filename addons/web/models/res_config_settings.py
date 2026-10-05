# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    web_app_name = fields.Char('Web App Name', config_parameter='web.web_app_name')

    login_hero_title = fields.Char(
        'Tiêu đề Hero Đăng nhập',
        config_parameter='insilos.login_hero_title',
        default='Trung Tâm Chỉ Huy & Bản Sao Số Doanh Nghiệp',
    )
    login_hero_subtitle = fields.Char(
        'Phụ đề Hero Đăng nhập',
        config_parameter='insilos.login_hero_subtitle',
        default='Bản sao số công nghiệp 3D kết nối thời gian thực với lõi điều hành sản xuất MES, chuỗi cung ứng logistics đa cảng và hệ thống tài chính kế toán chủ quyền.',
    )
    login_hero_3d_mode = fields.Selection([
        ('digital_twin', '3D Digital Twin Equipment (V-LIFT 2500E)'),
        ('logistics_radar', '3D Logistics Radar & Route Map'),
        ('cyber_mesh', '3D Cybernetic Mesh Topology'),
    ], string='Chế độ 3D Interactive Hero', config_parameter='insilos.login_hero_3d_mode', default='digital_twin')
    login_hero_show_3d = fields.Boolean(
        'Kích hoạt 3D Interactive Snippet',
        config_parameter='insilos.login_hero_show_3d',
        default=True,
    )
