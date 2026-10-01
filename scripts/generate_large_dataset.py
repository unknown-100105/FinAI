import json
import random
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TAXONOMY_FILE = PROJECT_ROOT / "data" / "intent_taxonomy.json"
TOOL_MAP_FILE = PROJECT_ROOT / "data" / "intent_tool_map.json"
SEED_FILE = PROJECT_ROOT / "data" / "financial_intents.jsonl"

OUTPUT_DIR = PROJECT_ROOT / "data" / "large"
OUTPUT_FILE = OUTPUT_DIR / "financial_20k.jsonl"

SEED = 42
EXAMPLES_PER_LANGUAGE_INTENT = 80

random.seed(SEED)


# ============================================================
# Localized topic phrases
# ============================================================

TOPICS = {
    "PAYMENT_FAILED": {
        "en": "a failed payment",
        "ta": "தோல்வியடைந்த பணம் செலுத்துதல்",
        "te": "విఫలమైన చెల్లింపు",
        "kn": "ವಿಫಲವಾದ ಪಾವತಿ",
        "ml": "പരാജയപ്പെട്ട പേയ്‌മെന്റ്"
    },
    "PAYMENT_PENDING": {
        "en": "a pending payment",
        "ta": "நிலுவையில் உள்ள பணம் செலுத்துதல்",
        "te": "పెండింగ్‌లో ఉన్న చెల్లింపు",
        "kn": "ಬಾಕಿಯಿರುವ ಪಾವತಿ",
        "ml": "പെൻഡിംഗിലുള്ള പേയ്‌മെന്റ്"
    },
    "PAYMENT_SUCCESS": {
        "en": "whether my payment was successful",
        "ta": "எனது பணம் செலுத்துதல் வெற்றிகரமாக நடந்ததா என்பது",
        "te": "నా చెల్లింపు విజయవంతమైందో లేదో",
        "kn": "ನನ್ನ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆಯೇ ಎಂಬುದು",
        "ml": "എന്റെ പേയ്‌മെന്റ് വിജയിച്ചോ എന്നത്"
    },
    "MERCHANT_NOT_CREDITED": {
        "en": "a merchant not receiving my payment",
        "ta": "வியாபாரிக்கு பணம் கிடைக்காதது",
        "te": "వ్యాపారికి చెల్లింపు అందకపోవడం",
        "kn": "ವ್ಯಾಪಾರಿಗೆ ಪಾವತಿ ತಲುಪದಿರುವುದು",
        "ml": "വ്യാപാരിക്ക് പേയ്‌മെന്റ് ലഭിക്കാത്തത്"
    },
    "WRONG_AMOUNT": {
        "en": "an incorrect transaction amount",
        "ta": "தவறான பரிவர்த்தனை தொகை",
        "te": "తప్పుగా உள்ள లావాదేవీ మొత్తం",
        "kn": "ತಪ್ಪಾದ ವಹಿವಾಟಿನ ಮೊತ್ತ",
        "ml": "തെറ്റായ ഇടപാട് തുക"
    },
    "DUPLICATE_TRANSACTION": {
        "en": "a duplicate transaction",
        "ta": "இரண்டு முறை நடந்த பரிவர்த்தனை",
        "te": "రెండుసార్లు జరిగిన లావాదేవీ",
        "kn": "ಎರಡು ಬಾರಿ ನಡೆದ ವಹಿವಾಟು",
        "ml": "രണ്ടുതവണ നടന്ന ഇടപാട്"
    },
    "TRANSACTION_REVERSED": {
        "en": "a reversed transaction",
        "ta": "திரும்பப்பெறப்பட்ட பரிவர்த்தனை",
        "te": "రివర్స్ అయిన లావాదేవీ",
        "kn": "ರಿವರ್ಸ್ ಆದ ವಹಿವಾಟು",
        "ml": "റിവേഴ്സ് ചെയ്ത ഇടപാട്"
    },
    "PAYMENT_CANCEL_REQUEST": {
        "en": "cancelling a payment",
        "ta": "பணம் செலுத்துதலை ரத்து செய்வது",
        "te": "చెల్లింపును రద్దు చేయడం",
        "kn": "ಪಾವತಿಯನ್ನು ರದ್ದುಪಡಿಸುವುದು",
        "ml": "പേയ്‌മെന്റ് റദ്ദാക്കുന്നത്"
    },
    "PAYMENT_LIMIT": {
        "en": "the payment limit",
        "ta": "பணம் செலுத்தும் வரம்பு",
        "te": "చెల్లింపు పరిమితి",
        "kn": "ಪಾವತಿ ಮಿತಿ",
        "ml": "പേയ്‌മെന്റ് പരിധി"
    },
    "LIMIT_QUERY": {
        "en": "my transaction limit",
        "ta": "எனது பரிவர்த்தனை வரம்பு",
        "te": "నా లావాదేవీ పరిమితి",
        "kn": "ನನ್ನ ವಹಿವಾಟಿನ ಮಿತಿ",
        "ml": "എന്റെ ഇടപാട് പരിധി"
    },

    "UPI_PAYMENT_FAILED": {
        "en": "a failed UPI payment",
        "ta": "தோல்வியடைந்த UPI பணம் செலுத்துதல்",
        "te": "విఫలమైన UPI చెల్లింపు",
        "kn": "ವಿಫಲವಾದ UPI ಪಾವತಿ",
        "ml": "പരാജയപ്പെട്ട UPI പേയ്‌മെന്റ്"
    },
    "UPI_PENDING": {
        "en": "a pending UPI transaction",
        "ta": "நிலுவையில் உள்ள UPI பரிவர்த்தனை",
        "te": "పెండింగ్‌లో ఉన్న UPI లావాదేవీ",
        "kn": "ಬಾಕಿಯಿರುವ UPI ವಹಿವಾಟು",
        "ml": "പെൻഡിംഗിലുള്ള UPI ഇടപാട്"
    },
    "UPI_ID_ISSUE": {
        "en": "a UPI ID problem",
        "ta": "UPI ID பிரச்சினை",
        "te": "UPI ID సమస్య",
        "kn": "UPI ID ಸಮಸ್ಯೆ",
        "ml": "UPI ID പ്രശ്നം"
    },
    "UPI_COLLECT_REQUEST": {
        "en": "a UPI collect request",
        "ta": "UPI collect request",
        "te": "UPI collect request",
        "kn": "UPI collect request",
        "ml": "UPI collect request"
    },
    "BANK_TRANSFER_FAILED": {
        "en": "a failed bank transfer",
        "ta": "தோல்வியடைந்த வங்கி பரிமாற்றம்",
        "te": "విఫలమైన బ్యాంక్ బదిలీ",
        "kn": "ವಿಫಲವಾದ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ",
        "ml": "പരാജയപ്പെട്ട ബാങ്ക് ട്രാൻസ്ഫർ"
    },
    "BANK_TRANSFER_PENDING": {
        "en": "a pending bank transfer",
        "ta": "நிலுவையில் உள்ள வங்கி பரிமாற்றம்",
        "te": "పెండింగ్‌లో ఉన్న బ్యాంక్ బదిలీ",
        "kn": "ಬಾಕಿಯಿರುವ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ",
        "ml": "പെൻഡിംഗിലുള്ള ബാങ്ക് ട്രാൻസ്ഫർ"
    },
    "BANK_TRANSFER_STATUS": {
        "en": "my bank transfer status",
        "ta": "எனது வங்கி பரிமாற்ற நிலை",
        "te": "నా బ్యాంక్ బదిలీ స్థితి",
        "kn": "ನನ್ನ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆಯ ಸ್ಥಿತಿ",
        "ml": "എന്റെ ബാങ്ക് ട്രാൻസ്ഫർ നില"
    },
    "BENEFICIARY_ISSUE": {
        "en": "a beneficiary problem",
        "ta": "பெறுநர் விவரப் பிரச்சினை",
        "te": "లబ్ధిదారుడి సమస్య",
        "kn": "ಫಲಾನುಭವಿಯ ಸಮಸ್ಯೆ",
        "ml": "ഗുണഭോക്താവിന്റെ പ്രശ്നം"
    },
    "CASH_WITHDRAWAL_FAILED": {
        "en": "a failed cash withdrawal",
        "ta": "தோல்வியடைந்த பணம் எடுப்பு",
        "te": "విఫలమైన నగదు ఉపసంహరణ",
        "kn": "ವಿಫಲವಾದ ನಗದು ಹಿಂಪಡೆಯುವಿಕೆ",
        "ml": "പരാജയപ്പെട്ട പണം പിൻവലിക്കൽ"
    },
    "CASH_WITHDRAWAL_STATUS": {
        "en": "my cash withdrawal status",
        "ta": "எனது பணம் எடுப்பு நிலை",
        "te": "నా నగదు ఉపసంహరణ స్థితి",
        "kn": "ನನ್ನ ನಗದು ಹಿಂಪಡೆಯುವಿಕೆಯ ಸ್ಥಿತಿ",
        "ml": "എന്റെ പണം പിൻവലിക്കൽ നില"
    },

    "REFUND_PENDING": {
        "en": "a pending refund",
        "ta": "நிலுவையில் உள்ள பணம் திரும்பப்பெறுதல்",
        "te": "పెండింగ్‌లో ఉన్న రీఫండ్",
        "kn": "ಬಾಕಿಯಿರುವ ಮರುಪಾವತಿ",
        "ml": "പെൻഡിംഗിലുള്ള റീഫണ്ട്"
    },
    "REFUND_FAILED": {
        "en": "a failed refund",
        "ta": "தோல்வியடைந்த பணம் திரும்பப்பெறுதல்",
        "te": "విఫలమైన రీఫండ్",
        "kn": "ವಿಫಲವಾದ ಮರುಪಾವತಿ",
        "ml": "പരാജയപ്പെട്ട റീഫണ്ട്"
    },
    "REFUND_RECEIVED": {
        "en": "a received refund",
        "ta": "பெறப்பட்ட பணம் திரும்பப்பெறுதல்",
        "te": "అందుకున్న రీఫండ్",
        "kn": "ಸ್ವೀಕರಿಸಿದ ಮರುಪಾವತಿ",
        "ml": "ലഭിച്ച റീഫണ്ട്"
    },
    "REFUND_AMOUNT_WRONG": {
        "en": "an incorrect refund amount",
        "ta": "தவறான பணம் திரும்பப்பெறும் தொகை",
        "te": "తప్పుగా ఉన్న రీఫండ్ మొత్తం",
        "kn": "ತಪ್ಪಾದ ಮರುಪಾವತಿ ಮೊತ್ತ",
        "ml": "തെറ്റായ റീഫണ്ട് തുക"
    },
    "DISPUTE_TRANSACTION": {
        "en": "disputing a transaction",
        "ta": "ஒரு பரிவர்த்தனை குறித்து புகார்",
        "te": "లావాదేవీపై వివాదం",
        "kn": "ವಹಿವಾಟಿನ ಕುರಿತು ವಿವಾದ",
        "ml": "ഒരു ഇടപാടിനെക്കുറിച്ചുള്ള തർക്കം"
    },

    "FRAUD_REPORT": {
        "en": "reporting financial fraud",
        "ta": "நிதி மோசடியை புகாரளிப்பது",
        "te": "ఆర్థిక మోసాన్ని నివేదించడం",
        "kn": "ಹಣಕಾಸು ವಂಚನೆಯನ್ನು ವರದಿ ಮಾಡುವುದು",
        "ml": "സാമ്പത്തിക തട്ടിപ്പ് റിപ്പോർട്ട് ചെയ്യുന്നത്"
    },
    "UNKNOWN_TRANSACTION": {
        "en": "an unknown transaction",
        "ta": "தெரியாத பரிவர்த்தனை",
        "te": "తెలియని లావాదేవీ",
        "kn": "ತಿಳಿಯದ ವಹಿವಾಟು",
        "ml": "അറിയാത്ത ഇടപാട്"
    },
    "SUSPICIOUS_ACTIVITY": {
        "en": "suspicious financial activity",
        "ta": "சந்தேகத்திற்கிடமான நிதி செயல்பாடு",
        "te": "అనుమానాస్పద ఆర్థిక కార్యకలాపం",
        "kn": "ಅನುಮಾನಾಸ್ಪದ ಹಣಕಾಸು ಚಟುವಟಿಕೆ",
        "ml": "സംശയാസ്പദമായ സാമ്പത്തിക പ്രവർത്തനം"
    },
    "ACCOUNT_COMPROMISED": {
        "en": "a compromised account",
        "ta": "சமரசம் செய்யப்பட்ட கணக்கு",
        "te": "సురక్షితం కాకிவிடిన ఖాతా",
        "kn": "ಸುರಕ್ಷತೆ ಕಳೆದುಕೊಂಡ ಖಾತೆ",
        "ml": "സുരക്ഷ നഷ്ടപ്പെട്ട അക്കൗണ്ട്"
    },

    "CARD_LOST": {
        "en": "a lost card",
        "ta": "தொலைந்த கார்டு",
        "te": "పోయిన కార్డు",
        "kn": "ಕಳೆದುಹೋದ ಕಾರ್ಡ್",
        "ml": "നഷ്ടപ്പെട്ട കാർഡ്"
    },
    "CARD_STOLEN": {
        "en": "a stolen card",
        "ta": "திருடப்பட்ட கார்டு",
        "te": "దొంగిలించబడిన కార్డు",
        "kn": "ಕಳುವಾದ ಕಾರ್ಡ್",
        "ml": "മോഷണം പോയ കാർഡ്"
    },
    "CARD_BLOCK": {
        "en": "blocking my card",
        "ta": "எனது கார்டை முடக்குவது",
        "te": "నా కార్డును బ్లాక్ చేయడం",
        "kn": "ನನ್ನ ಕಾರ್ಡ್ ಅನ್ನು ಬ್ಲಾಕ್ ಮಾಡುವುದು",
        "ml": "എന്റെ കാർഡ് ബ്ലോക്ക് ചെയ്യുന്നത്"
    },
    "CARD_UNBLOCK": {
        "en": "unblocking my card",
        "ta": "எனது கார்டை மீண்டும் செயல்படுத்துவது",
        "te": "నా కార్డును అన్‌బ్లాక్ చేయడం",
        "kn": "ನನ್ನ ಕಾರ್ಡ್ ಅನ್ನು ಅನ್‌ಬ್ಲಾಕ್ ಮಾಡುವುದು",
        "ml": "എന്റെ കാർഡ് അൺബ്ലോക്ക് ചെയ്യുന്നത്"
    },
    "CARD_PAYMENT_FAILED": {
        "en": "a failed card payment",
        "ta": "தோல்வியடைந்த கார்டு பணம் செலுத்துதல்",
        "te": "విఫలమైన కార్డ్ చెల్లింపు",
        "kn": "ವಿಫಲವಾದ ಕಾರ್ಡ್ ಪಾವತಿ",
        "ml": "പരാജയപ്പെട്ട കാർഡ് പേയ്‌മെന്റ്"
    },
    "CARD_ACTIVATION": {
        "en": "activating my card",
        "ta": "எனது கார்டை செயல்படுத்துவது",
        "te": "నా కార్డును యాక్టివేట్ చేయడం",
        "kn": "ನನ್ನ ಕಾರ್ಡ್ ಅನ್ನು ಸಕ್ರಿಯಗೊಳಿಸುವುದು",
        "ml": "എന്റെ കാർഡ് ആക്ടിവേറ്റ് ചെയ്യുന്നത്"
    },
    "PIN_FAILED": {
        "en": "a failed card PIN",
        "ta": "கார்டு PIN பிரச்சினை",
        "te": "కార్డ్ PIN సమస్య",
        "kn": "ಕಾರ್ಡ್ PIN ಸಮಸ್ಯೆ",
        "ml": "കാർഡ് PIN പ്രശ്നം"
    },

    "ACCOUNT_BALANCE": {
        "en": "my account balance",
        "ta": "எனது கணக்கு இருப்பு",
        "te": "నా ఖాతా బ్యాలెన్స్",
        "kn": "ನನ್ನ ಖಾತೆಯ ಬ್ಯಾಲೆನ್ಸ್",
        "ml": "എന്റെ അക്കൗണ്ട് ബാലൻസ്"
    },
    "TRANSACTION_HISTORY": {
        "en": "my transaction history",
        "ta": "எனது பரிவர்த்தனை வரலாறு",
        "te": "నా లావాదేవీ చరిత్ర",
        "kn": "ನನ್ನ ವಹಿವಾಟಿನ ಇತಿಹಾಸ",
        "ml": "എന്റെ ഇടപാട് ചരിത്രം"
    },
    "ACCOUNT_LOCKED": {
        "en": "a locked account",
        "ta": "பூட்டப்பட்ட கணக்கு",
        "te": "లాక్ అయిన ఖాతా",
        "kn": "ಲಾಕ್ ಆದ ಖಾತೆ",
        "ml": "ലോക്ക് ചെയ്ത അക്കൗണ്ട്"
    },
    "PROFILE_UPDATE": {
        "en": "updating my profile",
        "ta": "எனது சுயவிவரத்தை புதுப்பிப்பது",
        "te": "నా ప్రొఫైల్‌ను నవీకరించడం",
        "kn": "ನನ್ನ ಪ್ರೊಫೈಲ್ ನವೀಕರಿಸುವುದು",
        "ml": "എന്റെ പ്രൊഫൈൽ അപ്‌ഡേറ്റ് ചെയ്യുന്നത്"
    },
    "PASSWORD_RESET": {
        "en": "resetting my password",
        "ta": "எனது கடவுச்சொல்லை மீட்டமைப்பது",
        "te": "నా పాస్‌వర్డ్‌ను రీసெட் చేయడం",
        "kn": "ನನ್ನ ಪಾಸ್‌ವರ್ಡ್ ಮರುಹೊಂದಿಸುವುದು",
        "ml": "എന്റെ പാസ്‌വേഡ് റീസെറ്റ് ചെയ്യുന്നത്"
    },
    "KYC_STATUS": {
        "en": "my KYC status",
        "ta": "எனது KYC நிலை",
        "te": "నా KYC స్థితి",
        "kn": "ನನ್ನ KYC ಸ್ಥಿತಿ",
        "ml": "എന്റെ KYC നില"
    },
    "KYC_FAILED": {
        "en": "a failed KYC verification",
        "ta": "தோல்வியடைந்த KYC சரிபார்ப்பு",
        "te": "విఫలమైన KYC ధృవీకరణ",
        "kn": "ವಿಫಲವಾದ KYC ಪರಿಶೀಲನೆ",
        "ml": "പരാജയപ്പെട്ട KYC പരിശോധന"
    },
    "KYC_DOCUMENTS": {
        "en": "KYC documents",
        "ta": "KYC ஆவணங்கள்",
        "te": "KYC పత్రాలు",
        "kn": "KYC ದಾಖಲೆಗಳು",
        "ml": "KYC രേഖകൾ"
    },
    "KYC_UPDATE": {
        "en": "updating my KYC",
        "ta": "எனது KYC தகவலை புதுப்பிப்பது",
        "te": "నా KYC సమాచారాన్ని నవీకరించడం",
        "kn": "ನನ್ನ KYC ಮಾಹಿತಿಯನ್ನು ನವೀಕರಿಸುವುದು",
        "ml": "എന്റെ KYC വിവരങ്ങൾ അപ്‌ഡേറ്റ് ചെയ്യുന്നത്"
    },

    "LOAN_ELIGIBILITY": {
        "en": "loan eligibility",
        "ta": "கடன் தகுதி",
        "te": "రుణ అర్హత",
        "kn": "ಸಾಲದ ಅರ್ಹತೆ",
        "ml": "വായ്പാ യോഗ്യത"
    },
    "LOAN_STATUS": {
        "en": "my loan application status",
        "ta": "எனது கடன் விண்ணப்ப நிலை",
        "te": "నా రుణ దరఖాస్తు స్థితి",
        "kn": "ನನ್ನ ಸಾಲದ ಅರ್ಜಿ ಸ್ಥಿತಿ",
        "ml": "എന്റെ വായ്പാ അപേക്ഷയുടെ നില"
    },
    "EMI_QUERY": {
        "en": "my EMI",
        "ta": "எனது EMI",
        "te": "నా EMI",
        "kn": "ನನ್ನ EMI",
        "ml": "എന്റെ EMI"
    },
    "INTEREST_QUERY": {
        "en": "my loan interest rate",
        "ta": "எனது கடன் வட்டி விகிதம்",
        "te": "నా రుణ వడ్డీ రేటు",
        "kn": "ನನ್ನ ಸಾಲದ ಬಡ್ಡಿ ದರ",
        "ml": "എന്റെ വായ്പയുടെ പലിശ നിരക്ക്"
    },

    "SUPPORT_REQUEST": {
        "en": "help with my financial account",
        "ta": "எனது நிதி கணக்கு தொடர்பான உதவி",
        "te": "నా ఆర్థిక ఖాతాకు సంబంధించిన సహాయం",
        "kn": "ನನ್ನ ಹಣಕಾಸು ಖಾತೆಗೆ ಸಂಬಂಧಿಸಿದ ಸಹಾಯ",
        "ml": "എന്റെ സാമ്പത്തിക അക്കൗണ്ടുമായി ബന്ധപ്പെട്ട സഹായം"
    }
}


# ============================================================
# Language templates
# ============================================================

TEMPLATES = {
    "en": [
        "I need help with {topic}.",
        "Can you help me with {topic}?",
        "I want to know about {topic}.",
        "Please help me with {topic}.",
        "I have a problem with {topic}.",
        "Can you check {topic}?",
        "I need assistance regarding {topic}.",
        "What should I do about {topic}?",
        "Please explain {topic}.",
        "I have a question about {topic}."
    ],
    "ta": [
        "{topic} குறித்து எனக்கு உதவி வேண்டும்.",
        "{topic} பற்றி உதவ முடியுமா?",
        "{topic} பற்றி தெரிந்துகொள்ள வேண்டும்.",
        "{topic} குறித்து உதவுங்கள்.",
        "{topic} தொடர்பாக எனக்கு ஒரு பிரச்சினை உள்ளது.",
        "{topic} பற்றி சரிபார்க்க முடியுமா?",
        "{topic} தொடர்பாக உதவி தேவை.",
        "{topic} பற்றி நான் என்ன செய்ய வேண்டும்?",
        "{topic} பற்றி விளக்குங்கள்.",
        "{topic} குறித்து ஒரு கேள்வி உள்ளது."
    ],
    "te": [
        "{topic} గురించి నాకు సహాయం కావాలి.",
        "{topic} గురించి నాకు సహాయం చేయగలరా?",
        "{topic} గురించి తెలుసుకోవాలి.",
        "{topic} విషయంలో సహాయం చేయండి.",
        "{topic} విషయంలో నాకు ఒక సమస్య ఉంది.",
        "{topic} ను తనిఖీ చేయగలరా?",
        "{topic} గురించి నాకు సహాయం అవసరం.",
        "{topic} విషయంలో నేను ఏమి చేయాలి?",
        "{topic} గురించి వివరించండి.",
        "{topic} గురించి నాకు ఒక ప్రశ్న ఉంది."
    ],
    "kn": [
        "{topic} ಬಗ್ಗೆ ನನಗೆ ಸಹಾಯ ಬೇಕು.",
        "{topic} ಬಗ್ಗೆ ನನಗೆ ಸಹಾಯ ಮಾಡಬಹುದೇ?",
        "{topic} ಬಗ್ಗೆ ತಿಳಿದುಕೊಳ್ಳಬೇಕು.",
        "{topic} ಕುರಿತು ಸಹಾಯ ಮಾಡಿ.",
        "{topic} ಬಗ್ಗೆ ನನಗೆ ಸಮಸ್ಯೆ ಇದೆ.",
        "{topic} ಅನ್ನು ಪರಿಶೀಲಿಸಬಹುದೇ?",
        "{topic} ಬಗ್ಗೆ ನನಗೆ ಸಹಾಯ ಅಗತ್ಯವಿದೆ.",
        "{topic} ಬಗ್ಗೆ ನಾನು ಏನು ಮಾಡಬೇಕು?",
        "{topic} ಬಗ್ಗೆ ವಿವರಿಸಿ.",
        "{topic} ಕುರಿತು ನನಗೆ ಒಂದು ಪ್ರಶ್ನೆ ಇದೆ."
    ],
    "ml": [
        "{topic} സംബന്ധിച്ച് എനിക്ക് സഹായം വേണം.",
        "{topic} സംബന്ധിച്ച് സഹായിക്കാമോ?",
        "{topic}യെക്കുറിച്ച് അറിയണം.",
        "{topic} സംബന്ധിച്ച് സഹായിക്കുക.",
        "{topic} സംബന്ധിച്ച് എനിക്ക് ഒരു പ്രശ്നമുണ്ട്.",
        "{topic} പരിശോധിക്കാമോ?",
        "{topic} സംബന്ധിച്ച് സഹായം ആവശ്യമാണ്.",
        "{topic} സംബന്ധിച്ച് ഞാൻ എന്ത് ചെയ്യണം?",
        "{topic} വിശദീകരിക്കുക.",
        "{topic}യെക്കുറിച്ച് എനിക്ക് ഒരു ചോദ്യം ഉണ്ട്."
    ]
}


# ============================================================
# Small deterministic variations
# ============================================================

SUFFIXES = {
    "en": [
        "",
        " Please.",
        " Thanks.",
        " Kindly help.",
        " Urgently.",
        " Please check.",
        " I need this resolved.",
        " Can you assist?",
        " Please guide me.",
        " I need an answer."
    ],
    "ta": [
        "",
        " தயவுசெய்து.",
        " உதவுங்கள்.",
        " அவசரமாக உதவுங்கள்.",
        " தயவு செய்து பார்க்கவும்.",
        " வழிகாட்டுங்கள்.",
        " இது குறித்து உதவி தேவை.",
        " விரைவாக தெரிவிக்கவும்.",
        " தயவு செய்து சரிபார்க்கவும்.",
        " பதில் சொல்லுங்கள்."
    ],
    "te": [
        "",
        " దయచేసి.",
        " సహాయం చేయండి.",
        " అత్యవసరంగా సహాయం చేయండి.",
        " దయచేసి తనిఖీ చేయండి.",
        " మార్గనిర్దేశం చేయండి.",
        " దీనిపై సహాయం కావాలి.",
        " త్వరగా తెలియజేయండి.",
        " దయచేసి పరిశీలించండి.",
        " సమాధానం చెప్పండి."
    ],
    "kn": [
        "",
        " ದಯವಿಟ್ಟು.",
        " ಸಹಾಯ ಮಾಡಿ.",
        " ತುರ್ತಾಗಿ ಸಹಾಯ ಮಾಡಿ.",
        " ದಯವಿಟ್ಟು ಪರಿಶೀಲಿಸಿ.",
        " ಮಾರ್ಗದರ್ಶನ ನೀಡಿ.",
        " ಇದರ ಬಗ್ಗೆ ಸಹಾಯ ಬೇಕು.",
        " ಬೇಗ ತಿಳಿಸಿ.",
        " ದಯವಿಟ್ಟು ಪರಿಶೀಲಿಸಿ.",
        " ಉತ್ತರಿಸಿ."
    ],
    "ml": [
        "",
        " ദയവായി.",
        " സഹായിക്കുക.",
        " അടിയന്തരമായി സഹായിക്കുക.",
        " ദയവായി പരിശോധിക്കുക.",
        " മാർഗനിർദേശം നൽകുക.",
        " ഇതിന് സഹായം വേണം.",
        " വേഗത്തിൽ അറിയിക്കുക.",
        " ദയവായി പരിശോധിക്കൂ.",
        " മറുപടി നൽകുക."
    ]
}


def normalize_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_seed_examples():
    if not SEED_FILE.exists():
        return {}

    result = {}

    with SEED_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            key = (
                record["language"],
                record["intent"]
            )

            result[key] = record

    return result


def build_response(language, risk_level, requires_tool):
    if risk_level == "critical":
        responses = {
            "en": "For security, please use the official financial service or support channel and complete the required verification.",
            "ta": "பாதுகாப்பிற்காக அதிகாரப்பூர்வ நிதி சேவை அல்லது உதவி மையத்தைப் பயன்படுத்தி தேவையான சரிபார்ப்பை முடிக்கவும்.",
            "te": "భద్రత కోసం అధికారిక ఆర్థిక సేవ లేదా సహాయ కేంద్రాన్ని ఉపయోగించి అవసరమైన ధృవీకరణను పూర్తి చేయండి.",
            "kn": "ಭದ್ರತೆಗಾಗಿ ಅಧಿಕೃತ ಹಣಕಾಸು ಸೇವೆ ಅಥವಾ ಸಹಾಯವಾಣಿಯನ್ನು ಬಳಸಿ ಅಗತ್ಯ ಪರಿಶೀಲನೆಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ.",
            "ml": "സുരക്ഷയ്ക്കായി ഔദ്യോഗിക സാമ്പത്തിക സേവനമോ സഹായകേന്ദ്രമോ ഉപയോഗിച്ച് ആവശ്യമായ പരിശോധന പൂർത്തിയാക്കുക."
        }
        return responses[language]

    if requires_tool:
        responses = {
            "en": "This may require checking your authenticated account or transaction details through the official financial service.",
            "ta": "இதற்கு உங்கள் அதிகாரப்பூர்வ நிதி சேவையில் அங்கீகரிக்கப்பட்ட கணக்கு அல்லது பரிவர்த்தனை விவரங்களைச் சரிபார்க்க வேண்டியிருக்கலாம்.",
            "te": "దీనికి అధికారిక ఆర్థిక సేవలో మీ ధృవీకరించబడిన ఖాతా లేదా లావాదేవీ వివరాలను తనిఖీ చేయాల్సి ఉండవచ్చు.",
            "kn": "ಇದಕ್ಕಾಗಿ ಅಧಿಕೃತ ಹಣಕಾಸು ಸೇವೆಯಲ್ಲಿ ನಿಮ್ಮ ದೃಢೀಕರಿಸಿದ ಖಾತೆ ಅಥವಾ ವಹಿವಾಟಿನ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಬೇಕಾಗಬಹುದು.",
            "ml": "ഇതിന് ഔദ്യോഗിക സാമ്പത്തിക സേവനത്തിലെ നിങ്ങളുടെ അംഗീകരിച്ച അക്കൗണ്ട് അല്ലെങ്കിൽ ഇടപാട് വിവരങ്ങൾ പരിശോധിക്കേണ്ടി വരാം."
        }
        return responses[language]

    responses = {
        "en": "I can provide general information and guidance about this financial issue.",
        "ta": "இந்த நிதி பிரச்சினை குறித்து பொதுவான தகவலும் வழிகாட்டுதலும் வழங்க முடியும்.",
        "te": "ఈ ఆర్థిక సమస్య గురించి సాధారణ సమాచారం మరియు మార్గదర్శకత్వం ఇవ్వగలను.",
        "kn": "ಈ ಹಣಕಾಸು ಸಮಸ್ಯೆಯ ಬಗ್ಗೆ ಸಾಮಾನ್ಯ ಮಾಹಿತಿ ಮತ್ತು ಮಾರ್ಗದರ್ಶನ ನೀಡಬಹುದು.",
        "ml": "ഈ സാമ്പത്തിക വിഷയത്തെക്കുറിച്ച് പൊതുവായ വിവരവും മാർഗനിർദേശവും നൽകാം."
    }

    return responses[language]


def main():
    taxonomy = load_json(TAXONOMY_FILE)
    tool_map = load_json(TOOL_MAP_FILE)
    seeds = load_seed_examples()

    intents = [item["intent"] for item in taxonomy]

    errors = []

    # Ensure every taxonomy intent has localized topics.
    for intent in intents:
        if intent not in TOPICS:
            errors.append(
                f"Missing localized topic for {intent}"
            )

    if errors:
        print("CONFIGURATION ERRORS:")

        for error in errors:
            print("-", error)

        raise SystemExit(1)

    records = []

    languages = ["en", "ta", "te", "kn", "ml"]

    for intent in intents:

        taxonomy_item = next(
            item for item in taxonomy
            if item["intent"] == intent
        )

        category = taxonomy_item["category"]
        risk_level = taxonomy_item["risk_level"]
        requires_tool = taxonomy_item["requires_tool"]
        tool_name = tool_map[intent]["tool_name"]

        for language in languages:

            key = (language, intent)
            seed = seeds.get(key)

            # ----------------------------------------------------
            # Preserve original curated example when available.
            # ----------------------------------------------------
            if seed is not None:

                records.append({
                    "id": None,
                    "language": language,
                    "category": category,
                    "intent": intent,
                    "text": normalize_text(seed["text"]),
                    "response": seed["response"],
                    "risk_level": risk_level,
                    "requires_tool": requires_tool,
                    "tool_name": tool_name,
                    "variation_type": "curated_seed",
                    "source_type": "human_curated_seed"
                })

            generated_needed = (
                EXAMPLES_PER_LANGUAGE_INTENT
                - (1 if seed is not None else 0)
            )

            topic = TOPICS[intent][language]
            templates = TEMPLATES[language]
            suffixes = SUFFIXES[language]

            counter = 0

            while counter < generated_needed:

                template_index = counter % len(templates)
                suffix_index = (
                    counter // len(templates)
                ) % len(suffixes)

                text = templates[template_index].format(
                    topic=topic
                )

                text = normalize_text(
                    text.rstrip(".?!") +
                    suffixes[suffix_index]
                )

                # Create small deterministic formatting changes
                if counter % 13 == 0:
                    text = text.replace("  ", " ")

                if counter % 17 == 0:
                    text = text + "?"

                if counter % 19 == 0:
                    text = text.replace("?", "??")

                if counter % 23 == 0:
                    text = text.replace(".", "...")

                record = {
                    "id": None,
                    "language": language,
                    "category": category,
                    "intent": intent,
                    "text": text,
                    "response": build_response(
                        language,
                        risk_level,
                        requires_tool
                    ),
                    "risk_level": risk_level,
                    "requires_tool": requires_tool,
                    "tool_name": tool_name,
                    "variation_type": (
                        f"template_{template_index}_"
                        f"suffix_{suffix_index}"
                    ),
                    "source_type": "synthetic_template_v2"
                }

                records.append(record)
                counter += 1

    # ------------------------------------------------------------
    # Deduplicate
    # ------------------------------------------------------------
    unique = []
    seen = set()

    for record in records:

        key = (
            record["language"],
            record["intent"],
            record["text"].casefold()
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(record)

    records = unique

    # ------------------------------------------------------------
    # Shuffle
    # ------------------------------------------------------------
    random.shuffle(records)

    # ------------------------------------------------------------
    # IDs
    # ------------------------------------------------------------
    for index, record in enumerate(records, start=1):
        record["id"] = f"finai_{index:06d}"

    # ------------------------------------------------------------
    # Final validation
    # ------------------------------------------------------------
    expected_total = (
        len(intents)
        * len(languages)
        * EXAMPLES_PER_LANGUAGE_INTENT
    )

    if len(records) != expected_total:
        raise RuntimeError(
            f"Expected {expected_total} examples, "
            f"generated {len(records)}."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

    print("=" * 70)
    print("FINAI 20K DATASET GENERATED")
    print("=" * 70)
    print(f"Intents                 : {len(intents)}")
    print(f"Languages               : {len(languages)}")
    print(f"Examples per pair       : {EXAMPLES_PER_LANGUAGE_INTENT}")
    print(f"Total examples          : {len(records)}")
    print(f"Output                  : {OUTPUT_FILE}")
    print("=" * 70)
    print()
    print("Language distribution:")

    for language in languages:
        count = sum(
            1 for r in records
            if r["language"] == language
        )
        print(f"  {language}: {count}")

    print()
    print("Source distribution:")

    source_counts = {}

    for record in records:
        source = record["source_type"]
        source_counts[source] = (
            source_counts.get(source, 0) + 1
        )

    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    print()
    print("Generation complete.")


if __name__ == "__main__":
    main()