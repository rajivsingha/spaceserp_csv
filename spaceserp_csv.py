import streamlit as st
import pandas as pd
import requests
import base64

# Authentication
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    st.title("Keyword Query App")

    uploaded_file = st.file_uploader("Choose a .TXT file with keywords", type="txt")

    if uploaded_file is not None:
        keywords = uploaded_file.read().decode('utf-8').split('\n')
        keywords = [keyword.strip() for keyword in keywords if keyword.strip()]

        st.write(f"Number of keywords: {len(keywords)}")

        @st.cache_data
        def query_keyword(keyword):
            apiKey = st.secrets["api_key"]
            params = {
                "apiKey": apiKey,
                "q": keyword,
                "location": "Houston,Texas,United States",
                "domain": "google.com",
                "gl": "us",
                "hl": "en",
                "resultFormat": "json",
                "resultBlocks": "organic_results",
                "pageSize": "100"
            }
            response = requests.get("https://api.spaceserp.com/google/search", params=params)
            data = response.json()

            if 'organic_results' in data:
                return data['organic_results']
            else:
                st.warning(f"'organic_results' not found in API response for keyword '{keyword}'.")
                return []

        df = pd.DataFrame()
        dfs = []
        progress_placeholder = st.empty()

        for idx, keyword in enumerate(keywords):
            progress_placeholder.text(f"Keyword #{idx + 1}/{len(keywords)} being run")
            results = query_keyword(keyword)
            for result in results:
                result['keyword'] = keyword
                dfs.append(pd.DataFrame([result]))

        if dfs:
            df = pd.concat(dfs, ignore_index=True)

            if not df.empty:
                df = df[['keyword', 'position', 'page', 'domain', 'link', 'title', 'description']]
                st.dataframe(df)

                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="houston_Cogential_Important_TPs_search_results.csv">Download CSV file</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.write("No results found for the given keywords.")
        else:
            st.write("No valid keywords found in the file.")
