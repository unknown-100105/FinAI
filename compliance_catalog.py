"""Current Indian tax/compliance reference catalogue.

This is a source navigator and worksheet layer, not a filing/submission engine.
Time-sensitive details are linked to official portals and should be refreshed
before a real filing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ComplianceItem:
    item_id: str
    name: str
    category: str
    period: str
    purpose: str
    who_uses_it: str
    key_inputs: Tuple[str, ...]
    workflow: Tuple[str, ...]
    official_url: str
    source_name: str
    status_note: str


INCOME_TAX_URL = "https://www.incometax.gov.in/iec/foportal/"
ITR_DOWNLOAD_URL = "https://www.incometax.gov.in/iec/foportal/downloads/income-tax-returns"
GST_URL = "https://tutorial.gst.gov.in/userguide/returns/GSTR_1.htm"


ITEMS = (
    ComplianceItem(
        "itr1", "ITR-1 (Sahaj)", "Income Tax", "AY 2026-27",
        "Return for eligible resident individuals with salary/pension, one house property and specified other-income conditions.",
        "Eligible resident individual taxpayers meeting the portal's conditions.",
        ("salary/pension", "house-property income", "other income", "eligible capital gains", "TDS/AIS details"),
        ("Confirm eligibility", "Collect salary and tax statements", "Reconcile AIS/26AS", "Enter income and deductions", "Validate and submit", "Complete verification"),
        ITR_DOWNLOAD_URL, "Income Tax Department", "Use the current notified schema and eligibility rules."),
    ComplianceItem(
        "itr2", "ITR-2", "Income Tax", "AY 2026-27",
        "Return generally used by individuals/HUFs not having income from profits and gains of business or profession, subject to detailed conditions.",
        "Eligible individuals and HUFs.",
        ("salary", "house property", "capital gains", "other sources", "foreign assets/income where applicable", "AIS/26AS"),
        ("Confirm form eligibility", "Collect transaction records", "Reconcile information statements", "Compute income", "Validate", "Submit and verify"),
        ITR_DOWNLOAD_URL, "Income Tax Department", "Check the latest schema and detailed eligibility."),
    ComplianceItem(
        "itr3", "ITR-3", "Income Tax", "AY 2026-27",
        "Return for individuals/HUFs having income from profits and gains of business or profession, subject to detailed conditions.",
        "Eligible individuals/HUFs with business or professional income.",
        ("business/professional accounts", "capital gains", "other income", "tax payments", "AIS/26AS"),
        ("Determine business/profession status", "Prepare books and schedules", "Reconcile tax statements", "Compute taxable income", "Validate", "Submit and verify"),
        ITR_DOWNLOAD_URL, "Income Tax Department", "Use current notified utility/schema."),
    ComplianceItem(
        "itr4", "ITR-4 (Sugam)", "Income Tax", "AY 2026-27",
        "Return for eligible resident individuals, HUFs and firms other than LLPs using specified presumptive taxation conditions, subject to detailed eligibility.",
        "Eligible taxpayers satisfying the presumptive-taxation conditions.",
        ("presumptive business/profession details", "salary/pension", "other sources", "eligible capital-gain details", "AIS/26AS"),
        ("Confirm eligibility", "Prepare presumptive computation", "Reconcile tax statements", "Validate", "Submit and verify"),
        ITR_DOWNLOAD_URL, "Income Tax Department", "Eligibility and limits must be checked for the relevant year."),
    ComplianceItem(
        "itr5", "ITR-5", "Income Tax", "AY 2026-27",
        "Return form for entities such as firms, LLPs, AOPs, BOIs and specified persons, subject to applicable rules.",
        "Eligible non-individual taxpayers covered by the form.",
        ("financial statements", "business income", "capital gains", "tax payments", "entity details"),
        ("Identify entity type", "Collect financial data", "Compute income", "Reconcile taxes", "Validate", "Submit and verify"),
        ITR_DOWNLOAD_URL, "Income Tax Department", "Use current notified form and schema."),
    ComplianceItem(
        "itr6", "ITR-6", "Income Tax", "AY 2026-27",
        "Return for companies other than companies claiming exemption under the specified section referenced by the form.",
        "Eligible companies.",
        ("company financials", "tax audit information where applicable", "tax payments", "tax credits"),
        ("Confirm applicability", "Prepare company schedules", "Reconcile taxes", "Validate", "Submit and verify"),
        ITR_DOWNLOAD_URL, "Income Tax Department", "Use current notified form and schema."),
    ComplianceItem(
        "itr7", "ITR-7", "Income Tax", "AY 2026-27",
        "Return for persons including specified trusts, political parties and institutions covered by the form.",
        "Eligible entities covered by the form.",
        ("entity statements", "income and application details", "tax payments", "audit information where applicable"),
        ("Confirm section/form applicability", "Collect governing documents", "Prepare schedules", "Validate", "Submit and verify"),
        ITR_DOWNLOAD_URL, "Income Tax Department", "Use current notified form and schema."),
    ComplianceItem(
        "itr_u", "ITR-U (Updated Return)", "Income Tax", "Applicable years subject to law",
        "Updated return mechanism for correcting or reporting additional income subject to the governing conditions and time limits.",
        "Taxpayers meeting updated-return conditions.",
        ("original return data", "additional income", "tax already paid", "updated computation"),
        ("Check statutory eligibility and time limit", "Compute updated liability", "Complete updated-return form", "Pay applicable amounts", "Submit and verify"),
        INCOME_TAX_URL, "Income Tax Department", "Conditions, time windows and additional-tax requirements are time-sensitive."),
    ComplianceItem(
        "itr_v", "ITR-V", "Income Tax", "AY 2026-27",
        "Verification document associated with an income-tax return where the applicable verification route requires it.",
        "Taxpayers using the applicable verification workflow.",
        ("ITR acknowledgement", "verification details"),
        ("Submit return", "Generate verification", "Complete the permitted verification process", "Retain acknowledgement"),
        INCOME_TAX_URL, "Income Tax Department", "Follow the current e-filing verification workflow."),
    ComplianceItem(
        "form16", "Form 16", "TDS", "FY 2025-26 / relevant payment year",
        "Salary TDS certificate issued by the employer.",
        "Employees receiving salary with TDS reporting.",
        ("salary", "TDS deducted", "employer details", "deductions/exemptions reported"),
        ("Receive certificate", "Reconcile with AIS/26AS", "Use figures in the return", "Retain certificate"),
        INCOME_TAX_URL, "Income Tax Department", "Certificate format and availability are governed by current rules."),
    ComplianceItem(
        "form16a", "Form 16A", "TDS", "Relevant quarter",
        "TDS certificate for income other than salary.",
        "Recipients of specified non-salary payments where TDS applies.",
        ("payment nature", "gross amount", "TDS deducted", "deductor details"),
        ("Receive certificate", "Reconcile TDS credit", "Use in tax return/records", "Retain certificate"),
        INCOME_TAX_URL, "Income Tax Department", "Verify current reporting and certificate requirements."),
    ComplianceItem(
        "form26as", "Form 26AS", "Tax Information", "Current portal statement",
        "Tax-credit statement showing reported TDS/TCS and related tax information under the portal's current design.",
        "Taxpayers reviewing tax credits.",
        ("PAN-linked tax data", "TDS/TCS", "tax payments"),
        ("Login to portal", "Open tax credit statement", "Reconcile with certificates and books", "Investigate mismatches"),
        INCOME_TAX_URL, "Income Tax Department", "The portal also provides AIS; use the latest statement available."),
    ComplianceItem(
        "ais", "Annual Information Statement (AIS)", "Tax Information", "Current portal statement",
        "Information statement containing reported financial/tax information such as TDS/TCS, SFT, payments and other items shown by the portal.",
        "Taxpayers reconciling reported information.",
        ("reported transactions", "TDS/TCS", "SFT", "tax payments", "refund/demand information"),
        ("Download/view AIS", "Compare against books/bank/broker records", "Submit feedback where appropriate", "Reconcile before filing"),
        INCOME_TAX_URL, "Income Tax Department", "Information is report-based and can require reconciliation."),
    ComplianceItem(
        "15g", "Form 15G", "TDS", "Relevant financial year",
        "Declaration used by eligible taxpayers seeking non-deduction of TDS on specified receipts where statutory conditions are met.",
        "Eligible resident persons meeting the statutory conditions.",
        ("estimated total income", "specified receipt", "tax status", "declaration details"),
        ("Check eligibility", "Estimate income", "Complete declaration", "Submit to the relevant deductor"),
        INCOME_TAX_URL, "Income Tax Department", "Eligibility conditions must be checked for the relevant year."),
    ComplianceItem(
        "15h", "Form 15H", "TDS", "Relevant financial year",
        "Declaration for eligible resident senior citizens seeking non-deduction of TDS on specified receipts.",
        "Eligible resident senior citizens meeting statutory conditions.",
        ("estimated income", "specified receipt", "declaration details"),
        ("Check eligibility", "Prepare declaration", "Submit to deductor", "Retain acknowledgement"),
        INCOME_TAX_URL, "Income Tax Department", "Eligibility conditions are statutory and time-sensitive."),
    ComplianceItem(
        "10e", "Form 10E", "Income Tax Relief", "Relevant assessment year",
        "Statement of particulars for claiming relief under section 89(1) for specified receipts such as salary arrears/advance.",
        "Eligible individual taxpayers seeking section 89 relief.",
        ("arrears/advance salary", "salary details", "relief computation"),
        ("Calculate eligible relief", "Submit Form 10E", "Reflect relief in return", "Retain computation"),
        INCOME_TAX_URL, "Income Tax Department", "Use current relief and filing instructions."),
    ComplianceItem(
        "67", "Form 67", "Foreign Tax Credit", "Relevant assessment year",
        "Statement used for claiming foreign tax credit under the applicable provisions.",
        "Taxpayers claiming eligible foreign tax credit.",
        ("foreign income", "foreign tax paid", "supporting certificate", "DTAA/tax-law details"),
        ("Collect foreign tax proof", "Compute eligible credit", "Submit Form 67 within applicable requirements", "Claim credit in return"),
        INCOME_TAX_URL, "Income Tax Department", "Treat DTAA and timing requirements as current-law questions."),
    ComplianceItem(
        "gstr1", "GSTR-1", "GST", "Tax period",
        "Statement of outward supplies of goods and services for registered taxpayers required to furnish it.",
        "Applicable registered taxpayers.",
        ("invoice-level outward supplies", "credit/debit notes", "exports", "advances", "HSN/SAC summary"),
        ("Prepare invoice data", "Reconcile sales register", "Enter/upload data", "Generate summary", "File statement"),
        GST_URL, "GST Portal / CBIC", "Frequency and applicability depend on registration and current GST rules."),
    ComplianceItem(
        "gstr1a", "GSTR-1A", "GST", "Tax period",
        "Optional amendment facility described by the GST portal for correcting/adding certain outward-supply data before the relevant GSTR-3B filing.",
        "Eligible registered taxpayers using the facility.",
        ("correction records", "missed outward supplies", "GSTR-1 source data"),
        ("Review GSTR-1", "Add/amend eligible records", "Submit GSTR-1A", "Reconcile downstream data"),
        GST_URL, "GST Portal / CBIC", "Use the current portal workflow and eligibility."),
    ComplianceItem(
        "gstr3b", "GSTR-3B", "GST", "Tax period",
        "Summary GST return/statement used for reporting tax liability and other prescribed details.",
        "Applicable registered taxpayers.",
        ("outward tax liability", "input tax credit", "tax payments", "other prescribed fields"),
        ("Reconcile books and GSTR-2B/source data", "Compute liability", "Pay tax", "File GSTR-3B"),
        "https://www.gst.gov.in/", "GST Portal", "Use current rules and portal instructions."),
    ComplianceItem(
        "cmp08", "CMP-08", "GST Composition", "Tax period",
        "Statement for payment of self-assessed tax for eligible composition taxpayers.",
        "Eligible composition taxpayers.",
        ("turnover", "tax payable", "payment details"),
        ("Compute tax", "Pay through portal", "Submit statement", "Retain acknowledgement"),
        "https://tutorial.gst.gov.in/userguide/returns/", "GST Portal", "Use the current composition scheme rules."),
)


def list_items(category: str | None = None) -> List[Dict[str, object]]:
    items = ITEMS
    if category:
        category_n = category.strip().lower()
        items = tuple(item for item in items if item.category.lower() == category_n)
    return [asdict(item) for item in items]


def find_items(query: str) -> List[Dict[str, object]]:
    q = " ".join(str(query).strip().lower().split())
    if not q:
        return []
    matches = []
    for item in ITEMS:
        haystack = " ".join([
            item.item_id, item.name, item.category, item.period,
            item.purpose, item.who_uses,
        ]).lower()
        if q in haystack or any(token in haystack for token in q.split()):
            matches.append(asdict(item))
    return matches[:20]


def capital_gain_worksheet(
    buy_value: float,
    sell_value: float,
    transfer_costs: float = 0.0,
    improvement_cost: float = 0.0,
) -> Dict[str, float]:
    values = {
        "buy_value": buy_value,
        "sell_value": sell_value,
        "transfer_costs": transfer_costs,
        "improvement_cost": improvement_cost,
    }
    if values["buy_value"] < 0 or values["sell_value"] < 0 or values["transfer_costs"] < 0 or values["improvement_cost"] < 0:
        raise ValueError("Worksheet amounts must not be negative.")
    gain = sell_value - buy_value - transfer_costs - improvement_cost
    return {
        **values,
        "computed_gain_before_tax": gain,
    }


def metadata() -> Dict[str, str]:
    return {
        "income_tax_source": INCOME_TAX_URL,
        "itr_download_source": ITR_DOWNLOAD_URL,
        "gst_source": "https://www.gst.gov.in/",
        "note": "Use this module as a navigator/worksheet. Official filing portals, current rules and taxpayer-specific eligibility remain authoritative.",
    }
