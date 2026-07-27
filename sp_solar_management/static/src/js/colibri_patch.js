/** @thrive-module **/

import { Colibri } from "@web/public/colibri";

const originalApplyTOut = Colibri.prototype.applyTOut;
Colibri.prototype.applyTOut = function (el, value, initialValue) {
    if (!el) {
        return;
    }
    return originalApplyTOut.call(this, el, value, initialValue);
};

const originalApplyAttr = Colibri.prototype.applyAttr;
Colibri.prototype.applyAttr = function (el, attr, value, initialValue) {
    if (!el) {
        return;
    }
    return originalApplyAttr.call(this, el, attr, value, initialValue);
};

const originalUpdateContent = Colibri.prototype.updateContent;
Colibri.prototype.updateContent = function () {
    for (const [sel, nodes] of this.dynamicNodes.entries()) {
        if (nodes && nodes.length) {
            const filteredNodes = [];
            for (const node of nodes) {
                if (node) {
                    filteredNodes.push(node);
                }
            }
            this.dynamicNodes.set(sel, filteredNodes);
        }
    }
    return originalUpdateContent.call(this);
};

const originalDestroy = Colibri.prototype.destroy;
Colibri.prototype.destroy = function () {
    for (const [sel, nodes] of this.dynamicNodes.entries()) {
        if (nodes && nodes.length) {
            const filteredNodes = [];
            for (const node of nodes) {
                if (node) {
                    filteredNodes.push(node);
                }
            }
            this.dynamicNodes.set(sel, filteredNodes);
        }
    }
    return originalDestroy.call(this);
};
