
import streamlit as st
from google import genai
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime, timezone

st.set_page_config(
    page_title="My Cat's Choice 3.0",
    page_icon="🐱",
    layout="wide"
)

LANGUAGES = {
    "English": "English",
    "ไทย": "Thai",
    "中文": "Chinese",
    "Deutsch": "German",
    "العربية": "Arabic",
    "हिन्दी": "Hindi"
}

TEXT = {
    "English": ["Choose your language", "Product A", "Product B",
                "Upload photos", "Take a photo", "Price", "Currency",
                "Quantity", "What matters to you?",
                "Compare Products", "Your AI Comparison"],
    "ไทย": ["เลือกภาษา", "สินค้า A", "สินค้า B",
            "อัปโหลดรูปภาพ", "ถ่ายภาพ", "ราคา", "สกุลเงิน",
            "จำนวน", "คุณให้ความสำคัญกับอะไร?",
            "เปรียบเทียบสินค้า", "ผลการเปรียบเทียบ AI"],
    "中文": ["选择语言", "产品 A", "产品 B",
            "上传照片", "拍照", "价格", "货币",
            "数量", "您最看重什么？", "比较产品", "AI 比较结果"],
    "Deutsch": ["Sprache wählen", "Produkt A", "Produkt B",
                "Fotos hochladen", "Foto aufnehmen", "Preis", "Währung",
                "Menge", "Was ist Ihnen wichtig?",
                "Produkte vergleichen", "Ihr KI-Vergleich"],
    "العربية": ["اختر اللغة", "المنتج A", "المنتج B",
                "تحميل الصور", "التقاط صورة", "السعر", "العملة",
                "الكمية", "ما الذي يهمك؟",
                "قارن المنتجات", "مقارنة الذكاء الاصطناعي"],
    "हिन्दी": ["भाषा चुनें", "उत्पाद A", "उत्पाद B",
              "फोटो अपलोड करें", "फोटो लें", "कीमत", "मुद्रा",
              "मात्रा", "आपके लिए क्या महत्वपूर्ण है?",
              "उत्पादों की तुलना करें", "AI तुलना"]
}

CURRENCIES = [
    "THB", "USD", "INR", "EUR", "CNY", "KRW",
    "GBP", "JPY", "SAR", "AED", "TRY", "VND"
]

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fff0f6, #f0eaff, #e9f8ff);
}
h1 {
    color: #a64d79 !important;
    text-align: center;
}
h2, h3 {
    color: #80558c !important;
}
.stButton button {
    background: #ed83b2;
    color: white;
    border-radius: 18px;
    border: none;
    font-weight: bold;
    width: 100%;
}
.stButton button:hover {
    background: #c66b9b;
    color: white;
}
div[data-testid="stFileUploader"] {
    background: #fff8fc;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🐱 My Cat's Choice 3.0")
st.markdown(
    "<h3 style='text-align:center'>🌸 Compare Smarter, Choose Better! 🌸</h3>",
    unsafe_allow_html=True
)

language = st.selectbox("🌍 Choose your language", list(LANGUAGES))
t = TEXT[language]

st.divider()

def product_section(label, key):
    st.subheader(label)

    photos = st.file_uploader(
        f"📸 {t[3]} — {label}",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key=f"upload_{key}"
    )

    camera_photos = st.camera_input(
        f"📷 {t[4]} — {label}",
        key=f"camera_{key}"
    )

    images = []

    for photo in photos or []:
        try:
            img = Image.open(photo).convert("RGB")
            images.append(img)
        except Exception:
            st.warning("⚠️ One photo could not be opened.")

    if camera_photos:
        images.append(Image.open(camera_photos).convert("RGB"))

    if images:
        st.caption(f"✅ {len(images)} photo(s) added")
        preview = st.columns(min(len(images), 4))
        for i, img in enumerate(images):
            with preview[i % len(preview)]:
                st.image(img, use_container_width=True)

    price = st.number_input(
        f"💰 {t[5]} — {label}",
        min_value=0.0,
        value=0.0,
        key=f"price_{key}"
    )

    currency = st.selectbox(
        f"💱 {t[6]} — {label}",
        CURRENCIES,
        index=CURRENCIES.index("THB"),
        key=f"currency_{key}"
    )

    quantity = st.number_input(
        f"📦 {t[7]} — {label}",
        min_value=0.01,
        value=1.0,
        key=f"quantity_{key}"
    )

    return images, price, currency, quantity


col_a, col_b = st.columns(2)

with col_a:
    images_a, price_a, currency_a, qty_a = product_section(t[1], "a")

with col_b:
    images_b, price_b, currency_b, qty_b = product_section(t[2], "b")

st.divider()

preferences = st.text_area(
    f"❤️ {t[8]}",
    placeholder="e.g. Best value, good quality, safe ingredients..."
)

st.caption("💡 Add photos of the front, back, ingredients and labels for better analysis.")

def exchange_rate(base, target):
    if base == target:
        return 1.0, datetime.now(timezone.utc).date().isoformat()

    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        response = requests.get(url, timeout=8)
        data = response.json()

        if data.get("result") == "success":
            rate = data["rates"].get(target)
            if rate:
                return rate, data.get("time_last_update_utc", "Date unavailable")
    except Exception:
        pass

    return None, None


if st.button(f"🐾 {t[9]}", use_container_width=True):

    if not images_a or not images_b:
        st.error("⚠️ Please add at least one photo for BOTH products.")

    else:
        api_key = st.secrets.get("GEMINI_API_KEY", "")

        if not api_key:
            st.error("🔑 Gemini API key is missing from Streamlit Secrets.")

        else:
            with st.spinner("🐱 Our AI cat is analysing your products..."):
                try:
                    client = genai.Client(api_key=api_key)

                    rate, rate_date = exchange_rate(
                        currency_b, currency_a
                    )

                    if rate is not None:
                        converted_b = price_b * rate
                        currency_info = (
                            f"Exchange rate: 1 {currency_b} = "
                            f"{rate:.6f} {currency_a}. "
                            f"Last provider update: {rate_date}. "
                            f"Product B converted price: "
                            f"{converted_b:.2f} {currency_a}."
                        )
                    else:
                        currency_info = (
                            "⚠️ Currency conversion unavailable. "
                            "Show original prices only."
                        )

                    prompt = f"""
You are My Cat's Choice 3.0, a careful product comparison assistant.

Write your entire answer in {LANGUAGES[language]}.

Compare Product A and Product B using ALL supplied photographs.

USER PREFERENCES:
{preferences}

PRODUCT A:
Price: {price_a} {currency_a}
Quantity: {qty_a}

PRODUCT B:
Price: {price_b} {currency_b}
Quantity: {qty_b}

CURRENCY INFORMATION:
{currency_info}

Provide these sections:

1. 🔎 Product identification.
2. 🌿 Ingredients, materials and features.
3. ✅ Benefits of each product.
4. ❌ Possible disadvantages.
5. ⚠️ Safety warnings and allergens.
6. ❤️ Match with user preferences.
7. 💰 Price and value for money.
8. 🏆 Final recommendation.

IMPORTANT RULES:
- Analyse all photographs together.
- Do not invent ingredients or certifications.
- Clearly state when information is not visible.
- Never compare different currencies as raw numbers.
- Use the supplied exchange rate only for currency conversion.
- Show the rate and its update date.
- Consider price per quantity where possible.
- Highlight safety concerns using 🚨.
- Use ⚠️ for important warnings.
- Use ✅ for positive findings.
- Use 🏆 for the best recommendation.
- If products have different purposes, explain that they are not direct substitutes.
- Never claim a product is completely safe based only on its packaging.
- Explain uncertainty clearly.
"""

                    contents = [prompt]

                    for img in images_a:
                        contents.append(img)

                    for img in images_b:
                        contents.append(img)

                    result = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=contents
                    )

                    st.success("🎉 Comparison completed!")

                    st.subheader(t[10])
                    st.markdown(result.text)

                    st.caption(
                        "🐱 AI-generated information may contain errors. "
                        "Please verify product labels and important claims."
                    )

                except Exception as e:
                    st.error(f"⚠️ Comparison error: {e}")

st.divider()
st.markdown(
    "<p style='text-align:center;color:#a64d79'>"
    "🐾 My Cat's Choice 3.0 | Made with love 🌸"
    "</p>",
    unsafe_allow_html=True
)
