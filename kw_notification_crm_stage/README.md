# CRM Stage Notifications

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue.png)](http://www.gnu.org/licenses/lgpl-3.0-standalone.html)
[![Maintainer: Kitworks](https://img.shields.io/badge/maintainer-Kitworks-purple.png)](https://kitworks.systems/)
[![Odoo 14.0](https://img.shields.io/badge/Odoo-14.0-875A7B.png)](https://github.com/thrive/thrive/tree/14.0)

Automatically send SMS, Viber, and Email notifications when CRM leads change stages.

## Features

* **Automatic Stage Notifications**: Send SMS/Viber and Email notifications automatically when CRM leads move between stages
* **Multiple Communication Channels**: Support for SMS, Viber messages, and Email notifications
* **Template-Based**: Configure custom SMS and Email templates for each CRM stage
* **Smart Phone/Email Detection**: Automatically uses lead's phone/mobile/email or partner's contact information
* **Message Logging**: Optionally log sent notifications as notes in the lead's chatter
* **Advanced SMS Features**: Support for TurboSMS provider with Viber, transactional messages, TTL, images, and click tracking

## Configuration

1. **Configure CRM Stages**:
   - Go to **CRM > Configuration > Stages**
   - Select a stage and configure:
     - **SMS/Viber Template**: Choose an SMS template for automatic notifications
     - **Email Template**: Choose an Email template for automatic notifications  
     - **Log as Note**: Enable to log sent messages in lead chatter

2. **Create SMS Templates**:
   - Go to **Settings > Technical > SMS > SMS Templates**
   - Create templates with dynamic content using Odoo's template syntax
   - Configure TurboSMS-specific options if using TurboSMS provider

3. **Create Email Templates**:
   - Go to **Settings > Technical > Email > Email Templates**
   - Create templates for lead model (`crm.lead`)
   - Use Odoo's template syntax for dynamic content

## Usage

### Automatic Notifications

When a CRM lead changes stages:

1. **SMS Notification**: If the target stage has an SMS template configured:
   - System renders the template with lead data
   - SMS is sent to lead's phone/mobile number or partner's contact
   - Message is logged in chatter if "Log as Note" is enabled

2. **Email Notification**: If the target stage has an Email template configured:
   - System renders the template with lead data
   - Email is sent to lead's email or partner's email
   - Message is logged in chatter if "Log as Note" is enabled

### Contact Resolution

The system uses the following priority for contact information:

**For SMS/Viber**:
1. Lead's phone field
2. Partner's mobile field  
3. Partner's phone field

**For Email**:
1. Lead's email_from field
2. Partner's email field

### Template Variables

In your SMS and Email templates, you can use any field from the CRM lead model:

```python
Hello ${object.partner_name or 'Customer'},

Your inquiry "${object.name}" has moved to stage: ${object.stage_id.name}

% if object.user_id:
Your sales representative: ${object.user_id.name}
% endif

Thank you for your business!
```

## Technical Details

### Models Extended

* **crm.lead**: Added automatic notification triggers and message sending flag
* **crm.stage**: Added SMS and Email template configuration fields

### Key Fields

**CrmLead** (`crm.lead`):
- `kw_send_message` (Boolean): Internal flag to prevent duplicate messages

**CrmStage** (`crm.stage`):
- `kw_sms_template_id` (Many2one): SMS/Viber template for this stage
- `kw_email_template_id` (Many2one): Email template for this stage  
- `kw_sms_mass_keep_log` (Boolean): Log sent messages in chatter

### Dependencies

* **crm**: Core CRM functionality
* **sms**: SMS sending capabilities
* **generic_mixin**: Change tracking functionality
* **mail**: Email functionality

## TurboSMS Integration

This module includes advanced integration with TurboSMS provider, supporting:

* **Viber Messages**: Rich messages with images and buttons
* **Transactional SMS**: High-priority delivery
* **TTL (Time To Live)**: Message expiration settings
* **Click Tracking**: Monitor link clicks in messages
* **File Attachments**: Send images and documents

Configure these options in your SMS templates when using TurboSMS provider.

## Bug Tracker

Bugs are tracked on [Kitworks Support](https://kitworks.systems/requests).
In case of trouble, please check there if your issue has already been reported.

## Maintainer

This module is maintained by [Kitworks Systems](https://kitworks.systems).

We can provide you further Odoo Support, Odoo implementation, Odoo customization, Odoo 3rd Party development and integration software, consulting services. Our main goal is to provide the best quality product for you.

For any questions [contact us](mailto:support@kitworks.systems).
