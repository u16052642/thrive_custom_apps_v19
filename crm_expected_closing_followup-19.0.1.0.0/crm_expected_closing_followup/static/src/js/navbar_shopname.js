/** @thrive-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { CashierName } from "@point_of_sale/app/components/navbar/cashier_name/cashier_name";

patch(CashierName.prototype, {
    // For get the shop name in the nav bar in pos product screen
    get shopname() {
        return this.pos?.config?.display_name || ''
        
    },
})