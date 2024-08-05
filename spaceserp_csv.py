import streamlit as st
import pandas as pd
import requests
import base64

# Authentication
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secret["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    st.title("Keyword Query App")

    # File upload
    uploaded_file = st.file_uploader("Choose a .TXT file with keywords", type="txt")

    if uploaded_file is not None:
        keywords = uploaded_file.read().decode('utf-8').split('\n')
        keywords = [keyword.strip() for keyword in keywords if keyword.strip()]  # Remove empty lines and spaces

        st.write(f"Number of keywords: {len(keywords)}")

        @st.cache_data
        def query_keyword(keyword):
            apiKey = st.secret["api_key"]
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

            # Check if 'organic_results' key exists in the response
            if 'organic_results' in data:
                return data['organic_results']
            else:
                st.warning(f"'organic_results' not found in API response for keyword '{keyword}'.")
                return []  # Return an empty list if 'organic_results' is not found

        # Create an empty DataFrame
        df = pd.DataFrame()

        # Initialize a list to collect DataFrames
        dfs = []

        # Create a placeholder for the progress message
        progress_placeholder = st.empty()

        # Loop through keywords, query API, and append results to the list
        for idx, keyword in enumerate(keywords):
            # Update the progress message in the placeholder
            progress_placeholder.text(f"Keyword #{idx + 1}/{len(keywords)} being run")
            results = query_keyword(keyword)
            for result in results:
                result['keyword'] = keyword  # Add the keyword to the result
                # Append the result (as a DataFrame) to the list
                dfs.append(pd.DataFrame([result]))

        # Concatenate all DataFrames in the list into one DataFrame
        if dfs:
            df = pd.concat(dfs, ignore_index=True)

            # Select and rename columns as needed
            if not df.empty:
                df = df[['keyword', 'position', 'page', 'domain', 'link', 'title', 'description']]

                # Display the entire DataFrame
                st.dataframe(df)

                # Download the DataFrame as a CSV file
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
                href = f'<a href="data:file/csv;base64,{b64}" download="houston_Cogential_Important_TPs_search_results.csv">Download CSV file</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.write("No results found for the given keywords.")
        else:
            st.write("No valid keywords found in the file.")
