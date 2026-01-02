import os
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import json
import re
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

# Google Sheets scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def clean_json_response(text):
    """
    Extract and clean JSON from the response.
    Sometimes LLMs add markdown formatting or extra text.
    """
    # Remove markdown code blocks if present
    text = re.sub(r'```json\n?', '', text)
    text = re.sub(r'```\n?', '', text)
    
    # Try to find JSON object in the text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group()
    
    return text.strip()

def validate_inputs(inputs):
    """
    Validate and clean input data.
    
    Args:
        inputs: List of texts or URLs
    
    Returns:
        Tuple of (valid_inputs, warnings)
    """
    valid_inputs = []
    warnings = []
    
    for i, text in enumerate(inputs, 1):
        # Skip empty inputs
        if not text or not text.strip():
            warnings.append(f"Item {i}: Empty input skipped")
            continue
        
        # Check if it's a URL
        if text.startswith('http://') or text.startswith('https://'):
            valid_inputs.append(text)
        # Check text length
        elif len(text) < 10:
            warnings.append(f"Item {i}: Text too short (min 10 characters)")
        elif len(text) > 50000:
            warnings.append(f"Item {i}: Text truncated (max 50000 characters)")
            valid_inputs.append(text[:50000])
        else:
            valid_inputs.append(text)
    
    return valid_inputs, warnings

def analyze_text(text, analysis_type="sentiment"):
    """
    Analyze text using Gemini and return structured results.
    
    Args:
        text: The text to analyze
        analysis_type: Type of analysis (sentiment, summary, keywords, etc.)
    
    Returns:
        Dictionary with analysis results
    """
    
    # Create a prompt that asks for structured output
    prompt = f"""
    Analyze the following text and provide a {analysis_type} analysis.
    
    Return your response in this exact JSON format:
    {{
        "analysis_type": "{analysis_type}",
        "sentiment": "positive/negative/neutral",
        "confidence_score": 0.85,
        "key_points": ["point1", "point2", "point3"],
        "summary": "brief summary here"
    }}
    
    Text to analyze:
    {text}
    
    IMPORTANT: Return ONLY valid JSON, no other text or markdown formatting.
    """
    
    try:
        print(f"🔍 Analyzing text...")
        response = model.generate_content(prompt)
        
        # Clean and parse the JSON response
        cleaned_response = clean_json_response(response.text)
        result = json.loads(cleaned_response)
        
        # Add metadata
        result['original_text'] = text[:100] + "..." if len(text) > 100 else text
        result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("✅ Analysis complete!")
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

def fetch_url_content(url):
    """
    Fetch and extract main text content from a URL.
    
    Args:
        url: The URL to fetch
    
    Returns:
        Extracted text content or None if failed
    """
    try:
        print(f"🌐 Fetching content from: {url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        print(f"✅ Fetched {len(text)} characters")
        return text
        
    except Exception as e:
        print(f"❌ Error fetching URL: {e}")
        return None

def analyze_batch(inputs, analysis_type="sentiment"):
    """
    Analyze multiple texts or URLs in batch.
    
    Args:
        inputs: List of texts or URLs to analyze
        analysis_type: Type of analysis to perform
    
    Returns:
        List of analysis results
    """
    # Validate inputs first
    valid_inputs, warnings = validate_inputs(inputs)
    
    if warnings:
        print("\n⚠️  Input Warnings:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    
    if not valid_inputs:
        print("❌ No valid inputs to process")
        return []
    
    results = []
    
    for i, input_text in enumerate(valid_inputs, 1):
        print(f"\n{'='*50}")
        print(f"Processing item {i}/{len(valid_inputs)}")
        print(f"{'='*50}")
        
        # Check if input is a URL
        if input_text.startswith('http://') or input_text.startswith('https://'):
            content = fetch_url_content(input_text)
            if not content:
                print("⚠️  Skipping this URL due to fetch error")
                continue
            # Limit content length for analysis (Gemini has token limits)
            content = content[:5000]
        else:
            content = input_text
        
        # Analyze the content
        result = analyze_text(content, analysis_type)
        
        if result:
            result['input_source'] = input_text
            results.append(result)
    
    return results

def export_to_excel(results, filename=None):
    """
    Export analysis results to an Excel file.
    
    Args:
        results: List of analysis result dictionaries
        filename: Output filename (optional, auto-generates if not provided)
    
    Returns:
        The filename that was created
    """
    if not results:
        print("❌ No results to export")
        return None
    
    # Auto-generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_results_{timestamp}.xlsx"
    
    # Ensure .xlsx extension
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
    
    try:
        print(f"\n📝 Exporting results to Excel...")
        
        # Convert results to DataFrame
        # Flatten the key_points list into a string for Excel
        for result in results:
            if 'key_points' in result and isinstance(result['key_points'], list):
                result['key_points'] = ' | '.join(result['key_points'])
        
        df = pd.DataFrame(results)
        
        # Reorder columns for better readability
        desired_order = [
            'timestamp',
            'input_source', 
            'sentiment',
            'confidence_score',
            'summary',
            'key_points',
            'analysis_type',
            'original_text'
        ]
        
        # Only include columns that exist
        columns = [col for col in desired_order if col in df.columns]
        df = df[columns]
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Analysis Results', index=False)
            
            # Get the worksheet
            worksheet = writer.sheets['Analysis Results']
            
            # Adjust column widths
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                # Cap at 50 characters for readability
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[chr(64 + idx)].width = adjusted_width
        
        print(f"Results exported to: {filename}")
        print(f"Total rows: {len(df)}")
        return filename
        
    except Exception as e:
        print(f"❌ Error exporting to Excel: {e}")
        return None

def authenticate_google_sheets():
    """
    Authenticate with Google Sheets API.
    
    Returns:
        Authenticated gspread client or None if failed
    """
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("❌ Error: credentials.json not found")
                print("Please follow the setup instructions in README.md")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    try:
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def export_to_google_sheets(results, sheet_name=None):
    """
    Export analysis results to Google Sheets.
    
    Args:
        results: List of analysis result dictionaries
        sheet_name: Name for the Google Sheet (optional)
    
    Returns:
        The URL of the created sheet or None if failed
    """
    if not results:
        print("❌ No results to export")
        return None
    
    # Auto-generate sheet name if not provided
    if not sheet_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sheet_name = f"Analysis Results {timestamp}"
    
    try:
        print(f"\n📝 Authenticating with Google...")
        client = authenticate_google_sheets()
        
        if not client:
            return None
        
        print(f"📝 Creating Google Sheet: {sheet_name}")
        
        # Create a new spreadsheet
        spreadsheet = client.create(sheet_name)
        worksheet = spreadsheet.sheet1
        
        # Prepare data for Google Sheets
        # Flatten key_points list into string
        for result in results:
            if 'key_points' in result and isinstance(result['key_points'], list):
                result['key_points'] = ' | '.join(result['key_points'])
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Reorder columns
        desired_order = [
            'timestamp',
            'input_source', 
            'sentiment',
            'confidence_score',
            'summary',
            'key_points',
            'analysis_type',
            'original_text'
        ]
        
        columns = [col for col in desired_order if col in df.columns]
        df = df[columns]
        
        # Prepare data for sheets (headers + rows)
        headers = df.columns.tolist()
        data = df.values.tolist()
        
        # Write headers
        worksheet.update('A1', [headers])
        
        # Write data
        if data:
            worksheet.update(f'A2', data)
        
        # Format the sheet
        worksheet.format('A1:Z1', {
            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.8},
            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}
        })
        
        # Auto-resize columns
        worksheet.columns_auto_resize(0, len(headers))
        
        # Share the sheet (make it accessible via link)
        spreadsheet.share('', perm_type='anyone', role='reader')
        
        sheet_url = spreadsheet.url
        
        print(f"✅ Results exported to Google Sheets!")
        print(f"📊 Total rows: {len(df)}")
        print(f"🔗 Sheet URL: {sheet_url}")
        
        return sheet_url
        
    except Exception as e:
        print(f"❌ Error exporting to Google Sheets: {e}")
        return None

# Test the function
if __name__ == "__main__":
    # Test with multiple inputs
    test_inputs = [
        "I absolutely love this product! It exceeded all my expectations and the customer service was amazing.",
        "This was the worst experience ever. The product broke after one day and nobody responded to my complaints.",
        "The product is okay. Nothing special but it works as expected. Price is reasonable."
    ]
    
    print("🚀 Starting batch analysis...\n")
    results = analyze_batch(test_inputs)
    
    print("\n" + "="*50)
    print(f"📊 BATCH ANALYSIS COMPLETE - {len(results)} items processed")
    print("="*50)
    
    # Export to Excel
    if results:
        excel_file = export_to_excel(results)
        if excel_file:
            print(f"\n🎉 SUCCESS! Open the file to see your results:")
            print(f"   {excel_file}")