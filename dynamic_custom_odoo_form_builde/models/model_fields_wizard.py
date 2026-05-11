from thrive import models, fields, api, _


class ModelFieldsWizard(models.TransientModel):
    _name = 'dynamic.form.model.fields.wizard'
    _description = 'Model Fields Wizard'

    model_id = fields.Many2one('ir.model', 'Model', required=True, readonly=True)
    model_name = fields.Char(related='model_id.model', readonly=True)
    field_ids = fields.One2many('dynamic.form.model.fields.wizard.line', 'wizard_id', string='Fields')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_model_id'):
            model_id = self.env.context.get('default_model_id')
            model = self.env['ir.model'].browse(model_id)
            
            if model.exists():
                res.update({
                    'model_id': model_id,
                })
                # Create field lines
                field_lines = []
                try:
                    target_model = self.env[model.model]
                    for field_name, field_obj in target_model._fields.items():
                        # Skip technical fields
                        if field_name in ['id', 'create_date', 'write_date', 'create_uid', 'write_uid', '__last_update']:
                            continue
                        
                        # Skip relational fields
                        if field_obj.type in ['many2one', 'many2many', 'one2many', 'one2one']:
                            continue
                        
                        field_lines.append((0, 0, {
                            'field_name': field_name,
                            'field_label': field_obj.string or field_name,
                            'field_type': field_obj.type,
                            'required': field_obj.required,
                            'readonly': field_obj.readonly,
                        }))
                    
                    # Sort by field name
                    field_lines.sort(key=lambda x: x[2]['field_name'])
                    res['field_ids'] = field_lines
                except Exception as e:
                    pass
        
        return res

    def action_close(self):
        """Close the wizard"""
        return {'type': 'ir.actions.act_window_close'}


class ModelFieldsWizardLine(models.TransientModel):
    _name = 'dynamic.form.model.fields.wizard.line'
    _description = 'Model Fields Wizard Line'
    _order = 'field_name'

    wizard_id = fields.Many2one('dynamic.form.model.fields.wizard', 'Wizard', required=True, ondelete='cascade')
    field_name = fields.Char('Field Name', required=True, readonly=True)
    field_label = fields.Char('Field Label', readonly=True)
    field_type = fields.Char('Field Type', readonly=True)
    required = fields.Boolean('Required', readonly=True)
    readonly = fields.Boolean('Readonly', readonly=True)
