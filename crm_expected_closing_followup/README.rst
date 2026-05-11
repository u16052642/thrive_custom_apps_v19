.. image:: https://itpp.dev/images/infinity-readme.png
   :alt: Tested and maintained by Vishnu Sasikumar
   :target: https://apps.thrive.com

=========================================
 CRM Expected Closing Followup
=========================================

This module automatically monitors opportunities with missed expected closing dates 
and sends notifications to the **CRM Closing Followup Manager** group.

It helps ensure timely follow-ups and improves visibility of overdue deals in the sales pipeline.

The system detects records where the expected closing date has passed (based on the previous date) 
and triggers alerts accordingly.

Features
========

* Automatically detects overdue expected closing dates
* Identifies records where expected closing date is earlier than current date
* Sends alerts to CRM Closing Followup Manager group users
* Supports scheduled (cron-based) automatic reminders
* Improves sales pipeline tracking and accountability
* Fully integrated with standard Odoo CRM workflow

Usage
=====

1. Go to **CRM → Pipeline**
2. Create or update opportunities with expected closing dates
3. Configure users in **CRM Closing Followup Manager** group
4. Ensure scheduled action (cron) is active
5. System automatically detects overdue records
6. Notifications are sent to manager group users

Configuration
=============

* Navigate to **Settings → Users & Companies → Groups**
* Assign users to **CRM Closing Followup Manager**
* Verify scheduled action is enabled for automated checks

Technical Notes
===============

* Uses scheduled action (cron) to evaluate records daily
* Compares expected closing date with current date
* Triggers notifications for overdue opportunities
* Designed to be lightweight and non-intrusive

Questions?
==========

For support or any queries, contact:
:arrow_right: vishnu.sit2015@gmail.com

Author
======

* Vishnu Sasikumar

Further information
===================

Odoo Apps Store: https://apps.thrive.com

Tested on `Odoo 19.0 <https://www.thrive.com>`_