"""Global market/investment registry for research and eligibility checks."""
COUNTRIES=[
("India","IN","INR","NSE/BSE","Domestic"),("United States","US","USD","NYSE/Nasdaq","North America"),("Canada","CA","CAD","TSX","North America"),
("United Kingdom","GB","GBP","LSE","Europe"),("Germany","DE","EUR","Xetra","Europe"),("France","FR","EUR","Euronext Paris","Europe"),("Switzerland","CH","CHF","SIX","Europe"),("Netherlands","NL","EUR","Euronext Amsterdam","Europe"),("Italy","IT","EUR","Borsa Italiana","Europe"),("Spain","ES","EUR","BME","Europe"),("Ireland","IE","EUR","Euronext Dublin","Europe"),("Norway","NO","NOK","Oslo Bors","Europe"),("Sweden","SE","SEK","Nasdaq Stockholm","Europe"),("Denmark","DK","DKK","Nasdaq Copenhagen","Europe"),("Finland","FI","EUR","Nasdaq Helsinki","Europe"),
("Japan","JP","JPY","Tokyo Stock Exchange","Asia-Pacific"),("South Korea","KR","KRW","Korea Exchange","Asia-Pacific"),("China","CN","CNY","Shanghai/Shenzhen","Asia-Pacific"),("Hong Kong","HK","HKD","HKEX","Asia-Pacific"),("Taiwan","TW","TWD","Taiwan Stock Exchange","Asia-Pacific"),("Singapore","SG","SGD","SGX","Asia-Pacific"),("Australia","AU","AUD","ASX","Asia-Pacific"),("New Zealand","NZ","NZD","NZX","Asia-Pacific"),("Indonesia","ID","IDR","IDX","Asia-Pacific"),("Malaysia","MY","MYR","Bursa Malaysia","Asia-Pacific"),("Thailand","TH","THB","SET","Asia-Pacific"),("Vietnam","VN","VND","HOSE/HNX","Asia-Pacific"),("Philippines","PH","PHP","PSE","Asia-Pacific"),
("Israel","IL","ILS","TASE","Middle East"),("United Arab Emirates","AE","AED","ADX/DFM","Middle East"),("Saudi Arabia","SA","SAR","Tadawul","Middle East"),("Turkey","TR","TRY","Borsa Istanbul","Europe/Middle East"),
("Brazil","BR","BRL","B3","Latin America"),("Mexico","MX","MXN","BMV","Latin America"),("Argentina","AR","ARS","BYMA","Latin America"),("Chile","CL","CLP","Santiago","Latin America"),("Colombia","CO","COP","BVC","Latin America"),
("South Africa","ZA","ZAR","JSE","Africa"),("Egypt","EG","EGP","EGX","Africa"),("Nigeria","NG","NGN","NGX","Africa"),("Kenya","KE","KES","NSE Kenya","Africa"),
]

OFFICIAL_MARKET_SOURCES = {
"IN":"https://www.nseindia.com/","US":"https://www.sec.gov/","CA":"https://www.ciro.ca/","GB":"https://www.fca.org.uk/",
"DE":"https://www.bafin.de/","FR":"https://www.amf-france.org/","CH":"https://www.finma.ch/","NL":"https://www.afm.nl/",
"IT":"https://www.consob.it/","ES":"https://www.cnmv.es/","IE":"https://www.centralbank.ie/","NO":"https://www.finanstilsynet.no/",
"SE":"https://www.fi.se/","DK":"https://www.dfsa.dk/","FI":"https://www.finanssivalvonta.fi/","JP":"https://www.fsa.go.jp/",
"KR":"https://www.fsc.go.kr/","CN":"https://www.csrc.gov.cn/","HK":"https://www.sfc.hk/","TW":"https://www.sfb.gov.tw/",
"SG":"https://www.mas.gov.sg/","AU":"https://asic.gov.au/","NZ":"https://www.fma.govt.nz/","ID":"https://www.ojk.go.id/",
"MY":"https://www.sc.com.my/","TH":"https://www.sec.or.th/","VN":"https://www.ssc.gov.vn/","PH":"https://www.sec.gov.ph/",
"IL":"https://www.isa.gov.il/","AE":"https://sca.gov.ae/","SA":"https://cma.org.sa/","TR":"https://www.spk.gov.tr/",
"BR":"https://www.gov.br/cvm/","MX":"https://www.gob.mx/cnbv","AR":"https://www.argentina.gob.ar/cnv",
"CL":"https://www.cmfchile.cl/","CO":"https://www.superfinanciera.gov.co/","ZA":"https://www.fsca.co.za/",
"EG":"https://fra.gov.eg/","NG":"https://sec.gov.ng/","KE":"https://www.cma.or.ke/",
}

ASSET_CLASSES=[
{"id":"equity","label":"Equities","description":"Listed company shares and eligible depositary receipts."},{"id":"etf","label":"ETFs","description":"Exchange-traded funds subject to venue and investor-access rules."},{"id":"index","label":"Indices","description":"Benchmarks for research; an index is not necessarily investable."},{"id":"government_bond","label":"Government bonds","description":"Sovereign bills and bonds subject to local and Indian rules."},{"id":"corporate_bond","label":"Corporate bonds","description":"Issuer debt securities subject to intermediary and market-access rules."},{"id":"deposit","label":"Bank deposits / FD","description":"Foreign time deposits; residency, KYC, FX and repatriation rules vary."},{"id":"fund","label":"Funds","description":"Mutual funds and other pooled investment vehicles."},{"id":"reit","label":"REITs","description":"Listed real-estate investment vehicles where available."},{"id":"commodity","label":"Commodities","description":"Gold, energy, agricultural and industrial commodity exposures."},{"id":"forex","label":"Currencies","description":"FX data for research; retail access is jurisdiction-dependent."},
]
SPECIAL={
"AR":("CONDITIONAL","Argentine fixed-term deposits exist, but non-resident access, foreign-exchange controls, repatriation and bank KYC must be verified for the specific bank.","https://www.bcra.gob.ar/"),
"US":("CONDITIONAL","US securities may be accessible through eligible intermediaries; instrument, broker, tax and Indian overseas-investment rules must be checked.","https://www.treasury.gov/"),
"GB":("CONDITIONAL","UK securities and government debt can be researched globally; intermediary, tax and Indian overseas-investment requirements remain instrument-specific.","https://www.dmo.gov.uk/"),
"JP":("CONDITIONAL","Japanese securities and government debt may have international access routes; verify intermediary and tax requirements.","https://www.mof.go.jp/"),
"SG":("CONDITIONAL","Singapore securities and government securities have foreign-investor routes for some instruments; verify account, tax and Indian rules.","https://www.mas.gov.sg/"),
}
def list_global_markets():
    return [{"country":n,"country_code":c,"currency":cur,"primary_market":m,"region":r,"asset_classes":[a["id"] for a in ASSET_CLASSES],"official_source_url":OFFICIAL_MARKET_SOURCES.get(c)} for n,c,cur,m,r in COUNTRIES]
def global_catalog():
    return {"countries":list_global_markets(),"asset_classes":ASSET_CLASSES,"investor_profile":"Indian resident individual","scope_note":"Country coverage is a research registry; instrument-level eligibility must be verified before execution."}
ASSET_ACCESS_GUIDANCE = {
    "equity": {
        "label": "Equities",
        "summary": "Listed shares and related equity instruments. FinAI treats access as instrument- and intermediary-specific rather than assuming blanket eligibility.",
        "checks": ["Local exchange/investor eligibility", "Indian FEMA / overseas-investment rules", "Broker/KYC onboarding", "Currency conversion and repatriation", "Foreign withholding and Indian tax/reporting"],
    },
    "etf": {
        "label": "ETFs",
        "summary": "Exchange-traded funds. The exact ETF, listing venue, broker route and Indian overseas-investment treatment must be checked before any transaction.",
        "checks": ["ETF listing and distribution eligibility", "Indian FEMA / overseas-investment rules", "Broker/KYC onboarding", "Currency conversion and repatriation", "Foreign withholding and Indian tax/reporting"],
    },
    "index": {
        "label": "Indices",
        "summary": "Market benchmarks for research. An index itself is not necessarily a directly investable instrument.",
        "checks": ["Confirm whether the intended product tracks the index", "Local product/access rules", "Broker/KYC requirements", "FX and repatriation where applicable", "Tax/reporting treatment"],
    },
    "government_bond": {
        "label": "Government bonds",
        "summary": "Sovereign bills and bonds. Availability depends on the specific government security, investor category, settlement route and intermediary.",
        "checks": ["Specific security/investor eligibility", "Local sovereign-market access rules", "Indian FEMA / overseas-investment rules", "Settlement, FX and repatriation", "Tax/withholding treatment"],
    },
    "corporate_bond": {
        "label": "Corporate bonds",
        "summary": "Corporate debt securities. Access can depend on the issue, venue, investor classification and intermediary.",
        "checks": ["Issue and investor eligibility", "Venue/intermediary onboarding", "Indian FEMA / overseas-investment rules", "FX and settlement", "Tax/withholding treatment"],
    },
    "deposit": {
        "label": "Bank deposits / FD",
        "summary": "Foreign bank deposits or time deposits. Eligibility depends on the bank, residency rules, KYC, currency controls and repatriation conditions.",
        "checks": ["Bank-specific non-resident eligibility", "KYC/account-opening requirements", "Currency and FX controls", "Repatriation rules", "Tax/reporting treatment"],
    },
    "fund": {
        "label": "Funds",
        "summary": "Pooled investment vehicles such as mutual funds or comparable funds. The product, distribution route and investor eligibility must be verified.",
        "checks": ["Fund/product availability", "Local investor eligibility", "KYC and intermediary onboarding", "Indian FEMA / overseas-investment rules", "Tax/withholding treatment"],
    },
    "reit": {
        "label": "REITs",
        "summary": "Listed real-estate investment vehicles where available. Access depends on the listed product and investor route.",
        "checks": ["Specific REIT listing/investor eligibility", "Broker/KYC onboarding", "Indian FEMA / overseas-investment rules", "FX and repatriation", "Tax/reporting treatment"],
    },
    "commodity": {
        "label": "Commodities",
        "summary": "Commodity exposure can mean listed products, funds, derivatives or physical exposure; the actual instrument must be identified before eligibility is assessed.",
        "checks": ["Identify exact commodity product", "Local trading/ownership rules", "Broker/KYC requirements", "Indian FEMA / overseas-investment rules where relevant", "Tax/reporting treatment"],
    },
    "forex": {
        "label": "Currencies",
        "summary": "Currency markets are highly jurisdiction-dependent. FinAI treats FX as a research category until the exact permitted product and intermediary route are verified.",
        "checks": ["Identify exact FX product", "Retail/institutional access rules", "Broker/KYC requirements", "Indian FEMA / RBI rules where relevant", "Tax/reporting treatment"],
    },
}


def eligibility(country_code:str,asset_class:str):
    code=country_code.upper(); country=next((x for x in COUNTRIES if x[1]==code),None)
    if not country: raise ValueError("Unknown country code.")
    key = str(asset_class).strip().lower()
    if key not in {item["id"] for item in ASSET_CLASSES}:
        raise ValueError("Unknown asset class.")
    guidance = ASSET_ACCESS_GUIDANCE[key]
    if code == "IN":
        status = "DOMESTIC"
        summary = f"{guidance['summary']} For India, the domestic route still depends on the specific product and applicable rules."
    else:
        special = SPECIAL.get(code)
        status = special[0] if special else "CONDITIONAL"
        country_note = special[1] if special else "Country-specific access and regulatory conditions must be verified for the selected instrument."
        summary = f"{guidance['summary']} {country_note}"
    common_checks = list(guidance["checks"])
    return {
        "country": country[0],
        "country_code": code,
        "asset_class": key,
        "asset_class_label": guidance["label"],
        "investor": "Indian resident individual",
        "status": status,
        "summary": summary,
        "checks": common_checks,
        "verification_sources": [u for u in (SPECIAL.get(code, (None, None, None))[2], OFFICIAL_MARKET_SOURCES.get(code)) if u],
    }
