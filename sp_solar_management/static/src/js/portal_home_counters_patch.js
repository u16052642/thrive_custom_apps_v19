/** @thrive-module **/

import { patch } from "@web/core/utils/patch";
import { PortalHomeCounters } from "@portal/interactions/portal_home_counters";
import { rpc } from "@web/core/network/rpc";

patch(PortalHomeCounters.prototype, {
    async updateCounters() {
        const needed = Object.values(this.el.querySelectorAll("[data-placeholder_count]")).map(
            (documentsCounterEl) => documentsCounterEl.dataset["placeholder_count"]
        );
        const numberRpc = Math.min(Math.ceil(needed.length / 5), 3); // max 3 rpc, up to 5 counters by rpc ideally
        const counterByRpc = Math.ceil(needed.length / numberRpc);
        const countersAlwaysDisplayed = this.getCountersAlwaysDisplayed();

        const proms = [...Array(Math.min(numberRpc, needed.length)).keys()].map(async (i) => {
            const documentsCountersData = await rpc("/my/counters", {
                counters: needed.slice(i * counterByRpc, (i + 1) * counterByRpc),
            });
            Object.keys(documentsCountersData).forEach((counterName) => {
                const documentsCounterEl = this.el.querySelector(
                    `[data-placeholder_count='${counterName}']`
                );
                if (documentsCounterEl) {
                    documentsCounterEl.textContent = documentsCountersData[counterName];
                    if (
                        documentsCountersData[counterName] !== 0 ||
                        countersAlwaysDisplayed.includes(counterName)
                    ) {
                        const card = documentsCounterEl.closest(".o_portal_index_card");
                        if (card) {
                            card.classList.remove("d-none");
                        }
                    }
                }
            });
            return documentsCountersData;
        });
        return Promise.all(proms).then((results) => {
            const spinner = this.el.querySelector(".o_portal_doc_spinner");
            if (spinner) {
                spinner.remove();
            }
        });
    }
});
