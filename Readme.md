# Website & Brand Visibility Auditor

This Streamlit application performs a comprehensive audit of a website's online presence, including SEO, social media visibility, brand sentiment, and competitor analysis.

## 🚀 Features

-   **SEO Audit:** Checks on-page and technical SEO factors.
-   **Social Media Scan:** Identifies linked social media profiles and their activity levels.
-   **Brand Sentiment Analysis:** Gauges public opinion from online mentions.
-   **Competitor Analysis:** Identifies key competitors and compares their online presence.

## ⚙️ Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/brand-audit-app.git](https://github.com/your-username/brand-audit-app.git)
    cd brand-audit-app
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ How to Run the App

Once you've installed the dependencies, you can run the Streamlit app with the following command:

```bash
streamlit run app.py

Your web browser should open with the application running.

🔧 Configuration
You can customize the app's theme and other settings in the .streamlit/config.toml file.


---

### `requirements.txt`

This file lists all the Python libraries your project needs to run. This allows anyone to install the exact same dependencies easily.

```text
streamlit
pandas

(You would add other libraries here as you build out the real audit logic, such as requests, beautifulsoup4, google-generativeai, etc.)

.streamlit/config.toml
This file is for configuring your Streamlit app's appearance and behavior. For example, you can set a custom theme.

[theme]
primaryColor="#FF4B4B"
backgroundColor="#0E1117"
secondaryBackgroundColor="#262730"
textColor="#FAFAFA"
font="sans serif"

.gitignore
This file tells Git which files or folders to ignore. This is useful for keeping your repository clean by excluding virtual environments, cache files, and other non-essential items.

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
venv/
.venv/
env/
.env

# Streamlit secrets
.streamlit/secrets.toml