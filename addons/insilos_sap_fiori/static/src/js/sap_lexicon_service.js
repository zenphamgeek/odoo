import { translatedTermsGlobal } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

// =============================================================================
// SAP Enterprise Lexicon Dictionary (Client-Side Global Terminology)
// =============================================================================
export const SAP_LEXICON_TERMS = {
    // Sales & Distribution (SD)
    "Quotations": "SD Quotations",
    "Quotation": "SD Quotation",
    "Sales Orders": "SD Sales Orders",
    "Sales Order": "SD Sales Order",
    "Sales Team": "Sales Organization",
    "Sales Teams": "Sales Organizations",
    
    // Master Data & Business Partner (BP)
    "Customers": "Business Partners (Customers)",
    "Customer": "Business Partner (Customer)",
    "Vendors": "Business Partners (Suppliers)",
    "Vendor": "Business Partner (Supplier)",
    "Contacts": "Business Partners (BP)",
    "Contact": "Business Partner",
    "Contact Name": "Business Partner Name",
    
    // Materials Management (MM)
    "Products": "Material Master (MM)",
    "Product": "Material Master",
    "Product Variants": "Material Variants",
    "Product Variant": "Material Variant",
    "Purchase Orders": "MM Purchase Orders",
    "Purchase Order": "MM Purchase Order",
    "Requests for Quotation": "Vendor RFQs",
    "Request for Quotation": "Vendor RFQ",
    
    // Financial Accounting & Controlling (FI/CO)
    "Invoices": "Customer Billing Documents",
    "Invoice": "Customer Billing Document",
    "Bills": "Vendor Invoices (FI-AP)",
    "Bill": "Vendor Invoice (FI-AP)",
    "Journal Entries": "FI Accounting Documents",
    "Journal Entry": "FI Accounting Document",
    "Journal Items": "G/L Line Items",
    "Chart of Accounts": "Chart of Accounts (COA)",
    "Analytic Accounts": "Cost Centers / Profit Centers",
    "Analytic Account": "Cost Center / Profit Center",
    
    // Inventory & Logistics (MM-IM)
    "Delivery Orders": "Outbound Deliveries / Goods Issue",
    "Delivery Order": "Outbound Delivery",
    "Receipts": "Inbound Deliveries / Goods Receipt",
    "Receipt": "Inbound Delivery",
    "Inventory Adjustments": "Physical Inventory Adjustments",
    "Warehouses": "Plants / Distribution Centers",
    "Warehouse": "Plant / Distribution Center",
    "Locations": "Storage Locations (SLoc)",
    "Location": "Storage Location (SLoc)",
    
    // Production Planning (PP)
    "Manufacturing Orders": "Production Orders (PP)",
    "Manufacturing Order": "Production Order (PP)",
    "Work Centers": "Work Centers / Routing Resources",
    "Work Center": "Work Center / Resource",
    "Bills of Materials": "Production Bills of Materials",
    "Bill of Materials": "Production BOM",
};

// Seed global translation table directly
Object.assign(translatedTermsGlobal, SAP_LEXICON_TERMS);

export const sapLexiconService = {
    start() {
        // Enforce lexicon registration on startup
        Object.assign(translatedTermsGlobal, SAP_LEXICON_TERMS);
        return {
            getTerm(term) {
                return SAP_LEXICON_TERMS[term] || term;
            },
            lexicon: SAP_LEXICON_TERMS,
        };
    },
};

registry.category("services").add("sap_lexicon", sapLexiconService);
