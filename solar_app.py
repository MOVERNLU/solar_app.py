import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from collections import defaultdict
import pandas as pd

# Streamlit UI
st.set_page_config(page_title="Tæl ture via Mover Admin", layout="centered")
st.title("📦 Mover rutetæller (manuelt via browser)")
st.markdown("Denne app tæller antal ture pr. køretøj og adresse direkte fra Mover Admin.")

# Inputfelter
dato = st.date_input("Vælg dato")
kunde_id = st.text_input("Indtast kunde ID (fx 6016)", value="6016")

# Generer link baseret på input
valgt_dato_str = dato.strftime("%Y-%m-%d")
base_url = f"https://admin.mover.dk/dk/da/user-area/users/{kunde_id}/trips/"

st.markdown(f"🔗 [Åbn Mover Admin for {valgt_dato_str}]( {base_url} )")

# Startknap
if st.button("🚀 Start rutetælling (side 1-3)"):
    try:
        with st.spinner("Starter browser og henter data..."):

            # Chrome setup
            options = Options()
            options.add_experimental_option("detach", True)
            service = Service("chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=options)

            # Gå til første side
            driver.get(base_url)
            st.info("🔐 Log ind i browseren hvis nødvendigt. Venter 20 sekunder...")
            time.sleep(20)

            all_data = []

            for page in range(1, 4):
                st.write(f"⏳ Henter data fra side {page}...")
                if page > 1:
                    driver.get(base_url + str(page))
                    time.sleep(2)

                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) < 10:
                        continue

                    row_date = cols[1].text.strip()
                    pickup_address = cols[5].text.strip()
                    vehicle = cols[8].text.strip()

                    if row_date == valgt_dato_str:
                        all_data.append((pickup_address, vehicle))

            driver.quit()

            # Tæl
            counts = defaultdict(lambda: defaultdict(int))
            for address, vehicle in all_data:
                if address in ["Vingelodden 10", "Oliefabriksvej 49"]:
                    counts[address][vehicle] += 1

            result_rows = []
            for address, vehicles in counts.items():
                for vehicle_type, count in vehicles.items():
                    result_rows.append({
                        "Pickup address": address,
                        "Vehicle": vehicle_type,
                        "Antal ture": count
                    })

            if result_rows:
                df = pd.DataFrame(result_rows)
                st.success("✅ Rutetælling færdig!")
                st.dataframe(df)

                st.download_button(
                    label="📥 Download som Excel",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="manual_rutetælling.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Ingen ture fundet på den valgte dato for de nævnte adresser.")

    except Exception as e:
        st.error(f"🚨 Fejl: {e}")
