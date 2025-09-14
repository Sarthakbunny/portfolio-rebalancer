import pandas as pd

def format_groww_stock_portfolio(filename: str):
    """
    Format the data file from Groww which contains the stock portfolio data.
    It can handle both CSV and Excel files.
    It skips 10 rows as the first 10 rows have non-related data with a different format.
    
    args: filename(str)
    Args:
        filename (str): Path to the CSV or Excel file.
    """
    
    if filename.endswith(".csv"):
        df = pd.read_csv(filename, skiprows=10)
    elif filename.endswith((".xls", ".xlsx")):
        df = pd.read_excel(filename, skiprows=10)
    else:
        raise ValueError("Unsupported file format. Only CSV and Excel files are supported.")

    return df
    