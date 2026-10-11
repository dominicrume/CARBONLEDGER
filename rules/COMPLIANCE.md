# Compliance: What We Know, What We Must Ask

I am not a lawyer, and nobody on this project has been told these items are cleared. Status words:
VERIFIED = checked in a source this session. ASK COUNSEL = real question, no answer yet.

| # | Topic | Status | What it means for the build |
|---|---|---|---|
| C1 | Verra registry terms, clause 1.9: creating, marketing or transacting tokens ("Related Instruments") needs Verra's written consent. Verra said in January 2026 it aims to finish a formal tokenization policy by end of 2026. | VERIFIED (Verra's own statement, quoted in a January 2026 post) | We never wrap or reference Verra credits without consent. Backing is open decision 3. |
| C2 | Verra halted tokens built on retired credits in May 2022 to avoid double counting. | VERIFIED (several news reports) | A receipt token must not be confused with a credit. |
| C3 | The Climate Action Data Trust (World Bank Climate Warehouse, Singapore, IETA) already links data from major registries to help prevent double counting. | VERIFIED (World Bank blog, press reports) | We cannot claim "no registry exists". Consider integrating as a data source later. |
| C4 | Other registries' token policies (Gold Standard, ACR, Climate Action Reserve, Puro.earth for biochar). | ASK, not checked | Check each before linking its credits. |
| C5 | Environmental marketing claims (UK Competition and Markets Authority Green Claims Code, advertising rules, EU rules). | ASK COUNSEL | Drives the wording table in rules/HARDENING-PRODUCT.md. |
| C6 | Whether a non-transferable receipt token counts as a cryptoasset for UK financial promotion rules, and whether any version could be an investment. | ASK COUNSEL | Keep the token non-transferable and unpriced until answered. |
| C7 | A charitable trust holding land, with crops to the farmer's family, and a trustee-set price. | ASK COUNSEL | Needs a trust lawyer. The app's "trustee price" wording assumes this exists. |
| C8 | Personal data: farmers' GPS photos and locations, app users' baskets and trips. UK GDPR basis, retention, deletion, data sharing with the verification partner. | ASK COUNSEL | Hash on-chain, coarse location, raw files off-chain and deletable. |
| C9 | The UK Children's Code if under-18s can reach the app. | ASK COUNSEL | Age check and defaults before launch. |
| C10 | Taking payments from consumers and businesses. | ASK COUNSEL | No payments in phase 1. The app takes no payment. |
| C11 | Sanctions and prize rules for the Colosseum hackathon: entrants from listed countries are barred, and an entrant must confirm taking part breaches no employer right. | VERIFIED (official rules) | Both founders confirm before registering. |
| C12 | Open-source licence and the pending UK patent application (GB2611754.9). | ASK a patent attorney | Some licences include a patent grant. Decide before publishing code that implements the claimed method. |
| C13 | Data licences and attribution for the sources inside the app: Poore and Nemecek via Our World in Data, Agribalyse, Open Food Facts, and the Our World in Data CO2 series that sets each country's clearing target (cumulative 1850 to 2019, scaled to 2,400 Gt). | CHECK each licence and credit line | Add the required credits to the app footer before any public demo. |
