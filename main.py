import pandas as pd
import google.generativeai as gemini
import json
import os
from dotenv import load_dotenv
import re

prompt_template = """
You are a Chief Financial Planner. Your expertise lies in creating and managing investment portfolios to achieve specific financial goals.

**User Profile & Context:**
- **Primary Goal:** {goal}
- **Investment Horizon:** {invest_time} years or more.
- **Risk Tolerance:** {risk_tolerance}.

- **Current Portfolio:**
{portfolio_data}

**Task:**
Analyze the user's current portfolio and financial goal. Provide two separate sets of recommendations.

1.  **Portfolio Modification Recommendations:**
    -   Suggest changes to the existing portfolio holdings.
    -   The output must be a JSON array of objects.
    -   Each object should have the following keys:
        -   `stock_name`: (string)
        -   `stock_symbol`: (string)
        -   `action`: (string - "Buy", "Sell", or "Hold")
        -   `units`: (integer - The number of units to buy/sell/hold. Use 'null' if not applicable)
        -   `reason`: (string - A concise explanation for the recommendation)

2.  **New Diversification Recommendations:**
    -   Suggest new stocks or ETFs to buy that are not currently in the portfolio.
    -   These should be chosen to improve diversification and align with the user's goal and risk tolerance.
    -   The output must be a JSON array of objects.
    -   Each object should have the following keys:
        -   `stock_name`: (string)
        -   `stock_symbol`: (string)
        -   `action`: (string - "Buy")
        -   `units`: (integer - The number of units to buy)
        -   `reason`: (string - A concise explanation for the recommendation)

**Output Format:**
-   **Strictly** output a single JSON object.
-   The object must contain two keys:
    -   `current_portfolio_modifications`: A JSON array corresponding to Task 1.
    -   `outside_portfolio_buyables`: A JSON array corresponding to Task 2.
-   Example JSON structure:
```json
{{
  "current_portfolio_modifications": [
    {{
      "stock_name": "Microsoft",
      "stock_symbol": "MSFT",
      "action": "Hold",
      "units": 100,
      "reason": "Strong long-term outlook and stable growth."
    }}
  ],
  "outside_portfolio_buyables": [
    {{
      "stock_name": "Vanguard S&P 500 ETF",
      "stock_symbol": "VOO",
      "action": "Buy",
      "units": 50,
      "reason": "Provides broad market exposure for diversification."
    }}
  ]
}}
"""

load_dotenv()
################################
## CSV format
################################

def parse_csv(filename: str):
    """
    This function parses a CSV file and collects all the information
    """
    df = pd.read_csv(filename)
    return df

###############################
## Generate Prompt
###############################
def generate_prompt(portfolio_df, goal: str, invest_time: str, risk_appetite: str):
    """
    Generates a complete prompt for a financial planning AI.

    Args:
        goal (str): The user's primary financial goal.
        invest_time (int): The investment horizon in years.
        risk_tolerance (str): The user's risk tolerance (e.g., "Moderate").
        portfolio_data (str): A string representation of the current portfolio.

    Returns:
        str: The fully formatted prompt.
    """

    #convert data from the table to json format
    portfolio_data = portfolio_df.to_dict(orient = "records")
    
    prompt = prompt_template.format(
        goal=goal,
        invest_time=invest_time,
        risk_tolerance=risk_appetite,
        portfolio_data=portfolio_data
    )
    return prompt

###############################
## Portfolio Analysis(Brain)
###############################
def rebalance_portfolio(prompt: str):
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY. Please set it in .env file.")
    
    #Configure Gemini
    gemini.configure(api_key=api_key)
    
    model = gemini.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)
    raw_text = response.text

    # Use regex to find and extract the valid JSON object
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    
    if not json_match:
        raise ValueError("Could not find a valid JSON object in the response.")

    json_string = json_match.group(0)

    try:
        # Now, try to load the extracted JSON string
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        # Fallback for minor errors like trailing commas
        try:
            # Simple cleanup: remove any trailing comma before the last brace
            cleaned_json_string = re.sub(r',\s*\}', '}', json_string)
            data = json.loads(cleaned_json_string)
        except json.JSONDecodeError:
            raise ValueError(f"Gemini did not return valid JSON. Error: {e}\nResponse was:\n{raw_text}")

    return data["current_portfolio_modifications"], data["outside_portfolio_buyables"]



################################
## Merge Results
################################
def merge_results(portfolio_mods, outside_portfolio_buyables, output_path: str):
    df_mods = pd.DataFrame(portfolio_mods)
    df_outside = pd.DataFrame(outside_portfolio_buyables)
    
    df_mods["Section"] = "Current Portfolio"
    df_outside["Section"] = "Outside Portfolio"
    
    final_df = pd.concat([df_mods, df_outside], ignore_index=True)
    final_df.to_csv(output_path, index=False)
    return final_df

##############################
## Main
#############################
if __name__ == "__main__":
    portfolio = parse_csv("sample_portfolio.csv")
    
    prompt = generate_prompt(portfolio_df=portfolio, goal="Create wealth", invest_time="5", risk_appetite="HIGH")
    
    mods, outside_portfolio = rebalance_portfolio(prompt=prompt)
    
    output_path = "recommended_modifications.csv"
    final_csv = merge_results(portfolio_mods=mods, outside_portfolio_buyables=outside_portfolio, output_path=output_path)
    
    print(final_csv.head())