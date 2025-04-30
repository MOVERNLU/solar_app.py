import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from collections import defaultdict
import time
import pandas as pd

st.set_page_config(page_title="Mover rutetæller", layout="centered")

st.title("📦 Mover Admin – dagligt rutetjek")

# 📅 Dato
valgt_dato = st.date_input("Vælg dato", datetime.today())
dato_str = valgt_dato.strftime("%d-%m-%Y")

# Adresser og køretøjer
adresser = ["Vingelodden 10", "Oliefabriksvej 49"]
køretøjer = ["Cykel", "Bil", "Varevogn", "Liftvogn"]
resultat = {adr: defaultdict(int) for adr in adresser}

# 🔘 Knap
if st.button("Hent data"):
    st.info("Åbner Mover Admin – log ind i browseren")
    
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    driver.get("https://admin.mover.dk/")
    time.sleep(15)  # tid til login manuelt

    for side in range(1, 4):
        url = (
            "https://admin.mover.dk/dk/da/user-area/users/6016/trips/"
            if side == 1
            else f"https://admin.mover.dk/dk/da/user-area/users/6016/trips/{side}"
        )

        driver.get(url)
        time.sleep(2)
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        if not rows:
            break

        for row in rows:
            try:
                kolonner = row.find_elements(By.TAG_NAME, "td")
                dato_tekst = kolonner[1].text.strip()
                afhentning = kolonner[6].text.strip()
                køretøj = kolonner[9].text.strip()

                if dato_tekst != dato_str:
                    continue

                if afhentning in adresser and køretøj in køretøjer:
                    resultat[afhentning][køretøj] += 1
            except:
                continue

    driver.quit()
    st.success("✅ Data hentet!")

    # Formatér som DataFrame
    data = []
    for adr in adresser:
        for kør in køretøjer:
            data.append({
                "Adresse": adr,
                "Køretøj": kør,
                "Antal ture": resultat[adr][kør]
            })
    df = pd.DataFrame(data)

    st.dataframe(df)

    # 📥 Download som Excel
    def to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Ture")
        return output.getvalue()

    excel_data = to_excel(df)
    st.download_button(
        label="📥 Download som Excel",
        data=excel_data,
        file_name=f"ture_{dato_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
