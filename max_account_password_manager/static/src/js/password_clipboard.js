/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("actions").add("max_account_password_manager.copy_password", async (env, action) => {
    const password = action.params && action.params.password ? action.params.password : "";

    if (!password) {
        env.services.notification.add("Không có mật khẩu để sao chép.", {
            type: "warning",
        });
        return;
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(password);
    } else {
        const textarea = document.createElement("textarea");
        textarea.value = password;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
    }

    env.services.notification.add("Đã sao chép mật khẩu vào clipboard.", {
        type: "success",
    });
});
