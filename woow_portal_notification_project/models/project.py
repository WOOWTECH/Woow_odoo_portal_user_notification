from odoo import api, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def _wpn_portal_record_domain(self):
        """Projects shared with portal users; internal projects stay out of
        the centre of internal users."""
        return [('privacy_visibility', '=', 'portal')]


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def _wpn_portal_record_domain(self):
        """Tasks of projects shared with portal users."""
        return [('project_id.privacy_visibility', '=', 'portal')]
