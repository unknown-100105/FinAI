"""Official-source finance resources, schemes and form templates for FinAI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Resource:
    resource_id: str
    name: str
    category: str
    audience: Tuple[str, ...]
    official_url: str
    authority: str
    description: str
    form_title: str
    form_fields: Tuple[str, ...]
    current_source: bool = True


INDIAPOST = "https://www.indiapost.gov.in/Financial/Pages/Content/Post-Office-Saving-Schemes.aspx?facet=amp"
SEBI_EDU = "https://investor.sebi.gov.in/iematerial.html"
ITR_DOWNLOADS = "https://www.incometax.gov.in/iec/foportal/downloads/income-tax-returns"
INCOME_TAX = "https://www.incometax.gov.in/iec/foportal/"
RBI_RETAIL = "https://rbiretaildirect.org.in/"
RBI_LRS = "https://www.rbi.org.in/scripts/notificationuser.aspx?id=10192"
RBI_FAQ_RETAIL = "https://www.rbi.org.in/scripts/faqview.aspx/faqview.aspx/scripts/FAQView.aspx?Id=145"
PFRDA_NPS = "https://www.pfrda.org.in/en/schemes/national-pension-system/nps-for-all-citizen-models"
PFRDA_APY = "https://www.pfrda.org.in/en/schemes/atal-pension-yojana"
EPFO = "https://www.epfindia.gov.in/site_en/index.php"
EPF_SCHEME = "https://www.epfindia.gov.in/site_docs/PDFs/Downloads_PDFs/EPFScheme.pdf"
PMJDY = "https://www.pmjdy.gov.in/scheme"
GST = "https://www.gst.gov.in/"
MCA = "https://mca.gov.in/content/mca/global/en/home.html"
DEA = "https://dea.gov.in/budget-division/475"
FIU = "https://fiuindia.gov.in/files/downloads/downloads.html"
NSE = "https://www.nseindia.com/"
BSE = "https://www.bseindia.com/"
RBI = "https://www.rbi.org.in/"
SEBI = "https://www.sebi.gov.in/"
IRDAI = "https://irdai.gov.in/"
NISM = "https://www.nism.ac.in/"


RESOURCES = (
    Resource("ppf", "Public Provident Fund (PPF)", "Government Savings", ("Resident",), INDIAPOST, "Department of Posts",
             "Long-term small-savings account with notified interest and scheme-specific withdrawal rules.",
             "PPF account planning worksheet", ("full_name", "pan", "address", "date_of_birth", "deposit_amount", "nominee", "bank_account")),
    Resource("nsc", "National Savings Certificate (NSC)", "Government Savings", ("Resident",), INDIAPOST, "Department of Posts",
             "Five-year small-savings certificate with notified interest and maturity rules.",
             "NSC purchase worksheet", ("full_name", "pan", "address", "investment_amount", "nominee")),
    Resource("kvp", "Kisan Vikas Patra (KVP)", "Government Savings", ("Resident",), INDIAPOST, "Department of Posts",
             "Government small-savings certificate whose maturity period and rate are notified.",
             "KVP purchase worksheet", ("full_name", "pan", "address", "investment_amount", "nominee")),
    Resource("scss", "Senior Citizens' Savings Scheme (SCSS)", "Government Savings", ("Eligible Senior Citizen",), INDIAPOST, "Department of Posts",
             "Small-savings scheme for eligible senior citizens with scheduled interest payments.",
             "SCSS account worksheet", ("full_name", "pan", "date_of_birth", "address", "investment_amount", "nominee", "bank_account")),
    Resource("mis", "National Savings Monthly Income Account (MIS)", "Government Savings", ("Resident",), INDIAPOST, "Department of Posts",
             "Small-savings account designed for periodic interest income under notified conditions.",
             "MIS account worksheet", ("full_name", "pan", "address", "investment_amount", "nominee", "bank_account")),
    Resource("ssy", "Sukanya Samriddhi Account (SSA)", "Government Savings", ("Eligible Girl Child / Guardian",), "https://www.indiapost.gov.in/VAS/pages/pmodashboard/sukanyasamriddhiaccount.aspx", "Department of Posts",
             "Government small-savings account for an eligible girl child under the scheme rules.",
             "Sukanya Samriddhi application worksheet", ("girl_child_name", "girl_child_dob", "guardian_name", "pan", "address", "deposit_amount", "bank_account")),
    Resource("rd", "National Savings Recurring Deposit (RD)", "Government Savings", ("Resident",), INDIAPOST, "Department of Posts",
             "Recurring-deposit scheme with scheduled contributions and notified interest.",
             "RD account worksheet", ("full_name", "pan", "address", "monthly_deposit", "tenure", "nominee", "bank_account")),
    Resource("td", "National Savings Time Deposit (TD)", "Government Savings", ("Resident",), INDIAPOST, "Department of Posts",
             "Time-deposit scheme with notified tenure/rate options.",
             "TD account worksheet", ("full_name", "pan", "address", "deposit_amount", "tenure", "nominee", "bank_account")),
    Resource("posb", "Post Office Savings Account", "Government Savings", ("Resident",), INDIAPOST, "Department of Posts",
             "Savings account offered through the Department of Posts.",
             "Post Office savings account worksheet", ("full_name", "pan", "address", "mobile", "email", "nominee", "bank_account")),
    Resource("nps", "National Pension System (NPS)", "Retirement", ("Resident", "NRI", "OCI"), PFRDA_NPS, "PFRDA",
             "Retirement-oriented regulated pension account with investment choices and exit rules.",
             "NPS onboarding worksheet", ("full_name", "pan", "date_of_birth", "citizenship_status", "address", "mobile", "nominee", "bank_account")),
    Resource("apy", "Atal Pension Yojana (APY)", "Retirement", ("Resident",), PFRDA_APY, "PFRDA",
             "Government-backed pension scheme administered through the prescribed banking ecosystem.",
             "APY enrolment worksheet", ("full_name", "date_of_birth", "mobile", "bank_account", "nominee")),
    Resource("epf", "Employees' Provident Fund (EPF)", "Retirement", ("Eligible Employee",), EPF_SCHEME, "EPFO",
             "Provident-fund scheme administered by EPFO under the applicable law.",
             "EPF service worksheet", ("uan", "full_name", "employer", "mobile", "nominee", "bank_account")),
    Resource("eps", "Employees' Pension Scheme (EPS)", "Retirement", ("Eligible Employee",), EPFO, "EPFO",
             "Pension scheme administered by EPFO.",
             "EPS service worksheet", ("uan", "full_name", "date_of_birth", "service_details", "nominee")),
    Resource("edli", "Employees' Deposit Linked Insurance (EDLI)", "Insurance", ("Eligible Employee / Nominee",), EPFO, "EPFO",
             "Deposit-linked insurance scheme administered by EPFO.",
             "EDLI claim-preparation worksheet", ("uan", "member_name", "employee_details", "nominee", "claimant_details", "supporting_documents")),
    Resource("rbi_retail_direct", "RBI Retail Direct", "Government Securities", ("Resident", "Eligible Non-Resident"), RBI_RETAIL, "Reserve Bank of India",
             "Official retail access route for specified government securities.",
             "RBI Retail Direct account checklist", ("full_name", "pan", "mobile", "email", "address", "bank_account", "kyc_document")),
    Resource("lrs", "Liberalised Remittance Scheme (LRS)", "Overseas Investment", ("Resident Individual",), RBI_LRS, "Reserve Bank of India",
             "Framework for permitted resident-individual foreign exchange remittances within the prescribed annual limit and conditions.",
             "LRS remittance planning worksheet", ("pan", "purpose", "amount_usd", "beneficiary", "authorised_dealer", "form_a2_reference")),
    Resource("pmjdy", "Pradhan Mantri Jan-Dhan Yojana (PMJDY)", "Government Financial Inclusion", ("Resident",), PMJDY, "Department of Financial Services",
             "Financial-inclusion programme providing access to basic banking, remittances, credit, insurance and pension services.",
             "PMJDY account worksheet", ("full_name", "date_of_birth", "address", "identity_document", "mobile", "nominee")),
    Resource("itr1", "ITR-1 (Sahaj)", "Income Tax", ("Eligible Resident Individual",), ITR_DOWNLOADS, "Income Tax Department",
             "Income-tax return for the taxpayer categories and income sources specified by the current AY 2026-27 guidance.",
             "ITR-1 preparation worksheet", ("pan", "aadhaar", "salary", "house_property", "other_sources", "eligible_112a_ltcg", "tds", "deductions")),
    Resource("itr2", "ITR-2", "Income Tax", ("Individual", "HUF"), ITR_DOWNLOADS, "Income Tax Department",
             "Return for individuals/HUFs not having business/profession income and not eligible for ITR-1.",
             "ITR-2 preparation worksheet", ("pan", "salary", "house_property", "capital_gains", "other_sources", "foreign_assets", "tds", "deductions")),
    Resource("itr3", "ITR-3", "Income Tax", ("Individual", "HUF"), ITR_DOWNLOADS, "Income Tax Department",
             "Return covering business/professional income and other applicable income heads.",
             "ITR-3 preparation worksheet", ("pan", "business_income", "professional_income", "salary", "capital_gains", "other_sources", "balance_sheet", "profit_loss", "tds")),
    Resource("itr4", "ITR-4", "Income Tax", ("Eligible Resident Individual", "HUF", "Firm"), ITR_DOWNLOADS, "Income Tax Department",
             "Presumptive-tax return for specified eligible taxpayers.",
             "ITR-4 preparation worksheet", ("pan", "presumptive_business", "presumptive_profession", "salary", "house_property", "other_sources", "tds")),
    Resource("itr5", "ITR-5", "Income Tax", ("Firm", "LLP", "AOP", "BOI"), ITR_DOWNLOADS, "Income Tax Department",
             "Return for specified non-individual taxpayers.",
             "ITR-5 preparation worksheet", ("pan", "entity_name", "entity_type", "financials", "income", "tax_payments", "audit_data")),
    Resource("itr6", "ITR-6", "Income Tax", ("Company",), ITR_DOWNLOADS, "Income Tax Department",
             "Company income-tax return for entities covered by the form.",
             "ITR-6 preparation worksheet", ("pan", "cin", "company_name", "financials", "income", "tax_payments", "audit_data")),
    Resource("itr7", "ITR-7", "Income Tax", ("Trust", "Institution", "Specified Entities"), ITR_DOWNLOADS, "Income Tax Department",
             "Return for specified entities including trusts and institutions covered by the form.",
             "ITR-7 preparation worksheet", ("pan", "entity_name", "registration", "income", "application_of_income", "audit_data", "tax_payments")),
    Resource("itr_u", "ITR-U (Updated Return)", "Income Tax", ("Eligible Taxpayer",), ITR_DOWNLOADS, "Income Tax Department",
             "Updated-return mechanism subject to statutory eligibility and current time limits.",
             "ITR-U amendment worksheet", ("pan", "original_return", "additional_income", "tax_paid", "updated_computation")),
    Resource("form16", "Form 16", "Tax / TDS", ("Salary Recipient",), INCOME_TAX, "Income Tax Department",
             "Salary TDS certificate.",
             "Form 16 reconciliation worksheet", ("pan", "employer", "salary", "tds", "deductions")),
    Resource("form16a", "Form 16A", "Tax / TDS", ("Income Recipient",), INCOME_TAX, "Income Tax Department",
             "TDS certificate for specified non-salary payments.",
             "Form 16A reconciliation worksheet", ("pan", "deductor", "payment_nature", "gross_amount", "tds")),
    Resource("ais", "Annual Information Statement (AIS)", "Tax Information", ("Taxpayer",), INCOME_TAX, "Income Tax Department",
             "Reported financial and tax information for reconciliation before filing.",
             "AIS reconciliation worksheet", ("pan", "financial_year", "reported_income", "tds_tcs", "sft", "tax_payments", "mismatch_notes")),
    Resource("form26as", "Form 26AS", "Tax Information", ("Taxpayer",), INCOME_TAX, "Income Tax Department",
             "Tax-credit statement for reconciliation with return data.",
             "26AS reconciliation worksheet", ("pan", "financial_year", "tds", "tcs", "tax_paid", "refund", "mismatch_notes")),
    Resource("form67", "Form 67", "Foreign Tax Credit", ("Eligible Taxpayer",), INCOME_TAX, "Income Tax Department",
             "Statement used for claiming eligible foreign-tax credit.",
             "Form 67 preparation worksheet", ("pan", "foreign_income", "foreign_tax_paid", "country", "tax_certificate", "credit_claim")),
    Resource("form10e", "Form 10E", "Income Tax Relief", ("Eligible Taxpayer",), INCOME_TAX, "Income Tax Department",
             "Statement used with specified relief claims such as salary arrears under section 89(1).",
             "Form 10E worksheet", ("pan", "salary_current_year", "salary_arrears", "relief_computation")),
    Resource("form10iea", "Form 10-IEA", "Income Tax", ("Eligible Business / Profession Taxpayer",), INCOME_TAX, "Income Tax Department",
             "Current portal form used for specified tax-regime options for eligible taxpayers with business/professional income.",
             "Form 10-IEA worksheet", ("pan", "assessment_year", "business_profession_status", "regime_option", "acknowledgement")),
    Resource("gstr1", "GSTR-1", "GST", ("Registered Taxpayer",), GST, "GST Portal",
             "Statement of outward supplies for applicable registered taxpayers.",
             "GSTR-1 preparation worksheet", ("gstin", "tax_period", "invoices", "credit_debit_notes", "exports", "hsn_summary")),
    Resource("gstr3b", "GSTR-3B", "GST", ("Registered Taxpayer",), GST, "GST Portal",
             "Summary GST return/statement for reporting liability and eligible input-tax credit.",
             "GSTR-3B preparation worksheet", ("gstin", "tax_period", "outward_tax", "input_tax_credit", "tax_paid", "interest")),
    Resource("mca_spice", "MCA SPICe+ / Company Incorporation", "Corporate Compliance", ("Promoter", "Professional"), MCA, "Ministry of Corporate Affairs",
             "On-screen company incorporation workflow with linked MCA filings.",
             "SPICe+ planning worksheet", ("proposed_name", "company_type", "registered_office", "subscribers", "directors", "capital", "objects", "attachments")),
    Resource("sebi_education", "SEBI Investor Education Materials", "Study", ("Student", "Investor"), SEBI_EDU, "SEBI",
             "Official reading material covering securities markets, KYC, IPOs, mutual funds, REITs, InvITs, ETFs, NRI investing, derivatives and investor protection."),
             "Study-session worksheet", ("topic", "learning_goal", "notes", "questions", "revision_date")),
    Resource("rbi_retail_faq", "RBI Retail Direct FAQ", "Study", ("Student", "Investor"), RBI_FAQ_RETAIL, "Reserve Bank of India",
             "Official FAQ covering government securities, account opening, auctions, secondary-market transactions and related operational questions.",
             "Study-session worksheet", ("topic", "learning_goal", "notes", "questions", "revision_date")),
    Resource("nism", "NISM Learning Resources", "Study", ("Student", "Investor", "Professional"), NISM, "National Institute of Securities Markets",
             "Official securities-market education and certification ecosystem.",
             "Study-session worksheet", ("module", "learning_goal", "notes", "questions", "revision_date")),
    Resource("irda", "IRDAI Insurance Knowledge", "Study", ("Student", "Policyholder"), IRDAI, "IRDAI",
             "Official insurance regulator resources and regulations.",
             "Study-session worksheet", ("product", "learning_goal", "notes", "questions", "revision_date")),
)


def list_resources(category: Optional[str] = None) -> List[Dict[str, object]]:
    items = RESOURCES
    if category:
        normalized = category.strip().lower()
        items = tuple(item for item in items if item.category.lower() == normalized)
    return [asdict(item) for item in items]


def search_resources(query: str) -> List[Dict[str, object]]:
    normalized = " ".join(str(query).strip().lower().split())
    if not normalized:
        return []
    scored = []
    for item in RESOURCES:
        text = " ".join((item.resource_id, item.name, item.category, item.authority, item.description, item.form_title)).lower()
        score = (10 if normalized in text else 0) + sum(2 for token in normalized.split() if len(token) >= 3 and token in text)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].resource_id))
    return [asdict(item) for _, item in scored[:40]]


def build_blank_form(resource_id: str) -> Dict[str, object]:
    resource = next((item for item in RESOURCES if item.resource_id == resource_id), None)
    if resource is None:
        raise KeyError(f"Unknown resource: {resource_id}")
    return {
        "resource_id": resource.resource_id,
        "form_title": resource.form_title,
        "authority": resource.authority,
        "official_url": resource.official_url,
        "fields": list(resource.form_fields),
        "values": {field: "" for field in resource.form_fields},
        "draft_status": "BLANK",
    }
