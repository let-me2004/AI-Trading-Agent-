import google.generativeai as genai
from config import GOOGLE_API_KEY
import json
import logging

logger = logging.getLogger(__name__)
# --- CHANGE 1: Configure the Gemini API with the correct key ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Fatal Error: Could not configure Google AI. Check your API key. Error: {e}")
    exit()

# --- CHANGE 2: Use a current model and set the generation config for JSON output ---
generation_config = {
  "response_mime_type": "application/json",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config
)

# In llm_handler.py, replace this function

# In llm_handler.py, replace this function

def get_market_analysis(technical_data, news_headlines):
    """
    Takes market data, gets analysis from a specialized LLM persona, and sanitizes the output.
    """
    # This is our new, advanced prompt with persona, rules, and examples.
    prompt = f"""
    **Persona:**
    You are 'Cognito', a senior quantitative sentiment analyst for the Indian stock market. Your sole purpose is to analyze real-time data to provide a decisive, short-term (1-4 hour) directional bias for the NIFTY 50 index. You are data-driven, precise, and avoid ambiguity. You understand that in intraday trading, "Neutral" is often a missed opportunity, so you only use it when data is perfectly contradictory.

    **Rules of Analysis:**
    1.  **Negative Bias:** Market panic is faster than market greed. Give slightly more weight to negative news (inflation, geopolitical tension, bad corporate results) than positive news.
    2.  **High-Impact Keywords:** Any mention of "RBI," "inflation surprise," "policy change," or "geopolitical conflict" significantly increases the confidence of your analysis.
    3.  **Technicals as Context:** Use the provided technical data as context. A strong bullish technical reading can temper a bearish news outlook, and vice-versa.
    4.  **Output Format:** You MUST return your analysis ONLY as a single, clean JSON object. Do not include any other text, greetings, or explanations.

    **Examples of Correct Analysis:**

    * **Example 1:**
        * **Input Data:** "Techs: NIFTY at 24500. RSI is 45. EMA(10) is below EMA(20). | News: RBI announces unexpected interest rate hike to combat rising inflation."
        * **Correct Output:**
            ```json
            {{
              "outlook": "Strongly Bearish",
              "confidence": 0.9,
              "reasoning": "Unexpected RBI rate hike is a major negative catalyst, confirmed by weak technicals.",
              "suggested_action": "Favor Put options"
            }}
            ```

    * **Example 2:**
        * **Input Data:** "Techs: NIFTY at 24800. RSI is 65. Price is above all key moving averages. | News: Government announces major infrastructure spending package. Global markets are positive."
        * **Correct Output:**
            ```json
            {{
              "outlook": "Bullish",
              "confidence": 0.75,
              "reasoning": "Positive fiscal stimulus and strong technicals suggest continued upward momentum.",
              "suggested_action": "Favor Call options"
            }}
            ```

    ---
    **Live Data for Analysis:**

    Now, using the persona, rules, and examples above, analyze the following live data:

    * **Technical Snapshot:** "{technical_data}"
    * **Key News Headlines:** "{news_headlines}"

    Provide your output now.
    """

    try:
        response = model.generate_content(prompt)
        analysis_dict = json.loads(response.text)

        # Data Sanitization Protocol (from our previous fix)
        if 'confidence' in analysis_dict:
            try:
                analysis_dict['confidence'] = float(analysis_dict['confidence'])
            except (ValueError, TypeError):
                logger.warning(f"LLM returned invalid confidence value. Defaulting to 0.0. Value: {analysis_dict['confidence']}")
                analysis_dict['confidence'] = 0.0
        else:
            logger.warning("LLM response was missing 'confidence' key. Defaulting to 0.0.")
            analysis_dict['confidence'] = 0.0

        return analysis_dict

    except Exception as e:
        logger.error(f"Error getting or parsing analysis from LLM: {e}", exc_info=True)
        return None
# --- This is how we test our module ---
if __name__ == '__main__':
    print("Testing LLM Handler...")
    # Create sample data
    sample_tech_data = "NIFTY at 23500. RSI is 65. Approaching resistance at 23600."
    sample_news = "Global markets are down 1%. Major IT firm announces weak quarterly forecast."

    # Get the analysis
    analysis = get_market_analysis(sample_tech_data, sample_news)

    if analysis:
        print("Successfully received analysis from LLM:")
        # Pretty-print the JSON
        print(json.dumps(analysis, indent=2))
    else:
        print("Failed to get analysis.")