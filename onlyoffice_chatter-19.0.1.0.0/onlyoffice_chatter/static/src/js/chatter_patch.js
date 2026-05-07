/** @thrive-module **/

import { patch } from "@web/core/utils/patch";
import { useService, useAutofocus } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { Component, useState } from "@thrive/owl";

// ─────────────────────────────────────────────────────────────────
//  Diálogo OWL — selector de formato y título
// ─────────────────────────────────────────────────────────────────
class OnlyofficeChatterCreateDialog extends Component {
  static components = { Dialog };
  static template = "onlyoffice_chatter.CreateDialog";

  setup() {
    this.data = this.env.dialogData;
    this.notification = useService("notification");
    useAutofocus();

    this.formats = [
      { ext: "docx", label: _t("Document") },
      { ext: "xlsx", label: _t("Spreadsheet") },
      { ext: "pptx", label: _t("Presentation") },
    ];

    this.dialogTitle = _t("Create with ONLYOFFICE");

    this.labels = {
      title: _t("Title"),
      placeholder: _t("New Document"),
      creating: _t("Creating..."),
      create: _t("Create"),
      cancel: _t("Cancel"),
    };

    this.state = useState({
      isCreating: false,
      selectedFormat: "docx",
      title: _t("New Document"),
    });
  }

  selectFormat(ext) {
    this.state.selectedFormat = ext;
  }

  handleFormatKeydown(ext, ev) {
    if (ev.key === "Enter" || ev.key === " ") {
      ev.preventDefault();
      this.selectFormat(ext);
    }
  }

  isButtonDisabled() {
    return this.state.isCreating || !this.state.selectedFormat || !this.state.title;
  }

  async createFile() {
    if (this.isButtonDisabled()) return;

    this.state.isCreating = true;
    try {
      const result = await rpc("/onlyoffice/chatter/file/create", {
        res_model: this.props.resModel,
        res_id: this.props.resId,
        supported_format: this.state.selectedFormat,
        title: this.state.title,
      });

      if (result.error) {
        this.notification.add(result.error, { type: "danger", sticky: false });
        return;
      }

      this.notification.add(_t("Document created successfully"), {
        type: "success",
        sticky: false,
      });

      if (this.props.onCreated) {
        await this.props.onCreated();
      }

      if (result.url) {
        window.open(result.url, "_blank");
      }

      this.data.close();
    } catch (e) {
      console.error("OnlyOffice Chatter: createFile failed", e);
      this.notification.add(_t("Error creating document"), {
        type: "danger",
        sticky: false,
      });
    } finally {
      this.state.isCreating = false;
    }
  }
}

// ─────────────────────────────────────────────────────────────────
//  Patch del Chatter
// ─────────────────────────────────────────────────────────────────
patch(Chatter.prototype, {
  setup() {
    super.setup(...arguments);
    this.dialog = useService("dialog");

    this.ooLabels = {
      buttonTitle: _t("Create OnlyOffice Document"),
      buttonText: _t("New"),
    };
  },

  openOnlyofficeDialog() {
    this.dialog.add(OnlyofficeChatterCreateDialog, {
      // Odoo 19: el Chatter expone threadModel y threadId, NO resModel/resId
      resModel: this.props.threadModel,
      resId: this.props.threadId,
      onCreated: async () => {
        try {
          if (
            this.attachmentList &&
            typeof this.attachmentList.load === "function"
          ) {
            await this.attachmentList.load();
          } else if (typeof this.reloadAttachments === "function") {
            await this.reloadAttachments();
          } else if (
            this.props &&
            typeof this.props.onSave === "function"
          ) {
            await this.props.onSave();
          }
        } catch (err) {
          console.warn("OnlyOffice Chatter: could not refresh attachments", err);
        }
      },
    });
  },
});
