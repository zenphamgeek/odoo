# Part of Insilos. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
import hashlib
import os
from os.path import join as opj
import re

from insilos import api, fields, models
from insilos.http import request
from insilos.tools import BinaryBytes, file_open

MENU_ITEM_SEPARATOR = "/"
NUMBER_PARENS = re.compile(r"\(([0-9]+)\)")


class IrUiMenu(models.Model):
    _name = 'ir.ui.menu'
    _description = 'Menu'
    _order = "sequence,id"
    _parent_store = True
    _allow_sudo_commands = False
    _clear_cache_name = 'default'

    name = fields.Char(string='Menu', required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    child_id = fields.One2many('ir.ui.menu', 'parent_id', string='Child IDs')
    parent_id = fields.Many2one('ir.ui.menu', string='Parent Menu', index=True, ondelete="restrict")
    parent_path = fields.Char(index=True)
    group_ids = fields.Many2many('res.groups', 'ir_ui_menu_group_rel',
                                 'menu_id', 'gid', string='Groups',
                                 help="If you have groups, the visibility of this menu will be based on these groups. "\
                                      "If this field is empty, Insilos will compute visibility based on the related object's read access.")
    complete_name = fields.Char(string='Full Path', compute='_compute_complete_name', recursive=True)
    web_icon = fields.Char(string='Web Icon File')
    action = fields.Reference(selection=[('ir.actions.report', 'ir.actions.report'),
                                         ('ir.actions.act_window', 'ir.actions.act_window'),
                                         ('ir.actions.act_url', 'ir.actions.act_url'),
                                         ('ir.actions.server', 'ir.actions.server'),
                                         ('ir.actions.client', 'ir.actions.client')])

    web_icon_data = fields.Binary(string='Web Icon Image', attachment=True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for menu in self:
            menu.complete_name = menu._get_full_name()

    def _get_full_name(self, level=6):
        """ Return the full name of ``self`` (up to a certain level). """
        if level <= 0:
            return '...'
        if self.parent_id:
            return (self.parent_id._get_full_name(level - 1) or "") + MENU_ITEM_SEPARATOR + (self.name or "")
        else:
            return self.name

    def _generate_dynamic_app_icon(self, identifier):
        """Generate a dynamic Horizon-Carbon squircle tile SVG with initial letter."""
        raw_name = (identifier or 'App').split(',')[0].replace('_', ' ').strip()
        initial = (raw_name[:1] or 'A').upper()
        h = sum(ord(c) for c in raw_name)
        palette = [
            '#0F62FE',  # Carbon Blue (Sales / SD)
            '#007D79',  # Teal (Supply Chain / MM)
            '#8A3FFC',  # Purple (Finance / FI/CO)
            '#BA4E00',  # Warm Bronze / Amber (Manufacturing / PP)
            '#198038',  # Green (HCM / Sustainability)
            '#0072C3',  # Blue Cyan (Collaboration / Portals)
            '#6929C4',  # Deep Violet (Projects / PS)
            '#0B2E64',  # Insilos Horizon Dark Navy
        ]
        color = palette[h % len(palette)]
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">\n'
            f'  <rect x="12" y="12" width="232" height="232" rx="48" ry="48" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2"/>\n'
            f'  <rect x="44" y="44" width="168" height="168" rx="36" ry="36" fill="{color}" opacity="0.12"/>\n'
            f'  <text x="128" y="162" font-family="system-ui, -apple-system, sans-serif" font-size="96" font-weight="700" fill="{color}" text-anchor="middle">{initial}</text>\n'
            f'</svg>'
        )
        return BinaryBytes(svg.encode('utf-8'))

    def _read_image(self, path):
        if not path:
            return False
        path_info = path.split(',')
        if len(path_info) != 2:
            return self._generate_dynamic_app_icon(path)
        module, rel_path = path_info[0].strip(), path_info[1].strip()
        icon_path = opj(module, rel_path)
        try:
            with file_open(icon_path, 'rb', filter_ext=('.png', '.gif', '.ico', '.jfif', '.jpeg', '.jpg', '.svg', '.webp')) as f:
                data = f.read()
                if data:
                    return BinaryBytes(data)
        except Exception:
            pass

        # Try companion extension (.png <-> .svg)
        alt_rel_path = None
        if rel_path.endswith('.png'):
            alt_rel_path = rel_path[:-4] + '.svg'
        elif rel_path.endswith('.svg'):
            alt_rel_path = rel_path[:-4] + '.png'
        if alt_rel_path:
            try:
                with file_open(opj(module, alt_rel_path), 'rb', filter_ext=('.png', '.gif', '.ico', '.jfif', '.jpeg', '.jpg', '.svg', '.webp')) as f:
                    data = f.read()
                    if data:
                        return BinaryBytes(data)
            except Exception:
                pass

        # Dynamic initial-letter SVG tile generation fallback for unknown module without icon asset
        return self._generate_dynamic_app_icon(module)

    @api.model
    @api.ormcache('frozenset(self.env.user._get_group_ids())', 'debug')
    def _visible_menu_ids(self, debug=False):
        """ Return the ids of the menu items visible to the user. """
        group_ids = set(self.env.user._get_group_ids())
        if not debug:
            group_ids.discard(self.env['ir.model.data']._xmlid_to_res_id('base.group_no_one', raise_if_not_found=False))

        # retrieve menus with a domain to filter out menus with groups the user does not have.
        # It will be used to determine which ones are visible
        menus = self.with_context({}).search_fetch(
            # Don't use 'any' operator in the domain to avoid ir.rule
            ['|', ('group_ids', '=', False), ('group_ids', 'in', tuple(group_ids))],
            ['parent_id', 'action'], order='id',
        ).sudo()

        # take apart menus that have an action
        action_ids_by_model = defaultdict(list)
        for action in menus.mapped('action'):
            if action:
                action_ids_by_model[action._name].append(action.id)

        MODEL_BY_TYPE = {
            'ir.actions.act_window': 'res_model',
            'ir.actions.report': 'model',
            'ir.actions.server': 'model_name',
        }
        def exists_actions(model_name, action_ids):
            """ Return existing actions and fetch model name field if exists"""
            if model_name not in MODEL_BY_TYPE:
                return self.env[model_name].browse(action_ids).exists()
            records = self.env[model_name].sudo().with_context(active_test=False).search_fetch(
                [('id', 'in', action_ids)], [MODEL_BY_TYPE[model_name]], order='id',
            )
            if model_name == 'ir.actions.server':
                # Because it is computed, `search_fetch` doesn't fill the cache for it
                records.mapped('model_name')
            return records

        existing_actions = {
            action
            for model_name, action_ids in action_ids_by_model.items()
            for action in exists_actions(model_name, action_ids)
        }
        menu_ids = set(menus._ids)
        visible_ids = set()
        # process action menus, check whether their action is allowed
        for menu in menus:
            action = menu.action
            if not action or action not in existing_actions:
                continue
            model_fname = MODEL_BY_TYPE.get(action._name)
            # action[model_fname] has been fetched in batch in `exists_actions`
            if model_fname and not ((model := self.env.get(action[model_fname])) is not None and model.has_access('read')):
                continue
            # make menu visible, and its folder ancestors, too
            menu_id = menu.id
            while menu_id not in visible_ids and menu_id in menu_ids:
                visible_ids.add(menu_id)
                menu = menu.parent_id
                menu_id =  menu.id

        return frozenset(visible_ids)

    def _filter_visible_menus(self):
        """ Filter `self` to only keep the menu items that should be visible in
            the menu hierarchy of the current user.
            Uses a cache for speeding up the computation.
        """
        visible_ids = self._visible_menu_ids(request.session.debug if request else False)
        return self.filtered(lambda menu: menu.id in visible_ids)

    @api.depends('parent_id')
    def _compute_display_name(self):
        for menu in self:
            menu.display_name = menu._get_full_name()

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'web_icon' in values:
                values['web_icon_data'] = self._compute_web_icon_data(values.get('web_icon'))
        return super().create(vals_list)

    def write(self, vals):
        if 'web_icon' in vals:
            vals['web_icon_data'] = self._compute_web_icon_data(vals.get('web_icon'))
        return super().write(vals)

    def _compute_web_icon_data(self, web_icon):
        """ Returns the image associated to ``web_icon``.

        :param str web_icon: a comma-separated value string for either:

          * an image icon: ``f"{module},{path}"``
          * a built icon: ``f"{icon_class},{icon_color},{background_color}"``

        The ``web_icon_data`` computed field uses :meth:`_read_image` for image
        web icons, and is ``False`` for built icons.
        """
        if web_icon and len(web_icon.split(',')) == 2:
            return self._read_image(web_icon)
        return False

    def _register_hook(self):
        """Self-healing: reconcile root-menu icons with the files shipped on disk.

        ``web_icon_data`` is a snapshot taken at XML-load time. Whenever a DB is
        created/upgraded from an image whose icons changed (or the snapshot was
        lost), the webclient silently falls back to the default cube. Running this
        idempotent reconciliation on every registry load makes that impossible.
        """
        super()._register_hook()
        try:
            self._insilos_sync_icons()
        except Exception:  # noqa: BLE001 - never block a registry load on icons
            import logging
            logging.getLogger(__name__).warning("Insilos icon reconciliation skipped", exc_info=True)

    @api.model
    def _insilos_sync_icons(self):
        """Create/refresh ``web_icon_data`` of root menus whose snapshot is missing, stale, or lost on disk.

        :return: number of menus repaired
        """
        menus = self.sudo().with_context(active_test=False).search([
            ('parent_id', '=', False),
        ])
        if not menus:
            return 0

        # Query attachment metadata including filestore path and database storage flag
        self.env.cr.execute("""
            SELECT res_id, checksum, store_fname, (db_datas IS NOT NULL) AS has_db
              FROM ir_attachment
             WHERE res_model = 'ir.ui.menu' AND res_field = 'web_icon_data' AND res_id IN %s
        """, [tuple(menus.ids)])
        current = {
            row[0]: {'checksum': row[1], 'store_fname': row[2], 'has_db': row[3]}
            for row in self.env.cr.fetchall()
        }

        repaired = 0
        Attachment = self.env['ir.attachment'].sudo()
        for menu in menus:
            data = None
            if menu.web_icon and len(menu.web_icon.split(',')) == 2:
                data = self._read_image(menu.web_icon)
            if not data:
                data = (
                    self._read_image('base,static/description/icon.svg') or
                    self._read_image('base,static/description/icon.png') or
                    self._generate_dynamic_app_icon(menu.name or 'Insilos')
                )
            if not data:
                continue

            raw = bytes(data)
            expected_sha1 = hashlib.sha1(raw).hexdigest()
            mimetype = 'image/svg+xml' if raw.lstrip().startswith(b'<svg') else 'image/png'

            att_info = current.get(menu.id)
            if att_info and att_info['checksum'] == expected_sha1:
                if att_info['has_db']:
                    continue
                store_fname = att_info['store_fname']
                if store_fname:
                    full_path = Attachment._full_path(store_fname)
                    if os.path.isfile(full_path) and os.path.getsize(full_path) > 0:
                        continue

            # Reconcile: missing record, stale hash, or missing/empty filestore file
            existing_atts = Attachment.search([
                ('res_model', '=', 'ir.ui.menu'),
                ('res_field', '=', 'web_icon_data'),
                ('res_id', '=', menu.id),
            ])
            if existing_atts:
                existing_atts.unlink()

            new_att = Attachment.create({
                'name': f"{(menu.name or 'menu').lower().replace(' ', '_')}_icon",
                'res_model': 'ir.ui.menu',
                'res_field': 'web_icon_data',
                'res_id': menu.id,
                'type': 'binary',
                'raw': raw,
                'mimetype': mimetype,
            })

            if new_att.store_fname:
                fpath = Attachment._full_path(new_att.store_fname)
                if not os.path.isfile(fpath):
                    os.makedirs(os.path.dirname(fpath), exist_ok=True)
                    with open(fpath, 'wb') as f:
                        f.write(raw)

            repaired += 1

        if repaired:
            self.env['ir.ui.menu'].invalidate_model(['web_icon_data'])
            import logging
            logging.getLogger(__name__).info("Insilos icon reconciliation repaired %d menu icon(s)", repaired)
        return repaired

    def unlink(self):
        # Detach children and promote them to top-level, because it would be unwise to
        # cascade-delete submenus blindly. We also can't use ondelete=set null because
        # that is not supported when _parent_store is used (would silently corrupt it).
        # TODO: ideally we should move them under a generic "Orphans" menu somewhere?
        direct_children = self.with_context(active_test=False).search([('parent_id', 'in', self.ids)])
        direct_children.write({'parent_id': False})

        return super().unlink()

    def copy(self, default=None):
        new_menus = super().copy(default=default)
        for new_menu in new_menus:
            match = NUMBER_PARENS.search(new_menu.name)
            if match:
                next_num = int(match.group(1)) + 1
                new_menu.name = NUMBER_PARENS.sub('(%d)' % next_num, new_menu.name)
            else:
                new_menu.name = new_menu.name + '(1)'
        return new_menus

    @api.model
    def get_user_roots(self):
        """ Return all root menu ids visible for the user.

        :return: the root menu ids
        :rtype: list(int)
        """
        return self.search([('parent_id', '=', False)])._filter_visible_menus()

    def _load_menus_blacklist(self):
        return []

    @api.model
    @api.ormcache('self.env.uid', 'self.env.lang')
    def load_menus_root(self):
        fields = ['name', 'sequence', 'parent_id', 'action', 'web_icon_data']
        menu_roots = self.get_user_roots()
        menu_roots_data = menu_roots.read(fields) if menu_roots else []

        menu_root = {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': menu_roots_data,
            'all_menu_ids': menu_roots.ids,
        }

        xmlids = menu_roots._get_menuitems_xmlids()
        for menu in menu_roots_data:
            menu['xmlid'] = xmlids.get(menu['id'], '')

        return menu_root

    @api.model
    @api.ormcache('self.env.uid', 'debug', 'self.env.lang')
    def load_menus(self, debug):
        blacklisted_menu_ids = self._load_menus_blacklist()
        visible_menus = self.search_fetch(
            [('id', 'not in', blacklisted_menu_ids)],
            ['name', 'parent_id', 'action', 'web_icon'],
        )._filter_visible_menus()

        children_dict = defaultdict(list)  # {parent_id: []} / parent_id == False for root menus
        for menu in visible_menus:
            children_dict[menu.parent_id.id].append(menu.id)

        app_info = {}
        # recursively set app ids to related children
        def _set_app_id(menu_app_id, menu_id):
            app_info[menu_id] = menu_app_id
            for child_id in children_dict[menu_id]:
                _set_app_id(menu_app_id, child_id)

        for root_menu_id in children_dict[False]:
            _set_app_id(root_menu_id, root_menu_id)

        # Filter out menus not related to an app (+ keep root menu), it happens when
        # some parent menu are not visible for group.
        visible_menus = visible_menus.filtered(lambda menu: menu.id in app_info)

        xmlids = visible_menus._get_menuitems_xmlids()
        icon_attachments = self.env['ir.attachment'].sudo().search_fetch(
            domain=[
                ('res_model', '=', 'ir.ui.menu'),
                ('res_id', 'in', visible_menus._ids),
                ('res_field', '=', 'web_icon_data'),
            ],
            field_names=['res_id', 'raw', 'mimetype'],
            order='res_id',
        )
        icon_attachments_res_id = {attachment.res_id: attachment for attachment in icon_attachments}

        menus_dict = {}
        action_ids_by_type = defaultdict(list)
        for menu in visible_menus:

            menu_id = menu.id
            attachment = icon_attachments_res_id.get(menu_id)

            if action := menu.action:
                action_model = action._name
                action_id = action.id
                action_ids_by_type[action_model].append(action_id)
            else:
                action_model = False
                action_id = False

            # --- Robust Insilos Icon Resolution (4-Tier Self-Healing) ---
            icon_b64 = False
            icon_mimetype = False

            # Tier 1: Check DB attachment payload and validate non-empty
            if attachment:
                try:
                    raw = attachment.raw
                    if raw:
                        b64_val = raw.to_base64()
                        if b64_val:
                            icon_b64 = b64_val
                            icon_mimetype = attachment.mimetype
                except Exception:
                    icon_b64 = False

            # Tier 2: Seamless disk fallback if attachment is missing, corrupted, or filestore file lost
            if not icon_b64 and menu.web_icon:
                try:
                    disk_icon = self._read_image(menu.web_icon)
                    if disk_icon:
                        b64_val = disk_icon.to_base64()
                        if b64_val:
                            icon_b64 = b64_val
                            icon_mimetype = (
                                'image/svg+xml' if (menu.web_icon or '').endswith('.svg') or bytes(disk_icon).lstrip().startswith(b'<svg') else 'image/png'
                            )
                except Exception:
                    icon_b64 = False

            # Tier 3: Canonical Insilos Horizon-Carbon neutral tile fallback
            if not icon_b64:
                try:
                    neutral_icon = (
                        self._read_image('base,static/description/icon.svg') or
                        self._read_image('base,static/description/icon.png')
                    )
                    if neutral_icon:
                        b64_val = neutral_icon.to_base64()
                        if b64_val:
                            icon_b64 = b64_val
                            icon_mimetype = 'image/svg+xml' if bytes(neutral_icon).lstrip().startswith(b'<svg') else 'image/png'
                except Exception:
                    icon_b64 = False

            # Tier 4: Dynamic initial-letter squircle tile fallback for unmapped or unknown apps
            if not icon_b64:
                try:
                    dynamic_icon = self._generate_dynamic_app_icon(menu.name or 'Insilos')
                    if dynamic_icon:
                        icon_b64 = dynamic_icon.to_base64()
                        icon_mimetype = 'image/svg+xml'
                except Exception:
                    pass

            menus_dict[menu_id] = {
                'id': menu_id,
                'name': menu.name,
                'app_id': app_info[menu_id],
                'action_model': action_model,
                'action_id': action_id,
                'web_icon': menu.web_icon,
                'web_icon_data': icon_b64,
                'web_icon_data_mimetype': icon_mimetype,
                'xmlid': xmlids.get(menu_id, ""),
            }

        # prefetch action.path
        for model_name, action_ids in action_ids_by_type.items():
            self.env[model_name].sudo().browse(action_ids).fetch(['path'])

        # set children + model_path
        for menu_dict in menus_dict.values():
            if menu_dict['action_model']:
                menu_dict['action_path'] = self.env[menu_dict['action_model']].sudo().browse(menu_dict['action_id']).path
            else:
                menu_dict['action_path'] = False
            menu_dict['children'] = children_dict[menu_dict['id']]

        menus_dict['root'] = {
            'id': False,
            'name': 'root',
            'children': children_dict[False],
        }
        return menus_dict

    def _get_menuitems_xmlids(self):
        menuitems = self.env['ir.model.data'].sudo().search_fetch(
            [('res_id', 'in', self.ids), ('model', '=', 'ir.ui.menu')],
            ['res_id', 'complete_name'],
        )

        return {
            menu.res_id: menu.complete_name
            for menu in menuitems
        }
