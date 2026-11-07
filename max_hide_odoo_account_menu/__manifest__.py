{
    "name": "MAX Hide Odoo.com Account Menu",
    "version": "19.0.1.0.1",
    "summary": "Hide the My Odoo.com Account entry from the user menu",
    "category": "Tools",
    "author": "MAX Solution",
    "license": "LGPL-3",
    "depends": [
        "web",
    ],
    "assets": {
        "web.assets_backend": [
            "max_hide_odoo_account_menu/static/src/js/user_menu.js",
        ],
    },
    "installable": True,
    "application": False,
}
