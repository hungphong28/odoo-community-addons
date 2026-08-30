# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models


class AccountPasswordRecord(models.Model):
    _name = "max.account.password.record"
    _description = "Bản ghi mật khẩu tài khoản được quản lý"
    _order = "password_last_set_date desc, id desc"

    name = fields.Char(
        string="Mã",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Người dùng",
        required=True,
        ondelete="cascade",
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
    password_value = fields.Char(
        string="Mật khẩu",
        copy=False,
        readonly=True,
    )
    password_masked = fields.Char(
        string="Mật khẩu",
        compute="_compute_password_masked",
    )
    password_last_set_date = fields.Datetime(
        string="Ngày đặt gần nhất",
        readonly=True,
    )
    password_set_by_id = fields.Many2one(
        "res.users",
        string="Người đặt gần nhất",
        readonly=True,
    )
    source = fields.Selection(
        [
            ("manual", "Thủ công"),
            ("generated", "Tự sinh"),
            ("outside", "Ngoài trình quản lý"),
        ],
        string="Nguồn",
        default="manual",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("managed", "Đang quản lý"),
            ("out_of_sync", "Không đồng bộ"),
        ],
        string="Trạng thái",
        default="managed",
        required=True,
        index=True,
    )
    note = fields.Text(string="Ghi chú")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self._get_next_unique_name()
        return super().create(vals_list)

    def _get_next_unique_name(self):
        sequence_code = "max.account.password.record"
        self._sync_sequence_after_existing_names(sequence_code)

        for _attempt in range(100):
            name = self.env["ir.sequence"].next_by_code(sequence_code) or "New"
            if name == "New" or not self.search_count([("name", "=", name)]):
                return name

        return self.env["ir.sequence"].next_by_code(sequence_code) or "New"

    def _sync_sequence_after_existing_names(self, sequence_code):
        sequence = self.env["ir.sequence"].sudo().search([("code", "=", sequence_code)], limit=1)
        if not sequence:
            return

        max_number = 0
        for record in self.sudo().search([("name", "=like", "PM%")]):
            match = re.match(r"PM(\d+)$", record.name or "")
            if match:
                max_number = max(max_number, int(match.group(1)))

        if sequence.number_next_actual <= max_number:
            sequence.number_next_actual = max_number + 1

    def _compute_password_masked(self):
        for record in self:
            record.password_masked = "•" * len(record.password_value or "") if record.password_value else ""


    def action_copy_password(self):
        self.ensure_one()
        self.env["max.account.password.log"].create_log(
            user=self.user_id,
            action="copy_password",
            old_state=self.state,
            new_state=self.state,
            note="Đã sao chép mật khẩu từ trình quản lý mật khẩu.",
            record=self,
        )
        return {
            "type": "ir.actions.client",
            "tag": "max_account_password_manager.copy_password",
            "params": {
                "password": self.password_value or "",
            },
        }
