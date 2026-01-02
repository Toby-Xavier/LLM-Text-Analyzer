# LLM Text Analyzer

An automated text analysis tool powered by Google Gemini that analyzes text sentiment, generates summaries, and exports structured results to Excel or Google Sheets.

## Features

-  **Sentiment Analysis** - Analyze positive/negative/neutral sentiment with confidence scores
-  **Text Summarization** - Generate concise summaries of long texts
-  **Key Theme Extraction** - Identify main themes and talking points
-  **URL Support** - Fetch and analyze content from web pages
-  **Batch Processing** - Analyze multiple texts at once
-  **Excel Export** - Structured output in Excel format with formatted columns
-  **Google Sheets Export** - Cloud-based export with shareable links

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key (free tier available)
- (Optional) Google Cloud credentials for Google Sheets integration

## Installation

### 1. Clone or Download This Project

### 2. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Gemini API Key

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a `.env` file in the project root:
```
   GEMINI_API_KEY=your_api_key_here
```

### 5. (Optional) Set Up Google Sheets Integration

If you want to export directly to Google Sheets:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Sheets API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the JSON file
5. Rename the downloaded file to `credentials.json`
6. Place `credentials.json` in your project root directory
7. Run the tool - you'll be prompted to authorize on first use
8. The authorization is saved in `token.pickle` for future runs

## Usage

### Interactive Mode (Recommended)

Run the main script:
```bash
python run_analysis.py
```

Follow the interactive prompts to:
1. Choose input method (type text, provide URLs, or load from file)
2. Select analysis type (sentiment, summary, or themes)
3. Choose export format (Excel or Google Sheets)
4. Specify output filename (optional)

### Programmatic Usage

You can also import and use the functions directly in your own scripts:
```python
from analyzer import analyze_text, analyze_batch, export_to_excel, export_to_google_sheets

# Analyze single text
result = analyze_text("Your text here", analysis_type="sentiment")
print(result)

# Analyze multiple texts/URLs
results = analyze_batch([
    "Text 1",
    "Text 2",
    "https://example.com/article"
], analysis_type="summary")

# Export to Excel
export_to_excel(results, "my_results.xlsx")

# Export to Google Sheets
sheet_url = export_to_google_sheets(results, "My Analysis Results")
print(f"View your results: {sheet_url}")
```

## Input Methods

### 1. Direct Text Input
Type or paste text directly when prompted. Type `DONE` on a new line when finished.

Example:
```
> This product is amazing!
> DONE
```

### 2. URL Input
Provide URLs to web pages - the tool will fetch and analyze the content automatically.

Example:
```
> https://example.com/article
> https://blog.example.com/post
> DONE
```

### 3. Text File Input
Create a `.txt` file with one text or URL per line:

**sample_texts.txt:**
```
First text to analyze
Second text to analyze
https://example.com/article
The product quality is excellent and delivery was fast.
```

Then select option 3 and enter the filename: `sample_texts.txt`

## Analysis Types

### 1. Sentiment Analysis (Default)
- Determines positive/negative/neutral sentiment
- Provides confidence score (0.0 - 1.0)
- Extracts key sentiment indicators
- Generates brief summary

### 2. Summary
- Creates concise summaries of long texts
- Identifies main points
- Maintains context and key information

### 3. Themes
- Extracts main themes and topics
- Identifies recurring patterns
- Highlights key concepts

## Output Format

### Excel Output
Results are exported to `.xlsx` files with the following columns:
- **Timestamp** - When the analysis was performed
- **Input Source** - Original text or URL
- **Sentiment** - Positive/Negative/Neutral
- **Confidence Score** - 0.0 to 1.0
- **Summary** - Brief summary of the content
- **Key Points** - Main points separated by "|"
- **Analysis Type** - Type of analysis performed
- **Original Text** - Truncated preview of input

### Google Sheets Output
Same structure as Excel, but:
- Stored in your Google Drive
- Accessible via shareable link
- Formatted with colored headers
- Auto-resized columns
- Can be edited online

## Testing

### Test API Connection
```bash
python test_connection.py
```

This will:
- Verify your Gemini API key works
- List available models
- Send a test request
- Display the response

### Test Analysis
```bash
python analyzer.py
```

This runs a quick test with sample texts and exports to Excel.

## Troubleshooting

### API Key Issues

**Problem:** `GEMINI_API_KEY not found`
- **Solution:** Ensure your `.env` file is in the project root directory
- Verify `GEMINI_API_KEY` is spelled correctly (case-sensitive)
- Check that there are no extra spaces around the key

**Problem:** Invalid API key error
- **Solution:** Verify your API key at [Google AI Studio](https://aistudio.google.com/)
- Generate a new key if necessary

### Rate Limits

**Problem:** `429 Quota exceeded` error
- **Solution:** You've hit the free tier rate limit
- Wait a few minutes before trying again
- The tool uses `gemini-2.5-flash-lite` which has higher limits
- Consider spacing out requests for large batches
- Check limits at: https://ai.google.dev/gemini-api/docs/rate-limits

### URL Fetching Issues

**Problem:** Cannot fetch content from URL
- **Solution:** Some websites block automated access
- Try different URLs if one fails
- The tool will skip failed URLs and continue with others
- Check if the website requires authentication

### Google Sheets Authentication

**Problem:** `credentials.json not found`
- **Solution:** Follow the Google Sheets setup instructions above
- Ensure the file is named exactly `credentials.json`
- Place it in the project root directory

**Problem:** Authorization window doesn't open
- **Solution:** Check your firewall settings
- Try running with `--no-browser` flag if needed
- Manually copy the authorization URL from terminal

**Problem:** Permission errors when creating sheets
- **Solution:** Make sure Google Sheets API is enabled in Google Cloud Console
- Verify your OAuth credentials are for "Desktop app"
- Delete `token.pickle` and re-authenticate

### Input Validation Warnings

**Problem:** "Text too short" warning
- **Solution:** Minimum 10 characters required for meaningful analysis
- Combine short texts or add more context

**Problem:** "Text truncated" warning
- **Solution:** Texts over 50,000 characters are automatically truncated
- For very long documents, consider splitting into sections

## Limitations

- **API Rate Limits:** Free tier has limits on requests per minute/day
- **Text Length:** URL content limited to 5,000 characters for analysis to stay within token limits
- **Website Access:** Some websites may block automated content fetching
- **Language:** Works best with English text (Gemini supports other languages but accuracy may vary)
- **Internet Required:** Both Gemini API and Google Sheets require internet connection

## Cost Information

### Gemini API (Google)
- **Free Tier:** 15 requests per minute, 1,500 requests per day
- **Sufficient for:** Most learning and portfolio projects
- **Upgrade:** Pay-as-you-go pricing available if needed

### Google Sheets API
- **Free:** No additional cost beyond Google account
- **Storage:** Counts against your Google Drive quota