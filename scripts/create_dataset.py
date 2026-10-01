import json
from pathlib import Path

OUTPUT = Path("data/financial_intents.jsonl")

examples = [
    # ============================================================
    # 1. PAYMENT_FAILED
    # ============================================================
    {
        "language": "en",
        "intent": "PAYMENT_FAILED",
        "text": "My payment failed",
        "response": "Your payment appears to have failed. Please check the transaction status before trying again."
    },
    {
        "language": "ta",
        "intent": "PAYMENT_FAILED",
        "text": "என் பணம் செலுத்துதல் தோல்வியடைந்தது",
        "response": "உங்கள் பணம் செலுத்துதல் தோல்வியடைந்துள்ளது. மீண்டும் முயற்சிக்கும் முன் பரிவர்த்தனை நிலையைச் சரிபார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "PAYMENT_FAILED",
        "text": "నా చెల్లింపు విఫలమైంది",
        "response": "మీ చెల్లింపు విఫలమైనట్లు కనిపిస్తోంది. మళ్లీ ప్రయత్నించే ముందు లావాదేవీ స్థితిని తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "PAYMENT_FAILED",
        "text": "ನನ್ನ ಪಾವತಿ ವಿಫಲವಾಗಿದೆ",
        "response": "ನಿಮ್ಮ ಪಾವತಿ ವಿಫಲವಾದಂತೆ ಕಾಣುತ್ತಿದೆ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸುವ ಮೊದಲು ವಹಿವಾಟಿನ ಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "PAYMENT_FAILED",
        "text": "എന്റെ പേയ്‌മെന്റ് പരാജയപ്പെട്ടു",
        "response": "നിങ്ങളുടെ പേയ്‌മെന്റ് പരാജയപ്പെട്ടതായി തോന്നുന്നു. വീണ്ടും ശ്രമിക്കുന്നതിന് മുമ്പ് ഇടപാടിന്റെ നില പരിശോധിക്കുക."
    },

    # ============================================================
    # 2. PAYMENT_PENDING
    # ============================================================
    {
        "language": "en",
        "intent": "PAYMENT_PENDING",
        "text": "My payment is still pending",
        "response": "Your payment is currently pending. Please wait for the transaction status to be updated."
    },
    {
        "language": "ta",
        "intent": "PAYMENT_PENDING",
        "text": "என் பணம் செலுத்துதல் இன்னும் நிலுவையில் உள்ளது",
        "response": "உங்கள் பணம் செலுத்துதல் தற்போது நிலுவையில் உள்ளது. பரிவர்த்தனை நிலை புதுப்பிக்கப்படும் வரை காத்திருக்கவும்."
    },
    {
        "language": "te",
        "intent": "PAYMENT_PENDING",
        "text": "నా చెల్లింపు ఇంకా పెండింగ్‌లో ఉంది",
        "response": "మీ చెల్లింపు ప్రస్తుతం పెండింగ్‌లో ఉంది. లావాదేవీ స్థితి నవీకరించబడే వరకు వేచి ఉండండి."
    },
    {
        "language": "kn",
        "intent": "PAYMENT_PENDING",
        "text": "ನನ್ನ ಪಾವತಿ ಇನ್ನೂ ಬಾಕಿಯಿದೆ",
        "response": "ನಿಮ್ಮ ಪಾವತಿ ಪ್ರಸ್ತುತ ಬಾಕಿಯಿದೆ. ವಹಿವಾಟಿನ ಸ್ಥಿತಿ ನವೀಕರಿಸುವವರೆಗೆ ಕಾಯಿರಿ."
    },
    {
        "language": "ml",
        "intent": "PAYMENT_PENDING",
        "text": "എന്റെ പേയ്‌മെന്റ് ഇപ്പോഴും പെൻഡിംഗിലാണ്",
        "response": "നിങ്ങളുടെ പേയ്‌മെന്റ് ഇപ്പോൾ പെൻഡിംഗിലാണ്. ഇടപാടിന്റെ നില പുതുക്കുന്നത് വരെ കാത്തിരിക്കുക."
    },

    # ============================================================
    # 3. PAYMENT_SUCCESS
    # ============================================================
    {
        "language": "en",
        "intent": "PAYMENT_SUCCESS",
        "text": "Was my payment successful?",
        "response": "Please check the transaction status or transaction history to confirm whether the payment was successful."
    },
    {
        "language": "ta",
        "intent": "PAYMENT_SUCCESS",
        "text": "என் பணம் செலுத்துதல் வெற்றிகரமாக நடந்ததா?",
        "response": "பணம் செலுத்துதல் வெற்றிகரமாக நடந்ததா என்பதை அறிய பரிவர்த்தனை நிலை அல்லது வரலாற்றைப் பார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "PAYMENT_SUCCESS",
        "text": "నా చెల్లింపు విజయవంతమైందా?",
        "response": "చెల్లింపు విజయవంతమైందో లేదో తెలుసుకోవడానికి లావాదేవీ స్థితి లేదా చరిత్రను తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "PAYMENT_SUCCESS",
        "text": "ನನ್ನ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆಯೇ?",
        "response": "ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆಯೇ ಎಂದು ತಿಳಿಯಲು ವಹಿವಾಟಿನ ಸ್ಥಿತಿ ಅಥವಾ ಇತಿಹಾಸವನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "PAYMENT_SUCCESS",
        "text": "എന്റെ പേയ്‌മെന്റ് വിജയിച്ചോ?",
        "response": "പേയ്‌മെന്റ് വിജയിച്ചോ എന്ന് സ്ഥിരീകരിക്കാൻ ഇടപാടിന്റെ നിലയോ ചരിത്രമോ പരിശോധിക്കുക."
    },

    # ============================================================
    # 4. REFUND_PENDING
    # ============================================================
    {
        "language": "en",
        "intent": "REFUND_PENDING",
        "text": "Where is my refund?",
        "response": "Your refund may still be processing. Please check the refund status and expected processing time."
    },
    {
        "language": "ta",
        "intent": "REFUND_PENDING",
        "text": "எனது பணத்தைத் திரும்பப் பெறுவது எப்போது?",
        "response": "உங்கள் பணத்தைத் திரும்பப் பெறும் செயல்முறை இன்னும் நடைபெற்று இருக்கலாம். பணத்தைத் திரும்பப் பெறும் நிலையைச் சரிபார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "REFUND_PENDING",
        "text": "నా రీఫండ్ ఎక్కడ ఉంది?",
        "response": "మీ రీఫండ్ ఇంకా ప్రాసెస్ అవుతూ ఉండవచ్చు. రీఫండ్ స్థితి మరియు అంచనా సమయాన్ని తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "REFUND_PENDING",
        "text": "ನನ್ನ ಹಣ ಮರುಪಾವತಿ ಎಲ್ಲಿದೆ?",
        "response": "ನಿಮ್ಮ ಮರುಪಾವತಿ ಇನ್ನೂ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿರಬಹುದು. ಮರುಪಾವತಿಯ ಸ್ಥಿತಿ ಮತ್ತು ನಿರೀಕ್ಷಿತ ಸಮಯವನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "REFUND_PENDING",
        "text": "എന്റെ റീഫണ്ട് എവിടെയാണ്?",
        "response": "നിങ്ങളുടെ റീഫണ്ട് ഇപ്പോഴും പ്രോസസ്സിലായിക്കൊണ്ടിരിക്കാം. റീഫണ്ടിന്റെ നിലയും പ്രതീക്ഷിക്കുന്ന സമയവും പരിശോധിക്കുക."
    },

    # ============================================================
    # 5. MERCHANT_NOT_CREDITED
    # ============================================================
    {
        "language": "en",
        "intent": "MERCHANT_NOT_CREDITED",
        "text": "The merchant has not received my payment",
        "response": "Please verify the transaction status and payment reference before contacting the merchant."
    },
    {
        "language": "ta",
        "intent": "MERCHANT_NOT_CREDITED",
        "text": "வியாபாரிக்கு எனது பணம் கிடைக்கவில்லை",
        "response": "வியாபாரியை தொடர்புகொள்வதற்கு முன் பரிவர்த்தனை நிலை மற்றும் பணம் செலுத்திய குறிப்பு எண்ணைச் சரிபார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "MERCHANT_NOT_CREDITED",
        "text": "వ్యాపారికి నా చెల్లింపు అందలేదు",
        "response": "వ్యాపారిని సంప్రదించే ముందు లావాదేవీ స్థితి మరియు చెల్లింపు రిఫరెన్స్‌ను తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "MERCHANT_NOT_CREDITED",
        "text": "ವ್ಯಾಪಾರಿಗೆ ನನ್ನ ಪಾವತಿ ಬಂದಿಲ್ಲ",
        "response": "ವ್ಯಾಪಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸುವ ಮೊದಲು ವಹಿವಾಟಿನ ಸ್ಥಿತಿ ಮತ್ತು ಪಾವತಿ ಉಲ್ಲೇಖ ಸಂಖ್ಯೆಯನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "MERCHANT_NOT_CREDITED",
        "text": "വ്യാപാരിക്ക് എന്റെ പേയ്‌മെന്റ് ലഭിച്ചിട്ടില്ല",
        "response": "വ്യാപാരിയെ ബന്ധപ്പെടുന്നതിന് മുമ്പ് ഇടപാടിന്റെ നിലയും പേയ്‌മെന്റ് റഫറൻസും പരിശോധിക്കുക."
    },

    # ============================================================
    # 6. UNKNOWN_TRANSACTION
    # ============================================================
    {
        "language": "en",
        "intent": "UNKNOWN_TRANSACTION",
        "text": "I don't recognize this transaction",
        "response": "If you do not recognize the transaction, review the transaction details and report it through the official dispute or fraud process."
    },
    {
        "language": "ta",
        "intent": "UNKNOWN_TRANSACTION",
        "text": "இந்த பரிவர்த்தனை எனக்கு தெரியவில்லை",
        "response": "இந்த பரிவர்த்தனை உங்களுடையது அல்ல என்றால் அதன் விவரங்களைச் சரிபார்த்து அதிகாரப்பூர்வ புகார் அல்லது மோசடி அறிக்கை முறையைப் பயன்படுத்தவும்."
    },
    {
        "language": "te",
        "intent": "UNKNOWN_TRANSACTION",
        "text": "ఈ లావాదేవీ నాకు తెలియదు",
        "response": "ఈ లావాదేవీ మీది కాదని అనిపిస్తే వివరాలను తనిఖీ చేసి అధికారిక వివాదం లేదా మోసం నివేదిక ప్రక్రియను ఉపయోగించండి."
    },
    {
        "language": "kn",
        "intent": "UNKNOWN_TRANSACTION",
        "text": "ಈ ವಹಿವಾಟು ನನಗೆ ತಿಳಿದಿಲ್ಲ",
        "response": "ಈ ವಹಿವಾಟು ನಿಮ್ಮದು ಅಲ್ಲದಿದ್ದರೆ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತು ಅಧಿಕೃತ ವಿವಾದ ಅಥವಾ ವಂಚನೆ ವರದಿ ಪ್ರಕ್ರಿಯೆಯನ್ನು ಬಳಸಿ."
    },
    {
        "language": "ml",
        "intent": "UNKNOWN_TRANSACTION",
        "text": "ഈ ഇടപാട് എന്റേതല്ല",
        "response": "ഈ ഇടപാട് നിങ്ങളുടേതല്ലെങ്കിൽ ഇടപാട് വിവരങ്ങൾ പരിശോധിച്ച് ഔദ്യോഗിക തർക്കമോ തട്ടിപ്പ് റിപ്പോർട്ടിംഗ് സംവിധാനമോ ഉപയോഗിക്കുക."
    },

    # ============================================================
    # 7. FRAUD_REPORT
    # ============================================================
    {
        "language": "en",
        "intent": "FRAUD_REPORT",
        "text": "I think someone used my account without permission",
        "response": "Secure your account immediately and report the suspicious activity through the official fraud reporting process."
    },
    {
        "language": "ta",
        "intent": "FRAUD_REPORT",
        "text": "யாரோ என் கணக்கை அனுமதியின்றி பயன்படுத்தியதாக நினைக்கிறேன்",
        "response": "உங்கள் கணக்கைப் பாதுகாத்து, சந்தேகத்திற்கிடமான செயல்பாட்டை அதிகாரப்பூர்வ மோசடி அறிக்கை முறையில் தெரிவிக்கவும்."
    },
    {
        "language": "te",
        "intent": "FRAUD_REPORT",
        "text": "ఎవరో నా ఖాతాను అనుమతి లేకుండా ఉపయోగించినట్లు అనిపిస్తోంది",
        "response": "మీ ఖాతాను వెంటనే సురక్షితం చేసి అనుమానాస్పద కార్యకలాపాన్ని అధికారిక మోసం నివేదిక ప్రక్రియ ద్వారా తెలియజేయండి."
    },
    {
        "language": "kn",
        "intent": "FRAUD_REPORT",
        "text": "ಯಾರೋ ನನ್ನ ಖಾತೆಯನ್ನು ಅನುಮತಿಯಿಲ್ಲದೆ ಬಳಸಿದ್ದಾರೆ ಎಂದು ಅನಿಸುತ್ತದೆ",
        "response": "ನಿಮ್ಮ ಖಾತೆಯನ್ನು ತಕ್ಷಣ ಸುರಕ್ಷಿತಗೊಳಿಸಿ ಮತ್ತು ಅನುಮಾನಾಸ್ಪದ ಚಟುವಟಿಕೆಯನ್ನು ಅಧಿಕೃತ ವಂಚನೆ ವರದಿ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ತಿಳಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "FRAUD_REPORT",
        "text": "ആരോ എന്റെ അക്കൗണ്ട് അനുമതിയില്ലാതെ ഉപയോഗിച്ചതായി തോന്നുന്നു",
        "response": "നിങ്ങളുടെ അക്കൗണ്ട് ഉടൻ സുരക്ഷിതമാക്കി സംശയാസ്പദമായ പ്രവർത്തനം ഔദ്യോഗിക തട്ടിപ്പ് റിപ്പോർട്ടിംഗ് സംവിധാനത്തിലൂടെ അറിയിക്കുക."
    },

    # ============================================================
    # 8. ACCOUNT_BALANCE
    # ============================================================
    {
        "language": "en",
        "intent": "ACCOUNT_BALANCE",
        "text": "What is my account balance?",
        "response": "Your current balance can be checked securely through your bank or payment application's official balance section."
    },
    {
        "language": "ta",
        "intent": "ACCOUNT_BALANCE",
        "text": "எனது கணக்கு இருப்பு எவ்வளவு?",
        "response": "உங்கள் தற்போதைய கணக்கு இருப்பை அதிகாரப்பூர்வ வங்கி அல்லது பணப்பரிவர்த்தனை செயலியின் இருப்புப் பகுதியில் பாதுகாப்பாக பார்க்கலாம்."
    },
    {
        "language": "te",
        "intent": "ACCOUNT_BALANCE",
        "text": "నా ఖాతా బ్యాలెన్స్ ఎంత?",
        "response": "మీ ప్రస్తుత ఖాతా బ్యాలెన్స్‌ను అధికారిక బ్యాంకింగ్ లేదా చెల్లింపు యాప్‌లోని బ్యాలెన్స్ విభాగంలో సురక్షితంగా చూడవచ్చు."
    },
    {
        "language": "kn",
        "intent": "ACCOUNT_BALANCE",
        "text": "ನನ್ನ ಖಾತೆಯ ಬ್ಯಾಲೆನ್ಸ್ ಎಷ್ಟು?",
        "response": "ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಖಾತೆಯ ಬ್ಯಾಲೆನ್ಸ್ ಅನ್ನು ಅಧಿಕೃತ ಬ್ಯಾಂಕ್ ಅಥವಾ ಪಾವತಿ ಅಪ್ಲಿಕೇಶನ್‌ನ ಬ್ಯಾಲೆನ್ಸ್ ವಿಭಾಗದಲ್ಲಿ ಸುರಕ್ಷಿತವಾಗಿ ಪರಿಶೀಲಿಸಬಹುದು."
    },
    {
        "language": "ml",
        "intent": "ACCOUNT_BALANCE",
        "text": "എന്റെ അക്കൗണ്ട് ബാലൻസ് എത്രയാണ്?",
        "response": "നിങ്ങളുടെ നിലവിലെ അക്കൗണ്ട് ബാലൻസ് ഔദ്യോഗിക ബാങ്കിംഗ് അല്ലെങ്കിൽ പേയ്‌മെന്റ് ആപ്പിലെ ബാലൻസ് വിഭാഗത്തിൽ സുരക്ഷിതമായി പരിശോധിക്കാം."
    },

    # ============================================================
    # 9. TRANSACTION_HISTORY
    # ============================================================
    {
        "language": "en",
        "intent": "TRANSACTION_HISTORY",
        "text": "Show me my recent transactions",
        "response": "You can view recent transactions securely in the transaction history section of your official financial application."
    },
    {
        "language": "ta",
        "intent": "TRANSACTION_HISTORY",
        "text": "எனது சமீபத்திய பரிவர்த்தனைகளை காட்டுங்கள்",
        "response": "உங்கள் அதிகாரப்பூர்வ நிதி செயலியின் பரிவர்த்தனை வரலாறு பகுதியில் சமீபத்திய பரிவர்த்தனைகளை பாதுகாப்பாக பார்க்கலாம்."
    },
    {
        "language": "te",
        "intent": "TRANSACTION_HISTORY",
        "text": "నా ఇటీవలి లావాదేవీలను చూపించండి",
        "response": "మీ అధికారిక ఆర్థిక యాప్‌లోని లావాదేవీ చరిత్ర విభాగంలో ఇటీవలి లావాదేవీలను సురక్షితంగా చూడవచ్చు."
    },
    {
        "language": "kn",
        "intent": "TRANSACTION_HISTORY",
        "text": "ನನ್ನ ಇತ್ತೀಚಿನ ವಹಿವಾಟುಗಳನ್ನು ತೋರಿಸಿ",
        "response": "ನಿಮ್ಮ ಅಧಿಕೃತ ಹಣಕಾಸು ಅಪ್ಲಿಕೇಶನ್‌ನ ವಹಿವಾಟು ಇತಿಹಾಸ ವಿಭಾಗದಲ್ಲಿ ಇತ್ತೀಚಿನ ವಹಿವಾಟುಗಳನ್ನು ಸುರಕ್ಷಿತವಾಗಿ ನೋಡಬಹುದು."
    },
    {
        "language": "ml",
        "intent": "TRANSACTION_HISTORY",
        "text": "എന്റെ അടുത്തകാലത്തെ ഇടപാടുകൾ കാണിക്കുക",
        "response": "നിങ്ങളുടെ ഔദ്യോഗിക സാമ്പത്തിക ആപ്പിലെ ഇടപാട് ചരിത്ര വിഭാഗത്തിൽ അടുത്തകാലത്തെ ഇടപാടുകൾ സുരക്ഷിതമായി കാണാം."
    },

    # ============================================================
    # 10. CARD_LOST
    # ============================================================
    {
        "language": "en",
        "intent": "CARD_LOST",
        "text": "I lost my card",
        "response": "Block the card immediately using your official banking application or contact your bank through its official support channel."
    },
    {
        "language": "ta",
        "intent": "CARD_LOST",
        "text": "எனது கார்டை தொலைத்துவிட்டேன்",
        "response": "உங்கள் அதிகாரப்பூர்வ வங்கி செயலி மூலம் கார்டை உடனடியாக முடக்கவும் அல்லது வங்கியின் அதிகாரப்பூர்வ உதவி மையத்தைத் தொடர்புகொள்ளவும்."
    },
    {
        "language": "te",
        "intent": "CARD_LOST",
        "text": "నా కార్డు పోయింది",
        "response": "మీ అధికారిక బ్యాంకింగ్ యాప్ ద్వారా కార్డును వెంటనే బ్లాక్ చేయండి లేదా బ్యాంకు అధికారిక సహాయ కేంద్రాన్ని సంప్రదించండి."
    },
    {
        "language": "kn",
        "intent": "CARD_LOST",
        "text": "ನನ್ನ ಕಾರ್ಡ್ ಕಳೆದುಹೋಗಿದೆ",
        "response": "ನಿಮ್ಮ ಅಧಿಕೃತ ಬ್ಯಾಂಕಿಂಗ್ ಅಪ್ಲಿಕೇಶನ್ ಮೂಲಕ ಕಾರ್ಡ್ ಅನ್ನು ತಕ್ಷಣ ಬ್ಲಾಕ್ ಮಾಡಿ ಅಥವಾ ಬ್ಯಾಂಕಿನ ಅಧಿಕೃತ ಸಹಾಯವಾಣಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "CARD_LOST",
        "text": "എന്റെ കാർഡ് നഷ്ടപ്പെട്ടു",
        "response": "നിങ്ങളുടെ ഔദ്യോഗിക ബാങ്കിംഗ് ആപ്പ് ഉപയോഗിച്ച് കാർഡ് ഉടൻ ബ്ലോക്ക് ചെയ്യുക അല്ലെങ്കിൽ ബാങ്കിന്റെ ഔദ്യോഗിക സഹായകേന്ദ്രവുമായി ബന്ധപ്പെടുക."
    },

    # ============================================================
    # 11. CARD_BLOCK
    # ============================================================
    {
        "language": "en",
        "intent": "CARD_BLOCK",
        "text": "How can I block my card?",
        "response": "You can block your card through your official banking application or by contacting your bank's official support."
    },
    {
        "language": "ta",
        "intent": "CARD_BLOCK",
        "text": "எனது கார்டை எப்படி முடக்குவது?",
        "response": "உங்கள் அதிகாரப்பூர்வ வங்கி செயலி அல்லது வங்கியின் அதிகாரப்பூர்வ உதவி மையம் மூலம் கார்டை முடக்கலாம்."
    },
    {
        "language": "te",
        "intent": "CARD_BLOCK",
        "text": "నా కార్డును ఎలా బ్లాక్ చేయాలి?",
        "response": "మీ అధికారిక బ్యాంకింగ్ యాప్ లేదా బ్యాంకు అధికారిక సహాయ కేంద్రం ద్వారా కార్డును బ్లాక్ చేయవచ్చు."
    },
    {
        "language": "kn",
        "intent": "CARD_BLOCK",
        "text": "ನನ್ನ ಕಾರ್ಡ್ ಅನ್ನು ಹೇಗೆ ಬ್ಲಾಕ್ ಮಾಡುವುದು?",
        "response": "ನಿಮ್ಮ ಅಧಿಕೃತ ಬ್ಯಾಂಕಿಂಗ್ ಅಪ್ಲಿಕೇಶನ್ ಅಥವಾ ಬ್ಯಾಂಕಿನ ಅಧಿಕೃತ ಸಹಾಯವಾಣಿ ಮೂಲಕ ಕಾರ್ಡ್ ಅನ್ನು ಬ್ಲಾಕ್ ಮಾಡಬಹುದು."
    },
    {
        "language": "ml",
        "intent": "CARD_BLOCK",
        "text": "എന്റെ കാർഡ് എങ്ങനെ ബ്ലോക്ക് ചെയ്യാം?",
        "response": "നിങ്ങളുടെ ഔദ്യോഗിക ബാങ്കിംഗ് ആപ്പ് അല്ലെങ്കിൽ ബാങ്കിന്റെ ഔദ്യോഗിക സഹായകേന്ദ്രം വഴി കാർഡ് ബ്ലോക്ക് ചെയ്യാം."
    },

    # ============================================================
    # 12. KYC_STATUS
    # ============================================================
    {
        "language": "en",
        "intent": "KYC_STATUS",
        "text": "What is the status of my KYC?",
        "response": "You can check your KYC status through the official account or financial service application."
    },
    {
        "language": "ta",
        "intent": "KYC_STATUS",
        "text": "எனது KYC நிலை என்ன?",
        "response": "உங்கள் அதிகாரப்பூர்வ கணக்கு அல்லது நிதி சேவை செயலியில் KYC நிலையைச் சரிபார்க்கலாம்."
    },
    {
        "language": "te",
        "intent": "KYC_STATUS",
        "text": "నా KYC స్థితి ఏమిటి?",
        "response": "మీ అధికారిక ఖాతా లేదా ఆర్థిక సేవా యాప్‌లో KYC స్థితిని తనిఖీ చేయవచ్చు."
    },
    {
        "language": "kn",
        "intent": "KYC_STATUS",
        "text": "ನನ್ನ KYC ಸ್ಥಿತಿ ಏನು?",
        "response": "ನಿಮ್ಮ ಅಧಿಕೃತ ಖಾತೆ ಅಥವಾ ಹಣಕಾಸು ಸೇವಾ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ KYC ಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಬಹುದು."
    },
    {
        "language": "ml",
        "intent": "KYC_STATUS",
        "text": "എന്റെ KYC നില എന്താണ്?",
        "response": "നിങ്ങളുടെ ഔദ്യോഗിക അക്കൗണ്ട് അല്ലെങ്കിൽ സാമ്പത്തിക സേവന ആപ്പിൽ KYC നില പരിശോധിക്കാം."
    },

    # ============================================================
    # 13. KYC_FAILED
    # ============================================================
    {
        "language": "en",
        "intent": "KYC_FAILED",
        "text": "My KYC verification failed",
        "response": "Please check whether your submitted information and documents are correct and follow the official KYC re-verification process."
    },
    {
        "language": "ta",
        "intent": "KYC_FAILED",
        "text": "எனது KYC சரிபார்ப்பு தோல்வியடைந்தது",
        "response": "நீங்கள் சமர்ப்பித்த தகவல்கள் மற்றும் ஆவணங்கள் சரியாக உள்ளதா என்பதைச் சரிபார்த்து அதிகாரப்பூர்வ KYC மீள் சரிபார்ப்பு முறையைப் பின்பற்றவும்."
    },
    {
        "language": "te",
        "intent": "KYC_FAILED",
        "text": "నా KYC ధృవీకరణ విఫలమైంది",
        "response": "మీరు సమర్పించిన సమాచారం మరియు పత్రాలు సరైనవో లేదో తనిఖీ చేసి అధికారిక KYC పునఃధృవీకరణ ప్రక్రియను అనుసరించండి."
    },
    {
        "language": "kn",
        "intent": "KYC_FAILED",
        "text": "ನನ್ನ KYC ಪರಿಶೀಲನೆ ವಿಫಲವಾಗಿದೆ",
        "response": "ನೀವು ಸಲ್ಲಿಸಿದ ಮಾಹಿತಿ ಮತ್ತು ದಾಖಲೆಗಳು ಸರಿಯಾಗಿವೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸಿ ಅಧಿಕೃತ KYC ಮರುಪರಿಶೀಲನೆ ಪ್ರಕ್ರಿಯೆಯನ್ನು ಅನುಸರಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "KYC_FAILED",
        "text": "എന്റെ KYC പരിശോധന പരാജയപ്പെട്ടു",
        "response": "നിങ്ങൾ സമർപ്പിച്ച വിവരങ്ങളും രേഖകളും ശരിയാണെന്ന് പരിശോധിച്ച് ഔദ്യോഗിക KYC പുനഃപരിശോധന നടപടിക്രമം പിന്തുടരുക."
    },

    # ============================================================
    # 14. BANK_TRANSFER_FAILED
    # ============================================================
    {
        "language": "en",
        "intent": "BANK_TRANSFER_FAILED",
        "text": "My bank transfer failed",
        "response": "Check the transfer status and beneficiary details before attempting the transfer again."
    },
    {
        "language": "ta",
        "intent": "BANK_TRANSFER_FAILED",
        "text": "எனது வங்கி பரிமாற்றம் தோல்வியடைந்தது",
        "response": "மீண்டும் பணம் அனுப்புவதற்கு முன் பரிமாற்ற நிலை மற்றும் பெறுநர் விவரங்களைச் சரிபார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "BANK_TRANSFER_FAILED",
        "text": "నా బ్యాంక్ బదిలీ విఫలమైంది",
        "response": "మళ్లీ బదిలీ చేయడానికి ముందు బదిలీ స్థితి మరియు లబ్ధిదారుడి వివరాలను తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "BANK_TRANSFER_FAILED",
        "text": "ನನ್ನ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ ವಿಫಲವಾಗಿದೆ",
        "response": "ಮತ್ತೆ ವರ್ಗಾವಣೆ ಮಾಡುವ ಮೊದಲು ವರ್ಗಾವಣೆಯ ಸ್ಥಿತಿ ಮತ್ತು ಫಲಾನುಭವಿಯ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "BANK_TRANSFER_FAILED",
        "text": "എന്റെ ബാങ്ക് ട്രാൻസ്ഫർ പരാജയപ്പെട്ടു",
        "response": "വീണ്ടും ട്രാൻസ്ഫർ ചെയ്യുന്നതിന് മുമ്പ് ട്രാൻസ്ഫർ നിലയും ഗുണഭോക്താവിന്റെ വിവരങ്ങളും പരിശോധിക്കുക."
    },

    # ============================================================
    # 15. BANK_TRANSFER_PENDING
    # ============================================================
    {
        "language": "en",
        "intent": "BANK_TRANSFER_PENDING",
        "text": "My bank transfer is pending",
        "response": "Your bank transfer is currently pending. Check the transfer status for updates."
    },
    {
        "language": "ta",
        "intent": "BANK_TRANSFER_PENDING",
        "text": "எனது வங்கி பரிமாற்றம் நிலுவையில் உள்ளது",
        "response": "உங்கள் வங்கி பரிமாற்றம் தற்போது நிலுவையில் உள்ளது. புதுப்பிப்புகளுக்கு பரிமாற்ற நிலையைச் சரிபார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "BANK_TRANSFER_PENDING",
        "text": "నా బ్యాంక్ బదిలీ పెండింగ్‌లో ఉంది",
        "response": "మీ బ్యాంక్ బదిలీ ప్రస్తుతం పెండింగ్‌లో ఉంది. నవీకరణల కోసం బదిలీ స్థితిని తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "BANK_TRANSFER_PENDING",
        "text": "ನನ್ನ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ ಬಾಕಿಯಿದೆ",
        "response": "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ ಪ್ರಸ್ತುತ ಬಾಕಿಯಿದೆ. ನವೀಕರಣಗಳಿಗಾಗಿ ವರ್ಗಾವಣೆಯ ಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "BANK_TRANSFER_PENDING",
        "text": "എന്റെ ബാങ്ക് ട്രാൻസ്ഫർ പെൻഡിംഗിലാണ്",
        "response": "നിങ്ങളുടെ ബാങ്ക് ട്രാൻസ്ഫർ ഇപ്പോൾ പെൻഡിംഗിലാണ്. പുതുക്കലുകൾക്കായി ട്രാൻസ്ഫർ നില പരിശോധിക്കുക."
    },

    # ============================================================
    # 16. EMI_QUERY
    # ============================================================
    {
        "language": "en",
        "intent": "EMI_QUERY",
        "text": "How much is my monthly EMI?",
        "response": "Your exact EMI amount depends on your loan agreement. Check the official loan account for the scheduled EMI."
    },
    {
        "language": "ta",
        "intent": "EMI_QUERY",
        "text": "எனது மாதாந்திர EMI எவ்வளவு?",
        "response": "உங்கள் சரியான EMI தொகை கடன் ஒப்பந்தத்தைப் பொறுத்தது. அதிகாரப்பூர்வ கடன் கணக்கில் திட்டமிடப்பட்ட EMI-ஐப் பார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "EMI_QUERY",
        "text": "నా నెలవారీ EMI ఎంత?",
        "response": "మీ ఖచ్చితమైన EMI మొత్తం రుణ ఒప్పందంపై ఆధారపడి ఉంటుంది. అధికారిక రుణ ఖాతాలో షెడ్యూల్ చేసిన EMIని తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "EMI_QUERY",
        "text": "ನನ್ನ ಮಾಸಿಕ EMI ಎಷ್ಟು?",
        "response": "ನಿಮ್ಮ ನಿಖರವಾದ EMI ಮೊತ್ತವು ಸಾಲದ ಒಪ್ಪಂದವನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ. ಅಧಿಕೃತ ಸಾಲ ಖಾತೆಯಲ್ಲಿ ನಿಗದಿಪಡಿಸಿದ EMI ಅನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "EMI_QUERY",
        "text": "എന്റെ പ്രതിമാസ EMI എത്രയാണ്?",
        "response": "നിങ്ങളുടെ കൃത്യമായ EMI തുക വായ്പാ കരാറിനെ ആശ്രയിച്ചിരിക്കും. ഔദ്യോഗിക വായ്പാ അക്കൗണ്ടിൽ നിശ്ചയിച്ച EMI പരിശോധിക്കുക."
    },

    # ============================================================
    # 17. INTEREST_QUERY
    # ============================================================
    {
        "language": "en",
        "intent": "INTEREST_QUERY",
        "text": "What is the interest rate on my loan?",
        "response": "Your applicable interest rate depends on your loan agreement. Check the official loan documents or account."
    },
    {
        "language": "ta",
        "intent": "INTEREST_QUERY",
        "text": "எனது கடனுக்கான வட்டி விகிதம் என்ன?",
        "response": "உங்கள் கடனுக்கான வட்டி விகிதம் கடன் ஒப்பந்தத்தைப் பொறுத்தது. அதிகாரப்பூர்வ கடன் ஆவணங்கள் அல்லது கணக்கைப் பார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "INTEREST_QUERY",
        "text": "నా రుణంపై వడ్డీ రేటు ఎంత?",
        "response": "మీ రుణానికి వర్తించే వడ్డీ రేటు రుణ ఒప్పందంపై ఆధారపడి ఉంటుంది. అధికారిక రుణ పత్రాలు లేదా ఖాతాను తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "INTEREST_QUERY",
        "text": "ನನ್ನ ಸಾಲದ ಬಡ್ಡಿ ದರ ಎಷ್ಟು?",
        "response": "ನಿಮ್ಮ ಸಾಲಕ್ಕೆ ಅನ್ವಯಿಸುವ ಬಡ್ಡಿ ದರವು ಸಾಲದ ಒಪ್ಪಂದವನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ. ಅಧಿಕೃತ ಸಾಲದ ದಾಖಲೆಗಳು ಅಥವಾ ಖಾತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "INTEREST_QUERY",
        "text": "എന്റെ വായ്പയുടെ പലിശ നിരക്ക് എത്രയാണ്?",
        "response": "നിങ്ങളുടെ വായ്പയ്ക്ക് ബാധകമായ പലിശ നിരക്ക് വായ്പാ കരാറിനെ ആശ്രയിച്ചിരിക്കും. ഔദ്യോഗിക വായ്പാ രേഖകളോ അക്കൗണ്ടോ പരിശോധിക്കുക."
    },

    # ============================================================
    # 18. LIMIT_QUERY
    # ============================================================
    {
        "language": "en",
        "intent": "LIMIT_QUERY",
        "text": "What is my payment limit?",
        "response": "Your payment limit depends on the account and payment service. Check the official application for the current limit."
    },
    {
        "language": "ta",
        "intent": "LIMIT_QUERY",
        "text": "எனது பணம் செலுத்தும் வரம்பு என்ன?",
        "response": "உங்கள் பணம் செலுத்தும் வரம்பு கணக்கு மற்றும் சேவையைப் பொறுத்தது. தற்போதைய வரம்பை அதிகாரப்பூர்வ செயலியில் பார்க்கவும்."
    },
    {
        "language": "te",
        "intent": "LIMIT_QUERY",
        "text": "నా చెల్లింపు పరిమితి ఎంత?",
        "response": "మీ చెల్లింపు పరిమితి ఖాతా మరియు చెల్లింపు సేవపై ఆధారపడి ఉంటుంది. ప్రస్తుత పరిమితిని అధికారిక యాప్‌లో తనిఖీ చేయండి."
    },
    {
        "language": "kn",
        "intent": "LIMIT_QUERY",
        "text": "ನನ್ನ ಪಾವತಿ ಮಿತಿ ಎಷ್ಟು?",
        "response": "ನಿಮ್ಮ ಪಾವತಿ ಮಿತಿಯು ಖಾತೆ ಮತ್ತು ಪಾವತಿ ಸೇವೆಯನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ. ಪ್ರಸ್ತುತ ಮಿತಿಯನ್ನು ಅಧಿಕೃತ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "LIMIT_QUERY",
        "text": "എന്റെ പേയ്‌മെന്റ് പരിധി എത്രയാണ്?",
        "response": "നിങ്ങളുടെ പേയ്‌മെന്റ് പരിധി അക്കൗണ്ടും പേയ്‌മെന്റ് സേവനവും ആശ്രയിച്ചിരിക്കും. നിലവിലെ പരിധി ഔദ്യോഗിക ആപ്പിൽ പരിശോധിക്കുക."
    },

    # ============================================================
    # 19. DISPUTE_TRANSACTION
    # ============================================================
    {
        "language": "en",
        "intent": "DISPUTE_TRANSACTION",
        "text": "I want to dispute a transaction",
        "response": "Review the transaction details and submit a dispute through the official financial service process."
    },
    {
        "language": "ta",
        "intent": "DISPUTE_TRANSACTION",
        "text": "ஒரு பரிவர்த்தனை குறித்து புகார் செய்ய விரும்புகிறேன்",
        "response": "பரிவர்த்தனை விவரங்களைச் சரிபார்த்து அதிகாரப்பூர்வ நிதி சேவை முறையின் மூலம் புகாரைச் சமர்ப்பிக்கவும்."
    },
    {
        "language": "te",
        "intent": "DISPUTE_TRANSACTION",
        "text": "నేను ఒక లావాదేవీపై వివాదం నమోదు చేయాలనుకుంటున్నాను",
        "response": "లావాదేవీ వివరాలను సమీక్షించి అధికారిక ఆర్థిక సేవా ప్రక్రియ ద్వారా వివాదాన్ని నమోదు చేయండి."
    },
    {
        "language": "kn",
        "intent": "DISPUTE_TRANSACTION",
        "text": "ನಾನು ಒಂದು ವಹಿವಾಟಿನ ಬಗ್ಗೆ ದೂರು ನೀಡಲು ಬಯಸುತ್ತೇನೆ",
        "response": "ವಹಿವಾಟಿನ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಅಧಿಕೃತ ಹಣಕಾಸು ಸೇವಾ ಪ್ರಕ್ರಿಯೆಯ ಮೂಲಕ ವಿವಾದವನ್ನು ಸಲ್ಲಿಸಿ."
    },
    {
        "language": "ml",
        "intent": "DISPUTE_TRANSACTION",
        "text": "ഒരു ഇടപാടിനെക്കുറിച്ച് തർക്കം ഉന്നയിക്കണം",
        "response": "ഇടപാട് വിവരങ്ങൾ പരിശോധിച്ച് ഔദ്യോഗിക സാമ്പത്തിക സേവന നടപടിക്രമത്തിലൂടെ തർക്കം സമർപ്പിക്കുക."
    },

    # ============================================================
    # 20. SUPPORT_REQUEST
    # ============================================================
    {
        "language": "en",
        "intent": "SUPPORT_REQUEST",
        "text": "I need help with my account",
        "response": "Please describe the issue you are facing so that the appropriate support process can be identified."
    },
    {
        "language": "ta",
        "intent": "SUPPORT_REQUEST",
        "text": "எனது கணக்கு தொடர்பாக உதவி வேண்டும்",
        "response": "நீங்கள் எதிர்கொள்ளும் பிரச்சினையை விவரிக்கவும். அதற்கான சரியான உதவி முறையைத் தேர்ந்தெடுக்கலாம்."
    },
    {
        "language": "te",
        "intent": "SUPPORT_REQUEST",
        "text": "నా ఖాతాకు సంబంధించి నాకు సహాయం కావాలి",
        "response": "మీరు ఎదుర్కొంటున్న సమస్యను వివరించండి. దానికి తగిన సహాయ ప్రక్రియను గుర్తించవచ్చు."
    },
    {
        "language": "kn",
        "intent": "SUPPORT_REQUEST",
        "text": "ನನ್ನ ಖಾತೆಯ ಬಗ್ಗೆ ನನಗೆ ಸಹಾಯ ಬೇಕು",
        "response": "ನೀವು ಎದುರಿಸುತ್ತಿರುವ ಸಮಸ್ಯೆಯನ್ನು ವಿವರಿಸಿ. ಸೂಕ್ತವಾದ ಸಹಾಯ ಪ್ರಕ್ರಿಯೆಯನ್ನು ಗುರುತಿಸಬಹುದು."
    },
    {
        "language": "ml",
        "intent": "SUPPORT_REQUEST",
        "text": "എന്റെ അക്കൗണ്ടുമായി ബന്ധപ്പെട്ട് സഹായം വേണം",
        "response": "നിങ്ങൾ നേരിടുന്ന പ്രശ്നം വിശദീകരിക്കുക. അതിന് അനുയോജ്യമായ സഹായ നടപടിക്രമം കണ്ടെത്താം."
    }
]


def validate_dataset(data):
    required = {"language", "intent", "text", "response"}

    for i, item in enumerate(data, start=1):
        missing = required - item.keys()

        if missing:
            raise ValueError(
                f"Example {i} is missing fields: {missing}"
            )

        if not item["text"].strip():
            raise ValueError(f"Example {i} has empty text")

        if not item["response"].strip():
            raise ValueError(f"Example {i} has empty response")


def main():
    validate_dataset(examples)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        for item in examples:
            f.write(
                json.dumps(
                    item,
                    ensure_ascii=False
                ) + "\n"
            )

    languages = sorted(set(x["language"] for x in examples))
    intents = sorted(set(x["intent"] for x in examples))

    print("=" * 60)
    print("FINAI DATASET CREATED")
    print("=" * 60)
    print(f"Total examples : {len(examples)}")
    print(f"Languages      : {len(languages)}")
    print(f"Intents        : {len(intents)}")
    print(f"Output         : {OUTPUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()