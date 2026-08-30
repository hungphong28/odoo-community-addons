# -*- coding: utf-8 -*-

import secrets
import string

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountPasswordSetWizard(models.TransientModel):
    _name = "max.account.password.set.wizard"
    _description = "Đặt mật khẩu tài khoản được quản lý"

    user_id = fields.Many2one(
        "res.users",
        string="Người dùng",
        required=True,
        readonly=True,
    )
    password = fields.Char(
        string="Mật khẩu",
    )
    confirm_password = fields.Char(
        string="Xác nhận mật khẩu",
    )
    password_was_generated = fields.Boolean(
        string="Mật khẩu được tự sinh",
        default=True,
    )
    password_length = fields.Integer(
        string="Độ dài mật khẩu",
        default=12,
    )
    password_strength = fields.Selection(
        [
            ("empty", "Chưa có mật khẩu"),
            ("weak", "Yếu"),
            ("medium", "Trung bình"),
            ("strong", "Mạnh"),
            ("very_strong", "Rất mạnh"),
        ],
        string="Cường độ mật khẩu",
        compute="_compute_password_strength",
    )
    password_strength_note = fields.Char(
        string="Gợi ý",
        compute="_compute_password_strength",
    )
    note = fields.Text(string="Ghi chú")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        password = self._generate_password(
            length=values.get("password_length") or 12,
        )
        values["password"] = password
        values["confirm_password"] = password
        values["password_was_generated"] = True
        return values

    def _generate_password(self, length=12):
        if length < 8:
            raise UserError("Độ dài mật khẩu phải có ít nhất 8 ký tự.")

        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        numbers = string.digits
        special = "!@#$%^&*()-_=+[]{};:,.?"

        groups = [uppercase, lowercase, numbers, special]
        if length < len(groups):
            raise UserError("Độ dài mật khẩu quá ngắn để tạo mật khẩu mạnh.")

        password_chars = [secrets.choice(group) for group in groups]
        all_chars = "".join(groups)
        password_chars.extend(secrets.choice(all_chars) for _index in range(length - len(password_chars)))
        secrets.SystemRandom().shuffle(password_chars)
        return "".join(password_chars)

    @api.depends("password")
    def _compute_password_strength(self):
        for wizard in self:
            strength, note = wizard._evaluate_password_strength(wizard.password or "")
            wizard.password_strength = strength
            wizard.password_strength_note = note

    def _evaluate_password_strength(self, password):
        if not password:
            return "empty", "Chưa có mật khẩu."

        length = len(password)
        has_lowercase = any(char.islower() for char in password)
        has_uppercase = any(char.isupper() for char in password)
        has_number = any(char.isdigit() for char in password)
        has_special = any(not char.isalnum() for char in password)

        score = 0
        if length >= 8:
            score += 1
        if length >= 12:
            score += 1
        if length >= 16:
            score += 1
        score += sum([has_lowercase, has_uppercase, has_number, has_special])

        suggestions = []
        if length < 8:
            suggestions.append("dùng ít nhất 8 ký tự")
        if length < 12:
            suggestions.append("nên dùng từ 12 ký tự trở lên")
        if not has_lowercase:
            suggestions.append("thêm chữ thường")
        if not has_uppercase:
            suggestions.append("thêm chữ hoa")
        if not has_number:
            suggestions.append("thêm chữ số")
        if not has_special:
            suggestions.append("thêm ký tự đặc biệt")

        if score <= 2:
            return "weak", "Mật khẩu yếu. Gợi ý: " + ", ".join(suggestions) + "."
        if score <= 4:
            return "medium", "Mật khẩu trung bình. Gợi ý: " + ", ".join(suggestions) + "."
        if score <= 5:
            return "strong", "Mật khẩu mạnh."
        return "very_strong", "Mật khẩu rất mạnh."

    def action_generate_password(self):
        self.ensure_one()
        password = self._generate_password(
            length=self.password_length,
        )
        self.password = password
        self.confirm_password = password
        self.password_was_generated = True
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_set_password(self):
        self.ensure_one()
        if not self.password:
            raise UserError("Vui lòng nhập hoặc tạo mật khẩu.")
        if not self.confirm_password:
            raise UserError("Vui lòng xác nhận mật khẩu.")
        if self.password != self.confirm_password:
            raise UserError("Mật khẩu xác nhận không khớp.")

        old_record = self.env["max.account.password.record"].sudo().search([
            ("user_id", "=", self.user_id.id),
        ], limit=1)
        old_state = old_record.state if old_record else False

        self.user_id.with_context(from_account_password_manager=True).write({
            "password": self.password,
        })

        values = {
            "user_id": self.user_id.id,
            "password_value": self.password,
            "password_last_set_date": fields.Datetime.now(),
            "password_set_by_id": self.env.user.id,
            "source": "generated" if self.password_was_generated else "manual",
            "state": "managed",
            "note": self.note,
        }

        if old_record:
            old_record.sudo().write(values)
            record = old_record
        else:
            record = self.env["max.account.password.record"].sudo().create(values)

        self.env["max.account.password.log"].sudo().create_log(
            user=self.user_id,
            action="set_password",
            old_state=old_state,
            new_state="managed",
            note=self.note or "Mật khẩu quản lý đã được đặt.",
            record=record,
        )

        return {"type": "ir.actions.act_window_close"}
