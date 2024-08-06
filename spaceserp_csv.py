import streamlit as st
import pandas as pd
import requests
import time

# Authentication
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

def query_keyword(keyword):
    apiKey = st.secrets["SPACESERP_API_KEY"]
    params = {
        "apiKey": apiKey,
        "q": keyword,
        "location": "Houston,Texas,United States",
        "domain": "google.com",
        "gl": "us",
        "hl": "en",
        "resultFormat": "json",
        "resultBlocks": "organic_results",
        "pageSize":"100"
    }
    response = requests.get("https://api.spaceserp.com/google/search", params=params)
    data = response.json()

    if 'organic_results' in data:
        return data['organic_results']
    else:
        st.warning(f"Warning: 'organic_results' not found in API response for keyword '{keyword}'.")
        return []

def main():
    st.title("Keyword Search Results App")

    uploaded_file = st.file_uploader("Upload a .txt file with keywords", type="txt")

    if uploaded_file is not None:
        keywords = uploaded_file.getvalue().decode("utf-8").split("\n")
        keywords = [k.strip() for k in keywords if k.strip()]  # Remove empty lines
        
        st.write(f"**Number of keywords in the list: {len(keywords)}**")

        if st.button("Extract SERPs"):
            dfs = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, keyword in enumerate(keywords, 1):
                status_text.text(f"Keyword #{i}/{len(keywords)} being run")
                results = query_keyword(keyword)
                for result in results:
                    result['keyword'] = keyword
                    dfs.append(pd.DataFrame([result]))
                progress_bar.progress(i / len(keywords))
                time.sleep(0.1)  # To avoid hitting API rate limits

            df = pd.concat(dfs, ignore_index=True)
            df = df[['keyword', 'position', 'page', 'domain', 'link', 'title', 'description']]

            st.write("**Search Results:**")
            st.dataframe(df)

            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="search_results.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    if check_password():
        main()
