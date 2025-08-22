import requests
import sys

def get_random_quote():
    """Fetches a random quote from the Quotable API."""
    api_url = "https://api.quotable.io/random"
    try:
        response = requests.get(api_url, timeout=10) # 10 second timeout
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        
        quote_content = data.get('content')
        quote_author = data.get('author')
        
        if quote_content and quote_author:
            # Formats the quote with double quotes around the content
            return f'"{quote_content}" - {quote_author}'
        else:
            return "Error: Could not parse quote content or author from the API response."
            
    except requests.exceptions.Timeout:
        return "Error: The request timed out. Please check your internet connection."
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the API. Please check your internet connection."
    except requests.exceptions.RequestException as e:
        return f"An unexpected error occurred: {e}"
    except ValueError:
        return "Error: Could not decode JSON response from the API."

def main():
    """Main function to run the random quote generator."""
    print("Fetching a random quote...")
    quote = get_random_quote()
    print("\n" + quote)
    print("\n-----")
    print("For more quotes, run 'python main.py' again.")

if __name__ == "__main__":
    main()
