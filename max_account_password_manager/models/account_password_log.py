# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPasswordLog(models.Model):
    _name = "max.account.password.log"
    _description = "Nhật ký truy cập mật khẩu tài khoản"
    _order = "performed_date desc, id desc"

    record_id = fields.Many2one(
        "max.account.password.record",
        string="Bản ghi mật khẩu",
        ondelete="set null",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Người dùng được tác động",
        ondelete="set null",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Liên hệ",
        related="user_id.partner_id",
        store=True,
        readonly=True,
    )
    login = fields.Char(
        string="Tài khoản đăng nhập",
        related="user_id.login",
        store=True,
        readonly=True,
    )
    action = fields.Selection(
        [
            ("set_password", "Đặt mật khẩu"),
            ("generate_password", "Tạo mật khẩu"),
            ("view_password", "Xem mật khẩu"),
            ("copy_password", "Sao chép mật khẩu"),
            ("capture_password", "Tự động ghi nhận mật khẩu"),
            ("password_changed_outside_manager", "Mật khẩu đổi ngoài trình quản lý"),
            ("enable_management", "Bật quản lý"),
        ],
        string="Hành động",
        required=True,
        index=True,
    )
    performed_by_id = fields.Many2one(
        "res.users",
        string="Người thực hiện",
        default=lambda self: self.env.user,
        readonly=True,
    )
    performed_date = fields.Datetime(
        string="Thời gian thực hiện",
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    old_state = fields.Char(string="Trạng thái cũ", readonly=True)
    new_state = fields.Char(string="Trạng thái mới", readonly=True)
    note = fields.Text(string="Ghi chú", readonly=True)

    @api.model
    def create_log(self, user, action, old_state=False, new_state=False, note=False, record=False):
        return self.create({
            "record_id": record.id if record else False,
            "user_id": user.id if user else False,
            "action": action,
            "old_state": old_state or False,
            "new_state": new_state or False,
            "note": note or False,
        })
