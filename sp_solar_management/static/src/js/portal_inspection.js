/** @thrive-module **/

function initPortalInspectionPage() {
    document.querySelectorAll("tr.o_clickable_row").forEach(function (row) {
        row.addEventListener("click", function (ev) {
            if (ev.target.closest("a, button, input, label")) {
                return;
            }
            var href = row.getAttribute("data-href");
            if (href) {
                window.location.href = href;
            }
        });
    });

    initPortalDependentFields();
    initPortalChecklist();
    initPortalImageModal();
}

function initPortalDependentFields() {
    var dependentFields = document.querySelectorAll(".o_portal_dependent_field[data-controller][data-when]");
    var controllerNames = new Set();

    dependentFields.forEach(function (field) {
        controllerNames.add(field.getAttribute("data-controller"));
    });

    function setFieldEnabled(field, enabled) {
        field.classList.toggle("d-none", !enabled);
        field.querySelectorAll("input, select, textarea").forEach(function (input) {
            input.disabled = !enabled;
            if (field.getAttribute("data-required") === "1") {
                input.required = enabled;
            }
        });
    }

    function refreshDependentFields(controllerName) {
        var controller = document.querySelector('[name="' + controllerName + '"]');
        var controllerValue = controller ? controller.value : "";

        document.querySelectorAll('.o_portal_dependent_field[data-controller="' + controllerName + '"]').forEach(function (field) {
            var expectedValues = (field.getAttribute("data-when") || "").split(",").map(function (value) {
                return value.trim();
            });
            setFieldEnabled(field, expectedValues.includes(controllerValue));
        });
    }

    controllerNames.forEach(function (controllerName) {
        var controller = document.querySelector('[name="' + controllerName + '"]');
        if (!controller) {
            return;
        }
        controller.addEventListener("change", function () {
            refreshDependentFields(controllerName);
        });
        refreshDependentFields(controllerName);
    });
}

function initPortalChecklist() {
    var addButton = document.getElementById("add_checklist_line");
    var checklistLines = document.getElementById("portal_checklist_lines");
    var hiddenInputs = document.getElementById("portal_hidden_checklist_inputs");
    var noChecklistMessage = document.getElementById("portal_no_checklist_message");

    if (!addButton || !checklistLines || !hiddenInputs) {
        return;
    }

    var nextChecklistKey = checklistLines.querySelectorAll(".checklist-line").length + 1;

    function ensureDeleteInput(key) {
        var existing = hiddenInputs.querySelector('input[name="checklist_delete_ids"][value="' + key + '"]');
        if (existing) {
            return;
        }
        var input = document.createElement("input");
        input.type = "hidden";
        input.name = "checklist_delete_ids";
        input.value = key;
        hiddenInputs.appendChild(input);
    }

    function removeChecklistLine(card, key) {
        var hiddenKeyInput = card.querySelector('input[name="checklist_keys"]');
        if (hiddenKeyInput && !String(key).startsWith("new_")) {
            ensureDeleteInput(String(key));
        }
        card.remove();
        if (!checklistLines.querySelector(".checklist-line") && noChecklistMessage) {
            noChecklistMessage.style.display = "";
        }
    }

    function bindDeleteButton(button) {
        button.addEventListener("click", function () {
            var card = button.closest(".checklist-line");
            if (!card) {
                return;
            }
            var key = card.getAttribute("data-checklist-id") || "";
            removeChecklistLine(card, key);
        });
    }

    checklistLines.querySelectorAll(".o_portal_checklist_delete").forEach(bindDeleteButton);

    addButton.addEventListener("click", function () {
        var key = "new_" + String(nextChecklistKey++);
        var card = document.createElement("div");
        card.className = "border rounded p-3 mb-3 checklist-line";
        card.setAttribute("data-checklist-id", key);
        card.innerHTML =
            '<input type="hidden" name="checklist_keys" value="' + key + '">' +
            '<div class="row g-3 align-items-start">' +
                '<div class="col-lg-5">' +
                    '<label class="form-label">Checklist Point</label>' +
                    '<input type="text" class="form-control" name="checklist_name_' + key + '" value="">' +
                '</div>' +
                '<div class="col-lg-7">' +
                    '<label class="form-label">Description</label>' +
                    '<textarea class="form-control o_portal_checklist_description" rows="1" name="checklist_description_' + key + '"></textarea>' +
                '</div>' +
                '<div class="col-12 d-flex justify-content-end">' +
                    '<button type="button" class="btn btn-sm btn-outline-danger o_portal_checklist_delete">Delete</button>' +
                '</div>' +
            '</div>';

        checklistLines.appendChild(card);
        bindDeleteButton(card.querySelector(".o_portal_checklist_delete"));

        if (noChecklistMessage) {
            noChecklistMessage.style.display = "none";
        }

        var nameInput = card.querySelector('input[name="checklist_name_' + key + '"]');
        if (nameInput) {
            nameInput.focus();
        }
    });
}

function initPortalImageModal() {
    var modal = document.getElementById("portal_image_modal");
    var openButton = document.getElementById("open_image_modal");
    var closeButton = document.getElementById("close_image_modal");
    var cancelButton = document.getElementById("cancel_image_modal");
    var saveButton = document.getElementById("save_image_modal");
    var tagInput = document.getElementById("portal_modal_image_tag");
    var fileInput = document.getElementById("portal_modal_image_file");
    var preview = document.getElementById("portal_modal_image_preview");
    var imageLines = document.getElementById("portal_image_lines");
    var hiddenInputs = document.getElementById("portal_hidden_image_inputs");
    var noImagesMessage = document.getElementById("portal_no_saved_images_message");

    if (!modal || !openButton || !closeButton || !cancelButton || !saveButton || !tagInput || !fileInput || !preview || !imageLines || !hiddenInputs) {
        return;
    }

    var nextImageKey = imageLines.querySelectorAll(".o_portal_pending_image").length + 1;

    function resetModal() {
        tagInput.value = "";
        fileInput.value = "";
        preview.innerHTML = '<div class="o_pending_image_placeholder">Preview will appear here after selecting an image.</div>';
    }

    function openModal() {
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("o_portal_modal_open");
    }

    function closeModal() {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("o_portal_modal_open");
        resetModal();
    }

    function renderPreview(file) {
        if (!file) {
            resetModal();
            return;
        }
        var reader = new FileReader();
        reader.onload = function (ev) {
            preview.innerHTML = "";
            var image = document.createElement("img");
            image.src = ev.target.result;
            image.alt = file.name || "Preview";
            image.className = "o_pending_preview_image";
            preview.appendChild(image);
        };
        reader.readAsDataURL(file);
    }

    function createHiddenInput(name, value) {
        var input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = value;
        return input;
    }

    function removePendingImage(key, card) {
        hiddenInputs.querySelectorAll('[data-image-key="' + key + '"]').forEach(function (node) {
            node.remove();
        });
        if (card) {
            card.remove();
        }
    }

    function addPendingImage() {
        var file = fileInput.files && fileInput.files[0];
        if (!file) {
            fileInput.focus();
            return;
        }

        var key = String(nextImageKey++);
        var imageTag = tagInput.value.trim();
        var dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);

        hiddenInputs.appendChild(createHiddenInput("image_keys", key)).setAttribute("data-image-key", key);
        hiddenInputs.appendChild(createHiddenInput("inspection_image_tag_" + key, imageTag)).setAttribute("data-image-key", key);

        var titleInput = createHiddenInput("inspection_image_title_" + key, file.name || "Inspection Image");
        titleInput.setAttribute("data-image-key", key);
        hiddenInputs.appendChild(titleInput);

        var fileField = document.createElement("input");
        fileField.type = "file";
        fileField.name = "inspection_image_" + key;
        fileField.className = "d-none";
        fileField.files = dataTransfer.files;
        fileField.setAttribute("data-image-key", key);
        hiddenInputs.appendChild(fileField);

        var reader = new FileReader();
        reader.onload = function (ev) {
            var card = document.createElement("div");
            card.className = "o_portal_gallery_card o_portal_pending_image";
            card.setAttribute("data-image-key", key);
            card.innerHTML =
                '<img alt="Pending image preview">' +
                '<div class="o_portal_gallery_body">' +
                    '<div class="o_portal_gallery_tag"></div>' +
                    '<div class="o_portal_gallery_actions">' +
                        '<span class="o_portal_image_meta">Pending upload</span>' +
                        '<button type="button" class="btn btn-sm btn-outline-danger">Remove</button>' +
                    '</div>' +
                '</div>';
            card.querySelector("img").src = ev.target.result;
            card.querySelector("img").alt = file.name || "Pending image preview";
            card.querySelector(".o_portal_gallery_tag").textContent = imageTag || "Image";
            card.querySelector("button").addEventListener("click", function () {
                removePendingImage(key, card);
            });
            imageLines.appendChild(card);

            if (noImagesMessage) {
                noImagesMessage.style.display = "none";
            }

            closeModal();
        };
        reader.readAsDataURL(file);
    }

    openButton.addEventListener("click", openModal);
    closeButton.addEventListener("click", closeModal);
    cancelButton.addEventListener("click", closeModal);
    saveButton.addEventListener("click", addPendingImage);
    fileInput.addEventListener("change", function () {
        renderPreview(fileInput.files && fileInput.files[0]);
    });
    modal.addEventListener("click", function (ev) {
        if (ev.target === modal) {
            closeModal();
        }
    });
    document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && modal.classList.contains("is-open")) {
            closeModal();
        }
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPortalInspectionPage);
} else {
    initPortalInspectionPage();
}
