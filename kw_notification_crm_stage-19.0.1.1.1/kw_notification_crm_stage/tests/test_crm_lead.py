from unittest.mock import patch
from thrive.tests.common import TransactionCase


class TestCrmLead(TransactionCase):

    def setUp(self):
        super().setUp()
        self.lead_model = self.env['crm.lead']
        self.stage_model = self.env['crm.stage']
        self.partner_model = self.env['res.partner']
        self.mail_template_model = self.env['mail.template']

        self.partner = self.partner_model.create({
            'name': 'Test Partner',
            'email': 'partner@test.com',
            'phone': '+1234567890', })

        self.mail_template = self.mail_template_model.create({
            'name': 'Test Email Template',
            'model_id': self.env.ref('crm.model_crm_lead').id,
            'subject': 'Test Subject for ${object.name}',
            'body_html': '<p>Dear ${object.partner_name}, test body</p>', })

        self.stage_with_email = self.stage_model.create({
            'name': 'Stage with Email',
            'kw_email_template_id': self.mail_template.id,
            'kw_sms_mass_keep_log': True, })

        self.stage_without_templates = self.stage_model.create({
            'name': 'Stage without Templates',
            'kw_sms_mass_keep_log': False, })

    def test_crm_lead_fields_exist(self):
        lead = self.lead_model.create({
            'name': 'Test Lead',
            'partner_id': self.partner.id, })

        self.assertTrue(hasattr(lead, 'kw_send_message'))

    def test_crm_lead_default_values(self):
        lead = self.lead_model.create({
            'name': 'Test Lead',
            'partner_id': self.partner.id, })

        self.assertFalse(lead.kw_send_message)

    def test_crm_lead_inherit_models(self):
        lead = self.lead_model.create({'name': 'Test Lead', })

        self.assertIn('generic.mixin.track.changes', lead._inherit)
        self.assertIn('crm.lead', lead._inherit)

    def test_post_write_stage_id_email_with_kw_send_message_true(self):
        lead = self.lead_model.create({
            'name': 'Test Lead Email Blocked',
            'partner_id': self.partner.id,
            'stage_id': self.stage_with_email.id,
            'kw_send_message': True, })

        self.assertEqual(lead.stage_id.id, self.stage_with_email.id)
        self.assertTrue(lead.stage_id.kw_email_template_id.id)
        self.assertTrue(lead.kw_send_message)

    def test_post_write_stage_id_email_without_keep_log(self):
        stage_no_log = self.stage_model.create({
            'name': 'Stage No Log',
            'kw_email_template_id': self.mail_template.id,
            'kw_sms_mass_keep_log': False, })

        lead = self.lead_model.create({
            'name': 'Test Lead No Log',
            'partner_id': self.partner.id,
            'stage_id': stage_no_log.id,
            'email_from': 'test@example.com', })

        self.assertEqual(lead.stage_id.id, stage_no_log.id)
        self.assertFalse(lead.stage_id.kw_sms_mass_keep_log)

    def test_complex_stage_workflow(self):
        stage1 = self.stage_model.create({'name': 'Initial Stage', })

        stage2 = self.stage_model.create({
            'name': 'Final Stage',
            'kw_email_template_id': self.mail_template.id,
            'kw_sms_mass_keep_log': True, })

        lead = self.lead_model.create({
            'name': 'Workflow Test Lead',
            'partner_id': self.partner.id,
            'stage_id': stage1.id,
            'email_from': 'lead@test.com', })

        lead.write({'stage_id': stage2.id})
        self.assertEqual(lead.stage_id.id, stage2.id)
        self.assertTrue(lead.kw_send_message)

    @patch('thrive.addons.mail.models.mail_mail.MailMail.send')
    def test_post_write_stage_id_email_send_mock(self, mock_send):
        """Тест перевірки реального виклику відправки email з mock'ом"""
        lead = self.lead_model.create({
            'name': 'Test Lead Email Send',
            'partner_id': self.partner.id,
            'email_from': 'test@example.com',
            'kw_send_message': False,
        })

        # Зміна етапу повинна викликати відправку email
        lead.write({'stage_id': self.stage_with_email.id})

        # Перевіряємо, що email.send() був викликаний
        mock_send.assert_called()
        self.assertTrue(lead.kw_send_message)

    def test_post_write_stage_id_no_template_no_send(self):
        """Тест перевірки, що без шаблону повідомлення не відправляються"""
        lead = self.lead_model.create({
            'name': 'Test Lead No Template',
            'partner_id': self.partner.id,
            'email_from': 'test@example.com',
            'kw_send_message': False,
        })

        # Зміна етапу без шаблону не повинна змінювати kw_send_message
        lead.write({'stage_id': self.stage_without_templates.id})

        self.assertFalse(lead.kw_send_message)

    def test_post_write_stage_id_sms_basic_functionality(self):
        """Тест основної функціональності відправки SMS"""
        # Створюємо SMS шаблон з мінімальними полями
        sms_template = self.env['sms.template'].create({
            'name': 'Test SMS Template',
            'model_id': self.env.ref('crm.model_crm_lead').id,
            'body': 'Hello ${object.name}, your lead status changed!',
        })

        stage_with_sms = self.stage_model.create({
            'name': 'Stage with SMS',
            'kw_sms_template_id': sms_template.id,
            'kw_sms_mass_keep_log': True,
        })

        lead = self.lead_model.create({
            'name': 'Test Lead SMS',
            'partner_id': self.partner.id,
            'phone': '+1234567890',
            'kw_send_message': False,
        })

        # Зміна етапу повинна викликати відправку SMS
        lead.write({'stage_id': stage_with_sms.id})

        self.assertTrue(lead.kw_send_message)
        self.assertEqual(lead.stage_id.id, stage_with_sms.id)

    def test_post_write_stage_id_sms_phone_fallback_logic(self):
        """Тест логіки вибору номера телефону (phone fallback)"""
        sms_template = self.env['sms.template'].create({
            'name': 'Test SMS Template Fallback',
            'model_id': self.env.ref('crm.model_crm_lead').id,
            'body': 'Test SMS for ${object.name}',
        })

        stage_with_sms = self.stage_model.create({
            'name': 'Stage SMS Fallback',
            'kw_sms_template_id': sms_template.id,
            'kw_sms_mass_keep_log': False,
        })

        # Тест 1: Використання phone з lead
        lead_with_phone = self.lead_model.create({
            'name': 'Lead with Phone',
            'partner_id': self.partner.id,
            'phone': '+9999999999',  # Має пріоритет
            'kw_send_message': False,
        })

        lead_with_phone.write({'stage_id': stage_with_sms.id})
        self.assertTrue(lead_with_phone.kw_send_message)

        # Тест 2: Fallback до partner.phone
        partner_phone_only = self.partner_model.create({
            'name': 'Partner Phone Only',
            'phone': '+7777777777',
        })

        lead_phone_fallback = self.lead_model.create({
            'name': 'Lead Phone Fallback',
            'partner_id': partner_phone_only.id,
            'phone': False,
            'kw_send_message': False,
        })

        lead_phone_fallback.write({'stage_id': stage_with_sms.id})
        self.assertTrue(lead_phone_fallback.kw_send_message)

    def test_post_write_stage_id_sms_logging_functionality(self):
        """Тест логіки логування SMS повідомлень"""
        # SMS шаблон з логуванням
        sms_template = self.env['sms.template'].create({
            'name': 'SMS Template with Log',
            'model_id': self.env.ref('crm.model_crm_lead').id,
            'body': 'SMS body for ${object.name}',
        })

        # SMS шаблон без логування
        sms_template_no_log = self.env['sms.template'].create({
            'name': 'SMS Template No Log',
            'model_id': self.env.ref('crm.model_crm_lead').id,
            'body': 'SMS body no log for ${object.name}',
        })

        stage_sms_log = self.stage_model.create({
            'name': 'Stage SMS with Log',
            'kw_sms_template_id': sms_template.id,
            'kw_sms_mass_keep_log': True,
        })

        stage_sms_no_log = self.stage_model.create({
            'name': 'Stage SMS No Log',
            'kw_sms_template_id': sms_template_no_log.id,
            'kw_sms_mass_keep_log': False,
        })

        # Тест SMS з логуванням
        lead_sms_log = self.lead_model.create({
            'name': 'Test SMS Lead with Log',
            'partner_id': self.partner.id,
            'phone': '+1111111111',
            'kw_send_message': False,
        })

        lead_sms_log.write({'stage_id': stage_sms_log.id})
        self.assertTrue(lead_sms_log.kw_send_message)

        # Тест SMS без логування
        lead_sms_no_log = self.lead_model.create({
            'name': 'Test SMS Lead No Log',
            'partner_id': self.partner.id,
            'phone': '+2222222222',
            'kw_send_message': False,
        })

        lead_sms_no_log.write({'stage_id': stage_sms_no_log.id})
        self.assertTrue(lead_sms_no_log.kw_send_message)

    @patch('thrive.addons.sms.models.sms_sms.SmsSms.send')
    def test_post_write_stage_id_sms_send_mock(self, mock_sms_send):
        """Тест перевірки реального виклику відправки SMS з mock'ом"""
        sms_template = self.env['sms.template'].create({
            'name': 'Mock SMS Template',
            'model_id': self.env.ref('crm.model_crm_lead').id,
            'body': 'Mock SMS for ${object.name}',
        })

        stage_with_sms = self.stage_model.create({
            'name': 'Stage SMS Mock',
            'kw_sms_template_id': sms_template.id,
            'kw_sms_mass_keep_log': False,
        })

        lead = self.lead_model.create({
            'name': 'Test Lead SMS Mock',
            'partner_id': self.partner.id,
            'phone': '+3333333333',
            'kw_send_message': False,
        })

        # Зміна етапу повинна викликати відправку SMS
        lead.write({'stage_id': stage_with_sms.id})

        # Перевіряємо, що sms.send() був викликаний
        mock_sms_send.assert_called()
        self.assertTrue(lead.kw_send_message)

    def test_post_write_stage_id_sms_no_phone_no_send(self):
        """Тест що SMS не відправляється без номера телефону"""
        sms_template = self.env['sms.template'].create({
            'name': 'No Phone SMS Template',
            'model_id': self.env.ref('crm.model_crm_lead').id,
            'body': 'SMS for ${object.name}',
        })

        stage_with_sms = self.stage_model.create({
            'name': 'Stage SMS No Phone',
            'kw_sms_template_id': sms_template.id,
            'kw_sms_mass_keep_log': False,
        })

        # Партнер без телефонів
        partner_no_phone = self.partner_model.create({
            'name': 'Partner No Phone',
            'phone': False,
        })

        lead_no_phone = self.lead_model.create({
            'name': 'Lead No Phone',
            'partner_id': partner_no_phone.id,
            'phone': False,
            'kw_send_message': False,
        })

        lead_no_phone.write({'stage_id': stage_with_sms.id})

        self.assertEqual(lead_no_phone.stage_id.id, stage_with_sms.id)
