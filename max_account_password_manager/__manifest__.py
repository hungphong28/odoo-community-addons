# -*- coding: utf-8 -*-
{
    "name": "Quản lý mật khẩu",
    "summary": "Quản lý mật khẩu người dùng được tạo, lưu trữ và nhật ký truy cập mật khẩu",
    "version": "19.0.1.0.0",
    "category": "Administration",
    "author": "hungphong28",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/account_password_record_views.xml",
        "views/account_password_log_views.xml",
        "views/account_password_set_wizard_views.xml",
        "views/res_users_views.xml",
        "views/menus.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "max_account_password_manager/static/src/js/password_clipboard.js"
        ]
    },
    "installable": True,
    "application": False,
}
