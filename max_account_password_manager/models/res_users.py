# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    managed_password_record_id = fields.Many2one(
        "max.account.password.record",
        string="Bản ghi mật khẩu quản lý",
        compute="_compute_managed_password_record",
    )
    managed_password_record_count = fields.Integer(
        string="Mật khẩu",
        compute="_compute_managed_password_record",
    )

    def _compute_managed_password_record(self):
        records = self.env["max.account.password.record"].sudo().search([
            ("user_id", "in", self.ids),
        ])
        mapped = {record.user_id.id: record for record in records}
        for user in self:
            record = mapped.get(user.id)
            user.managed_password_record_id = record
            user.managed_password_record_count = 1 if record else 0

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        for user, vals in zip(users, vals_list):
            password = vals.get("password")
            if password:
                user._capture_password_to_manager(
                    password=password,
                    source="outside",
                    note="Mật khẩu được tự động ghi nhận khi tạo tài khoản.",
                )
        return users

    def write(self, vals):
        password = vals.get("password")
        manager_context = self.env.context.get("from_account_password_manager")

        result = super().write(vals)

        if password and not manager_context:
            self._capture_password_to_manager(
                password=password,
                source="outside",
                note="Mật khẩu được tự động ghi nhận khi thay đổi ngoài trình quản lý mật khẩu.",
            )
        return result

    def _capture_password_to_manager(self, password, source="outside", note=None):
        if not password:
            return

        PasswordRecord = self.env["max.account.password.record"].sudo()
        PasswordLog = self.env["max.account.password.log"].sudo()
        now = fields.Datetime.now()

        for user in self:
            record = PasswordRecord.search([("user_id", "=", user.id)], limit=1)
            old_state = record.state if record else False
            values = {
                "password_value": password,
                "password_last_set_date": now,
                "password_set_by_id": self.env.user.id,
                "source": source,
                "state": "managed",
                "note": note or "",
            }

            if record:
                record.write(values)
            else:
                values["user_id"] = user.id
                record = PasswordRecord.create(values)

            PasswordLog.create_log(
                user=user,
                action="capture_password",
                old_state=old_state,
                new_state=record.state,
                note=note or "Mật khẩu được tự động ghi nhận.",
                record=record,
            )

    def action_open_password_set_wizard(self):
        self.ensure_one()
        return {
            "name": "Đặt mật khẩu",
            "type": "ir.actions.act_window",
            "res_model": "max.account.password.set.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_user_id": self.id,
            },
        }


    def action_open_managed_password_record(self):
        self.ensure_one()
        action = self.env.ref("max_account_password_manager.action_max_account_password_record").sudo().read()[0]
        action["domain"] = [("user_id", "=", self.id)]
        action["context"] = {
            "default_user_id": self.id,
        }

        if self.managed_password_record_id:
            action["views"] = [(False, "form")]
            action["res_id"] = self.managed_password_record_id.id

        return action
