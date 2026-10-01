from pathlib import Path
import json
import hashlib
import random
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

SEED_FILE = ROOT / "data" / "sft_v3_work" / "finai_v3_intent_seed.jsonl"
OUT_FILE = ROOT / "data" / "sft_v3_work" / "finai_v3_contrastive.jsonl"
MANIFEST = ROOT / "data" / "manifests" / "finai_v3_contrastive_manifest.json"

random.seed(20260929)

LANGUAGES = ["en", "ta", "te", "kn", "ml"]


# Carefully separated examples for the most important intent boundaries.
TEMPLATES = {

    ("PAYMENT_FAILED", "PAYMENT_PENDING"): {
        "PAYMENT_FAILED": {
            "en": [
                "My payment was declined.",
                "The payment failed immediately.",
                "The transaction was rejected.",
                "My payment did not go through.",
                "The payment attempt was unsuccessful.",
                "The payment was declined by the bank.",
                "Why was my payment rejected?",
                "The transaction failed while I was paying.",
                "I received a payment failure message.",
                "My payment attempt failed."
            ],
            "ta": [
                "என் பணம் செலுத்துதல் தோல்வியடைந்தது.",
                "என் கட்டணம் நிராகரிக்கப்பட்டது.",
                "பரிவர்த்தனை வெற்றிகரமாக முடியவில்லை.",
                "பணம் செலுத்தும் முயற்சி தோல்வியடைந்தது.",
                "என் payment செல்லவில்லை.",
                "வங்கி payment-ஐ நிராகரித்தது.",
                "என் பரிவர்த்தனை தோல்வியடைந்தது.",
                "Payment failure என்று வருகிறது.",
                "நான் செய்த payment reject ஆனது.",
                "பணம் செலுத்த முடியவில்லை."
            ],
            "te": [
                "నా payment విఫలమైంది.",
                "నా చెల్లింపు తిరస్కరించబడింది.",
                "లావాదేవీ విజయవంతం కాలేదు.",
                "నా payment జరగలేదు.",
                "చెల్లింపు ప్రయత్నం విఫలమైంది.",
                "బ్యాంక్ payment ను తిరస్కరించింది.",
                "నా transaction failed అయింది.",
                "Payment failure అని చూపిస్తోంది.",
                "నేను చేసిన payment reject అయింది.",
                "చెల్లింపు పూర్తి కాలేదు."
            ],
            "kn": [
                "ನನ್ನ payment ವಿಫಲವಾಗಿದೆ.",
                "ನನ್ನ ಪಾವತಿ ತಿರಸ್ಕರಿಸಲಾಗಿದೆ.",
                "ವಹಿವಾಟು ಯಶಸ್ವಿಯಾಗಲಿಲ್ಲ.",
                "ನನ್ನ payment ಆಗಲಿಲ್ಲ.",
                "ಪಾವತಿ ಪ್ರಯತ್ನ ವಿಫಲವಾಗಿದೆ.",
                "ಬ್ಯಾಂಕ್ payment ಅನ್ನು ತಿರಸ್ಕರಿಸಿದೆ.",
                "ನನ್ನ transaction failed ಆಗಿದೆ.",
                "Payment failure ಎಂದು ತೋರಿಸುತ್ತಿದೆ.",
                "ನಾನು ಮಾಡಿದ payment reject ಆಯಿತು.",
                "ಪಾವತಿ ಪೂರ್ಣವಾಗಲಿಲ್ಲ."
            ],
            "ml": [
                "എന്റെ payment പരാജയപ്പെട്ടു.",
                "എന്റെ പണമടയ്ക്കൽ നിരസിക്കപ്പെട്ടു.",
                "ഇടപാട് വിജയിച്ചില്ല.",
                "എന്റെ payment നടന്നില്ല.",
                "പണമടയ്ക്കാനുള്ള ശ്രമം പരാജയപ്പെട്ടു.",
                "ബാങ്ക് payment നിരസിച്ചു.",
                "എന്റെ transaction failed ആയി.",
                "Payment failure എന്ന് കാണിക്കുന്നു.",
                "ഞാൻ നടത്തിയ payment reject ആയി.",
                "പണമടയ്ക്കൽ പൂർത്തിയായില്ല."
            ]
        },
        "PAYMENT_PENDING": {
            "en": [
                "My payment is still pending.",
                "The payment is waiting to complete.",
                "My transaction shows pending.",
                "The payment has not completed yet.",
                "Why is the payment still processing?",
                "My payment is stuck in pending status.",
                "The transaction is waiting for confirmation.",
                "The payment has not settled yet.",
                "My payment is processing for a long time.",
                "The transaction has not reached final status."
            ],
            "ta": [
                "என் payment இன்னும் pending-ல் உள்ளது.",
                "என் கட்டணம் இன்னும் முடிவடையவில்லை.",
                "பரிவர்த்தனை pending என்று காட்டுகிறது.",
                "என் payment இன்னும் செயலாக்கத்தில் உள்ளது.",
                "Payment இன்னும் processing-ல் உள்ளது.",
                "என் transaction இன்னும் உறுதிப்படுத்தப்படவில்லை.",
                "பரிவர்த்தனை முடிக்க காத்திருக்கிறது.",
                "என் payment settle ஆகவில்லை.",
                "நீண்ட நேரமாக payment pending-ல் உள்ளது.",
                "Transaction-க்கு final status வரவில்லை."
            ],
            "te": [
                "నా payment ఇంకా pending లో ఉంది.",
                "నా చెల్లింపు ఇంకా పూర్తికాలేదు.",
                "లావాదేవీ pending గా చూపిస్తోంది.",
                "నా payment ఇంకా processing లో ఉంది.",
                "Payment ఇంకా process అవుతోంది.",
                "నా transaction ఇంకా confirm కాలేదు.",
                "లావాదేవీ పూర్తి కావడానికి వేచి ఉంది.",
                "నా payment ఇంకా settle కాలేదు.",
                "చాలా సేపటి నుంచి payment pending లో ఉంది.",
                "Transaction కు final status రాలేదు."
            ],
            "kn": [
                "ನನ್ನ payment ಇನ್ನೂ pending ಇದೆ.",
                "ನನ್ನ ಪಾವತಿ ಇನ್ನೂ ಪೂರ್ಣವಾಗಿಲ್ಲ.",
                "ವಹಿವಾಟು pending ಎಂದು ತೋರಿಸುತ್ತಿದೆ.",
                "ನನ್ನ payment ಇನ್ನೂ processing ನಲ್ಲಿ ಇದೆ.",
                "Payment ಇನ್ನೂ process ಆಗುತ್ತಿದೆ.",
                "ನನ್ನ transaction ಇನ್ನೂ confirm ಆಗಿಲ್ಲ.",
                "ವಹಿವಾಟು ಪೂರ್ಣಗೊಳ್ಳಲು ಕಾಯುತ್ತಿದೆ.",
                "ನನ್ನ payment ಇನ್ನೂ settle ಆಗಿಲ್ಲ.",
                "ಬಹಳ ಸಮಯದಿಂದ payment pending ಇದೆ.",
                "Transaction ಗೆ final status ಬಂದಿಲ್ಲ."
            ],
            "ml": [
                "എന്റെ payment ഇപ്പോഴും pending ആണ്.",
                "എന്റെ പണമടയ്ക്കൽ ഇതുവരെ പൂർത്തിയായിട്ടില്ല.",
                "ഇടപാട് pending ആയി കാണിക്കുന്നു.",
                "എന്റെ payment ഇപ്പോഴും processing ആണ്.",
                "Payment ഇപ്പോഴും process ചെയ്യുകയാണ്.",
                "എന്റെ transaction ഇതുവരെ confirm ചെയ്തിട്ടില്ല.",
                "ഇടപാട് പൂർത്തിയാകാൻ കാത്തിരിക്കുകയാണ്.",
                "എന്റെ payment ഇതുവരെ settle ആയിട്ടില്ല.",
                "വളരെ നേരമായി payment pending ആണ്.",
                "Transaction ന് final status ലഭിച്ചിട്ടില്ല."
            ]
        }
    },

    ("UPI_PAYMENT_FAILED", "CARD_PAYMENT_FAILED"): {
        "UPI_PAYMENT_FAILED": {
            "en": [
                "My UPI payment failed.",
                "The UPI transaction was declined.",
                "UPI did not let me complete the payment.",
                "My UPI payment was unsuccessful.",
                "The UPI transfer failed during checkout.",
                "Why did my UPI payment fail?",
                "I got a failure message for my UPI payment.",
                "The payment failed when I used UPI.",
                "My UPI transaction was rejected.",
                "I could not complete the payment through UPI."
            ],
            "ta": [
                "என் UPI payment தோல்வியடைந்தது.",
                "UPI பரிவர்த்தனை நிராகரிக்கப்பட்டது.",
                "UPI மூலம் payment செய்ய முடியவில்லை.",
                "என் UPI payment வெற்றியளிக்கவில்லை.",
                "UPI transaction தோல்வியடைந்தது.",
                "என் UPI payment ஏன் தோல்வியடைந்தது?",
                "UPI payment failure என்று வருகிறது.",
                "UPI பயன்படுத்தியபோது payment தோல்வியடைந்தது.",
                "என் UPI transaction reject ஆனது.",
                "UPI மூலம் பணம் செலுத்த முடியவில்லை."
            ],
            "te": [
                "నా UPI payment విఫలమైంది.",
                "UPI transaction తిరస్కరించబడింది.",
                "UPI ద్వారా payment పూర్తి కాలేదు.",
                "నా UPI payment విజయవంతం కాలేదు.",
                "UPI transaction failed అయింది.",
                "నా UPI payment ఎందుకు విఫలమైంది?",
                "UPI payment failure అని వస్తోంది.",
                "UPI ఉపయోగించినప్పుడు payment విఫలమైంది.",
                "నా UPI transaction reject అయింది.",
                "UPI ద్వారా చెల్లించలేకపోయాను."
            ],
            "kn": [
                "ನನ್ನ UPI payment ವಿಫಲವಾಗಿದೆ.",
                "UPI transaction ತಿರಸ್ಕರಿಸಲಾಗಿದೆ.",
                "UPI ಮೂಲಕ payment ಪೂರ್ಣವಾಗಲಿಲ್ಲ.",
                "ನನ್ನ UPI payment ಯಶಸ್ವಿಯಾಗಲಿಲ್ಲ.",
                "UPI transaction failed ಆಗಿದೆ.",
                "ನನ್ನ UPI payment ಏಕೆ ವಿಫಲವಾಯಿತು?",
                "UPI payment failure ಎಂದು ತೋರಿಸುತ್ತಿದೆ.",
                "UPI ಬಳಸಿದಾಗ payment ವಿಫಲವಾಯಿತು.",
                "ನನ್ನ UPI transaction reject ಆಯಿತು.",
                "UPI ಮೂಲಕ ಪಾವತಿ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ."
            ],
            "ml": [
                "എന്റെ UPI payment പരാജയപ്പെട്ടു.",
                "UPI ഇടപാട് നിരസിക്കപ്പെട്ടു.",
                "UPI വഴി payment പൂർത്തിയാക്കാൻ കഴിഞ്ഞില്ല.",
                "എന്റെ UPI payment വിജയിച്ചില്ല.",
                "UPI transaction failed ആയി.",
                "എന്റെ UPI payment എന്തുകൊണ്ട് പരാജയപ്പെട്ടു?",
                "UPI payment failure എന്ന് കാണിക്കുന്നു.",
                "UPI ഉപയോഗിച്ചപ്പോൾ payment പരാജയപ്പെട്ടു.",
                "എന്റെ UPI transaction reject ആയി.",
                "UPI വഴി പണമടയ്ക്കാൻ കഴിഞ്ഞില്ല."
            ]
        },
        "CARD_PAYMENT_FAILED": {
            "en": [
                "My card payment failed.",
                "The card transaction was declined.",
                "My debit card payment did not go through.",
                "The card payment was unsuccessful.",
                "Why was my card payment rejected?",
                "The payment failed when I used my card.",
                "My card transaction was declined by the bank.",
                "I received a failure message for my card payment.",
                "The merchant could not process my card payment.",
                "I could not complete the payment using my card."
            ],
            "ta": [
                "என் card payment தோல்வியடைந்தது.",
                "என் card transaction நிராகரிக்கப்பட்டது.",
                "Debit card மூலம் payment செல்லவில்லை.",
                "என் card payment வெற்றியளிக்கவில்லை.",
                "என் card payment ஏன் reject ஆனது?",
                "Card பயன்படுத்தியபோது payment தோல்வியடைந்தது.",
                "வங்கி என் card transaction-ஐ நிராகரித்தது.",
                "Card payment failure என்று வருகிறது.",
                "Merchant என் card payment-ஐ செயல்படுத்த முடியவில்லை.",
                "Card மூலம் payment செய்ய முடியவில்லை."
            ],
            "te": [
                "నా card payment విఫలమైంది.",
                "నా card transaction తిరస్కరించబడింది.",
                "Debit card ద్వారా payment జరగలేదు.",
                "నా card payment విజయవంతం కాలేదు.",
                "నా card payment ఎందుకు reject అయింది?",
                "Card ఉపయోగించినప్పుడు payment విఫలమైంది.",
                "బ్యాంక్ నా card transaction ను తిరస్కరించింది.",
                "Card payment failure అని వస్తోంది.",
                "Merchant నా card payment ను process చేయలేకపోయాడు.",
                "Card ద్వారా payment పూర్తి కాలేదు."
            ],
            "kn": [
                "ನನ್ನ card payment ವಿಫಲವಾಗಿದೆ.",
                "ನನ್ನ card transaction ತಿರಸ್ಕರಿಸಲಾಗಿದೆ.",
                "Debit card ಮೂಲಕ payment ಆಗಲಿಲ್ಲ.",
                "ನನ್ನ card payment ಯಶಸ್ವಿಯಾಗಲಿಲ್ಲ.",
                "ನನ್ನ card payment ಏಕೆ reject ಆಯಿತು?",
                "Card ಬಳಸಿದಾಗ payment ವಿಫಲವಾಯಿತು.",
                "ಬ್ಯಾಂಕ್ ನನ್ನ card transaction ಅನ್ನು ತಿರಸ್ಕರಿಸಿತು.",
                "Card payment failure ಎಂದು ತೋರಿಸುತ್ತಿದೆ.",
                "Merchant ನನ್ನ card payment ಅನ್ನು process ಮಾಡಲಿಲ್ಲ.",
                "Card ಮೂಲಕ payment ಪೂರ್ಣಗೊಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ."
            ],
            "ml": [
                "എന്റെ card payment പരാജയപ്പെട്ടു.",
                "എന്റെ card transaction നിരസിക്കപ്പെട്ടു.",
                "Debit card വഴി payment നടന്നില്ല.",
                "എന്റെ card payment വിജയിച്ചില്ല.",
                "എന്റെ card payment എന്തുകൊണ്ട് reject ആയി?",
                "Card ഉപയോഗിച്ചപ്പോൾ payment പരാജയപ്പെട്ടു.",
                "ബാങ്ക് എന്റെ card transaction നിരസിച്ചു.",
                "Card payment failure എന്ന് കാണിക്കുന്നു.",
                "Merchant എന്റെ card payment process ചെയ്യാൻ കഴിഞ്ഞില്ല.",
                "Card ഉപയോഗിച്ച് payment പൂർത്തിയാക്കാൻ കഴിഞ്ഞില്ല."
            ]
        }
    },

    ("ACCOUNT_BALANCE", "TRANSACTION_HISTORY"): {
        "ACCOUNT_BALANCE": {
            "en": [
                "What is my current account balance?",
                "How much money is in my account?",
                "Show me my available balance.",
                "How much can I use from my account?",
                "What is my present balance?",
                "Please check my account balance.",
                "Tell me how much money I have.",
                "What funds are currently available?",
                "Can you show my balance?",
                "How much is left in my account?"
            ],
            "ta": [
                "என் தற்போதைய account balance என்ன?",
                "என் கணக்கில் எவ்வளவு பணம் உள்ளது?",
                "என் available balance-ஐ காட்டுங்கள்.",
                "என் கணக்கில் பயன்படுத்தக்கூடிய தொகை எவ்வளவு?",
                "என் தற்போதைய இருப்பு என்ன?",
                "என் account balance-ஐ சரிபார்க்கவும்.",
                "என்னிடம் எவ்வளவு பணம் உள்ளது?",
                "தற்போது கிடைக்கும் தொகை எவ்வளவு?",
                "என் balance-ஐ காட்ட முடியுமா?",
                "என் கணக்கில் எவ்வளவு மீதம் உள்ளது?"
            ],
            "te": [
                "నా ప్రస్తుత account balance ఎంత?",
                "నా ఖాతాలో ఎంత డబ్బు ఉంది?",
                "నా available balance చూపించండి.",
                "నా ఖాతాలో ఉపయోగించగల మొత్తం ఎంత?",
                "నా ప్రస్తుత బ్యాలెన్స్ ఎంత?",
                "నా account balance చెక్ చేయండి.",
                "నా దగ్గర ఎంత డబ్బు ఉంది?",
                "ప్రస్తుతం అందుబాటులో ఉన్న మొత్తం ఎంత?",
                "నా balance చూపించగలరా?",
                "నా ఖాతాలో ఎంత మిగిలింది?"
            ],
            "kn": [
                "ನನ್ನ ಪ್ರಸ್ತುತ account balance ಎಷ್ಟು?",
                "ನನ್ನ ಖಾತೆಯಲ್ಲಿ ಎಷ್ಟು ಹಣ ಇದೆ?",
                "ನನ್ನ available balance ತೋರಿಸಿ.",
                "ನನ್ನ ಖಾತೆಯಿಂದ ಬಳಸಬಹುದಾದ ಮೊತ್ತ ಎಷ್ಟು?",
                "ನನ್ನ ಪ್ರಸ್ತುತ ಬ್ಯಾಲೆನ್ಸ್ ಎಷ್ಟು?",
                "ನನ್ನ account balance ಪರಿಶೀಲಿಸಿ.",
                "ನನ್ನ ಬಳಿ ಎಷ್ಟು ಹಣ ಇದೆ?",
                "ಈಗ ಲಭ್ಯವಿರುವ ಹಣ ಎಷ್ಟು?",
                "ನನ್ನ balance ತೋರಿಸಬಹುದೇ?",
                "ನನ್ನ ಖಾತೆಯಲ್ಲಿ ಎಷ್ಟು ಉಳಿದಿದೆ?"
            ],
            "ml": [
                "എന്റെ നിലവിലെ account balance എത്രയാണ്?",
                "എന്റെ അക്കൗണ്ടിൽ എത്ര പണമുണ്ട്?",
                "എന്റെ available balance കാണിക്കൂ.",
                "എന്റെ അക്കൗണ്ടിൽ ഉപയോഗിക്കാനാകുന്ന തുക എത്ര?",
                "എന്റെ നിലവിലെ ബാലൻസ് എത്രയാണ്?",
                "എന്റെ account balance പരിശോധിക്കൂ.",
                "എന്റെ കൈവശം എത്ര പണമുണ്ട്?",
                "ഇപ്പോൾ ലഭ്യമായ തുക എത്രയാണ്?",
                "എന്റെ balance കാണിക്കാമോ?",
                "എന്റെ അക്കൗണ്ടിൽ എത്ര ബാക്കി ഉണ്ട്?"
            ]
        },
        "TRANSACTION_HISTORY": {
            "en": [
                "Show my recent transactions.",
                "What transactions happened recently?",
                "Can I see my transaction history?",
                "Show my latest account activity.",
                "What payments were made recently?",
                "List my recent debits and credits.",
                "I want to view my transaction history.",
                "Which transactions occurred this week?",
                "Show my recent account activity.",
                "Can you display my latest transactions?"
            ],
            "ta": [
                "என் சமீபத்திய transactions-ஐ காட்டுங்கள்.",
                "சமீபத்தில் நடந்த transactions என்ன?",
                "என் transaction history-ஐ பார்க்க முடியுமா?",
                "என் சமீபத்திய account activity-ஐ காட்டுங்கள்.",
                "சமீபத்தில் செய்யப்பட்ட payments என்ன?",
                "என் recent debits மற்றும் credits-ஐ பட்டியலிடுங்கள்.",
                "என் transaction history-ஐ பார்க்க வேண்டும்.",
                "இந்த வாரம் நடந்த transactions எவை?",
                "என் சமீபத்திய account activity-ஐ காட்டுங்கள்.",
                "என் latest transactions-ஐ காட்ட முடியுமா?"
            ],
            "te": [
                "నా recent transactions చూపించండి.",
                "ఇటీవల జరిగిన transactions ఏమిటి?",
                "నా transaction history చూడగలనా?",
                "నా తాజా account activity చూపించండి.",
                "ఇటీవల చేసిన payments ఏమిటి?",
                "నా recent debits మరియు credits చూపించండి.",
                "నా transaction history చూడాలి.",
                "ఈ వారం జరిగిన transactions ఏమిటి?",
                "నా తాజా account activity చూపించండి.",
                "నా latest transactions చూపగలరా?"
            ],
            "kn": [
                "ನನ್ನ recent transactions ತೋರಿಸಿ.",
                "ಇತ್ತೀಚೆಗೆ ನಡೆದ transactions ಯಾವುವು?",
                "ನನ್ನ transaction history ನೋಡಬಹುದೇ?",
                "ನನ್ನ ಇತ್ತೀಚಿನ account activity ತೋರಿಸಿ.",
                "ಇತ್ತೀಚೆಗೆ ಮಾಡಿದ payments ಯಾವುವು?",
                "ನನ್ನ recent debits ಮತ್ತು credits ಪಟ್ಟಿ ಮಾಡಿ.",
                "ನನ್ನ transaction history ನೋಡಬೇಕು.",
                "ಈ ವಾರ ನಡೆದ transactions ಯಾವುವು?",
                "ನನ್ನ ಇತ್ತೀಚಿನ account activity ತೋರಿಸಿ.",
                "ನನ್ನ latest transactions ತೋರಿಸಬಹುದೇ?"
            ],
            "ml": [
                "എന്റെ recent transactions കാണിക്കൂ.",
                "അടുത്തിടെ നടന്ന transactions എന്തൊക്കെയാണ്?",
                "എന്റെ transaction history കാണാമോ?",
                "എന്റെ latest account activity കാണിക്കൂ.",
                "അടുത്തിടെ നടത്തിയ payments എന്തൊക്കെയാണ്?",
                "എന്റെ recent debits, credits കാണിക്കൂ.",
                "എന്റെ transaction history കാണണം.",
                "ഈ ആഴ്ച നടന്ന transactions ഏതൊക്കെയാണ്?",
                "എന്റെ latest account activity കാണിക്കൂ.",
                "എന്റെ latest transactions കാണിക്കാമോ?"
            ]
        }
    }
}


# The remaining boundaries use compact language-neutral cues.
# They are generated from the actual language-specific seed examples,
# so assistant/tool metadata remains canonical.
PAIR_TARGETS = [
    ("REFUND_PENDING", "REFUND_RECEIVED"),
    ("CARD_LOST", "CARD_STOLEN"),
    ("KYC_STATUS", "KYC_COMPLETED"),
    ("MERCHANT_NOT_CREDITED", "PAYMENT_FAILED"),
    ("BANK_TRANSFER_FAILED", "BANK_TRANSFER_PENDING"),
    ("UNKNOWN_TRANSACTION", "FRAUD_REPORT"),
    ("DUPLICATE_TRANSACTION", "WRONG_AMOUNT"),
    ("CASH_WITHDRAWAL_FAILED", "CASH_WITHDRAWAL_STATUS"),
]


def clean(text):
    return " ".join(str(text or "").replace("\x00", " ").split())


def key_for(record):
    value = (
        record.get("intent", "")
        + "\n"
        + record.get("language", "")
        + "\n"
        + record.get("user", "")
        + "\n"
        + record.get("assistant", "")
    )

    return hashlib.sha256(
        value.lower().encode("utf-8")
    ).hexdigest()


def main():

    # Load canonical assistant/tool metadata.
    canonical = {}

    with SEED_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if not line.strip():
                continue

            r = json.loads(line)

            k = (
                r.get("intent"),
                r.get("language")
            )

            if k not in canonical:
                canonical[k] = r

    existing = set(
        key_for(r)
        for r in (
            json.loads(x)
            for x in SEED_FILE.open(
                "r",
                encoding="utf-8"
            )
            if x.strip()
        )
    )

    generated = []

    # Explicit high-quality multilingual templates.
    for pair, sides in TEMPLATES.items():

        for intent, languages in sides.items():

            for language, texts in languages.items():

                base = canonical.get(
                    (intent, language)
                )

                if base is None:
                    continue

                for text in texts:

                    record = {
                        "source_dataset": "FinAI-Contrastive-Synthetic",
                        "task_type": "finai_router_contrastive",
                        "intent": intent,
                        "language": language,
                        "user": clean(text),
                        "assistant": base.get("assistant", ""),
                        "risk_level": base.get("risk_level", ""),
                        "requires_tool": base.get("requires_tool", False),
                        "tool_name": base.get("tool_name", ""),
                        "contrastive_pair": (
                            f"{pair[0]} <-> {pair[1]}"
                        )
                    }

                    k = key_for(record)

                    if k not in existing:
                        existing.add(k)
                        generated.append(record)

    # For the remaining pairs, create controlled modifications of real
    # examples by adding a short, same-language clarification cue.
    suffixes = {
        "en": {
            "REFUND_PENDING": [
                " It has not reached my account yet.",
                " I am still waiting for the refund.",
                " The refund is not showing yet."
            ],
            "REFUND_RECEIVED": [
                " I can already see the refund in my account.",
                " The refund has arrived and I want to confirm it.",
                " I received the refunded amount."
            ],
            "CARD_LOST": [
                " I cannot find the card anywhere.",
                " I have physically lost the card.",
                " The card is missing."
            ],
            "CARD_STOLEN": [
                " Someone took the card from me.",
                " My card was stolen.",
                " I believe the card was taken."
            ],
            "KYC_STATUS": [
                " I want to know the current verification status.",
                " I only want to check the verification status.",
                " Please tell me the current KYC status."
            ],
            "KYC_COMPLETED": [
                " I want to confirm that verification is complete.",
                " Please confirm whether my KYC is completed.",
                " I want confirmation that KYC has finished."
            ],
            "MERCHANT_NOT_CREDITED": [
                " My account was debited but the shop did not get it.",
                " The merchant says the money was not received.",
                " I was charged but the merchant has not received it."
            ],
            "BANK_TRANSFER_FAILED": [
                " The transfer was rejected rather than pending.",
                " The bank transfer failed.",
                " The transfer attempt was unsuccessful."
            ],
            "BANK_TRANSFER_PENDING": [
                " The transfer is still waiting to complete.",
                " The bank transfer remains pending.",
                " The transfer has not settled yet."
            ],
            "UNKNOWN_TRANSACTION": [
                " I do not recognize this transaction.",
                " I have no idea what this transaction is.",
                " This transaction is unfamiliar to me."
            ],
            "FRAUD_REPORT": [
                " I think someone may have committed fraud.",
                " I want to report suspected financial fraud.",
                " I believe this activity may be fraudulent."
            ],
            "DUPLICATE_TRANSACTION": [
                " The same charge appears more than once.",
                " I see the same transaction twice.",
                " This looks like a duplicate charge."
            ],
            "WRONG_AMOUNT": [
                " The amount charged is different from what I expected.",
                " The transaction amount is incorrect.",
                " The charged amount is wrong."
            ],
            "CASH_WITHDRAWAL_FAILED": [
                " The ATM withdrawal was declined.",
                " The cash withdrawal attempt failed.",
                " The ATM would not complete the withdrawal."
            ],
            "CASH_WITHDRAWAL_STATUS": [
                " I only want to know the current withdrawal status.",
                " The ATM transaction is still being processed.",
                " I want to check the withdrawal status."
            ]
        }
    }

    for left, right in PAIR_TARGETS:

        for language in LANGUAGES:

            if language != "en":
                continue

            for intent in (left, right):

                base = canonical.get(
                    (intent, language)
                )

                if not base:
                    continue

                # Use up to 10 real seed questions and append
                # a discriminative clarification.
                source_records = []

                with SEED_FILE.open(
                    "r",
                    encoding="utf-8"
                ) as f:

                    for line in f:

                        if not line.strip():
                            continue

                        r = json.loads(line)

                        if (
                            r.get("intent") == intent
                            and r.get("language") == language
                            and len(source_records) < 10
                        ):
                            source_records.append(r)

                for index, source in enumerate(
                    source_records
                ):

                    cues = suffixes[
                        language
                    ].get(
                        intent,
                        []
                    )

                    if not cues:
                        continue

                    cue = cues[
                        index % len(cues)
                    ]

                    question = (
                        clean(
                            source.get("user", "")
                        )
                        + cue
                    )

                    record = {
                        "source_dataset": "FinAI-Contrastive-Synthetic",
                        "task_type": "finai_router_contrastive",
                        "intent": intent,
                        "language": language,
                        "user": question,
                        "assistant": base.get(
                            "assistant",
                            ""
                        ),
                        "risk_level": base.get(
                            "risk_level",
                            ""
                        ),
                        "requires_tool": base.get(
                            "requires_tool",
                            False
                        ),
                        "tool_name": base.get(
                            "tool_name",
                            ""
                        ),
                        "contrastive_pair":
                            f"{left} <-> {right}"
                    }

                    k = key_for(record)

                    if k not in existing:
                        existing.add(k)
                        generated.append(record)

    random.shuffle(generated)

    OUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        for record in generated:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

    by_language = Counter(
        r["language"]
        for r in generated
    )

    by_intent = Counter(
        r["intent"]
        for r in generated
    )

    manifest = {
        "dataset": "FinAI-V3 synthetic contrastive augmentation",
        "records": len(generated),
        "languages": dict(by_language),
        "intents": dict(by_intent),
        "purpose": "Teach boundaries between confusing FinAI intents.",
        "must_not_be_used_as": [
            "validation set",
            "test set"
        ],
        "source_seed": str(SEED_FILE),
        "note": "Synthetic augmentation using approved intent labels and canonical seed metadata."
    }

    MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("=" * 72)
    print("FINAI-V3 CONTRASTIVE AUGMENTATION")
    print("=" * 72)
    print("NEW RECORDS:", len(generated))

    print()
    print("BY LANGUAGE:")
    for k, v in sorted(by_language.items()):
        print(f"  {k}: {v}")

    print()
    print("BY INTENT:")
    for k, v in sorted(by_intent.items()):
        print(f"  {k}: {v}")

    print()
    print("[OK] Dataset:", OUT_FILE)
    print("[OK] Manifest:", MANIFEST)

    print("=" * 72)
    print("CONTRASTIVE AUGMENTATION COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
