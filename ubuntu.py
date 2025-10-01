import requests
import os
import hashlib
from urllib.parse import urlparse
import mimetypes

def get_filename_from_url(url, content_type):
    """Extract filename from URL or generate one based on content type"""
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    
    # If no filename in URL, generate one with appropriate extension
    if not filename:
        extension = mimetypes.guess_extension(content_type) or '.bin'
        filename = f"downloaded_image{extension}"
    
    return filename

def is_duplicate_image(content, directory="Fetched_Images"):
    """Check if image content already exists in directory"""
    # Create hash of image content
    content_hash = hashlib.md5(content).hexdigest()
    
    # Check all files in directory for matching hash
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash == content_hash:
                    return True, filename
    
    return False, content_hash

def is_safe_to_download(response):
    """Check if it's safe to download the response content"""
    # Check content type
    content_type = response.headers.get('content-type', '').lower()
    if not content_type.startswith('image/'):
        return False, f"Unsupported content type: {content_type}"
    
    # Check content length (limit to 10MB)
    content_length = response.headers.get('content-length')
    if content_length and int(content_length) > 10 * 1024 * 1024:
        return False, "File too large (max 10MB)"
    
    # Check disposition for suspicious filenames
    content_disposition = response.headers.get('content-disposition', '')
    if '..' in content_disposition or content_disposition.startswith('/'):
        return False, "Suspicious content disposition"
    
    return True, "OK"

def download_image(url, directory="Fetched_Images"):
    """Download an image from a URL with safety checks"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Fetch the image with headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # First, make a HEAD request to check headers
        head_response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        head_response.raise_for_status()
        
        # Check if safe to download based on headers
        safe, reason = is_safe_to_download(head_response)
        if not safe:
            return False, f"Safety check failed: {reason}"
        
        # Now make the actual GET request
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # Double-check safety with the full response
        safe, reason = is_safe_to_download(response)
        if not safe:
            return False, f"Safety check failed after download: {reason}"
        
        # Read content
        content = response.content
        
        # Check for duplicates
        is_duplicate, duplicate_info = is_duplicate_image(content, directory)
        if is_duplicate:
            return False, f"Duplicate of existing image: {duplicate_info}"
        
        # Extract filename
        filename = get_filename_from_url(url, response.headers.get('content-type'))
        filepath = os.path.join(directory, filename)
        
        # Ensure filename is safe
        if '..' in filename or filename.startswith('/'):
            filename = f"safe_name_{duplicate_info}.jpg"
            filepath = os.path.join(directory, filename)
        
        # Save the image
        with open(filepath, 'wb') as f:
            f.write(content)
            
        return True, f"Successfully fetched: {filename}"
        
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {e}"
    except Exception as e:
        return False, f"An error occurred: {e}"

def main():
    print("Welcome to the Ubuntu Image Fetcher")
    print("A tool for mindfully collecting images from the web\n")
    
    # Get multiple URLs from user
    urls_input = input("Please enter image URLs (separated by commas): ")
    urls = [url.strip() for url in urls_input.split(',') if url.strip()]
    
    if not urls:
        print("No valid URLs provided.")
        return
    
    print(f"\nAttempting to fetch {len(urls)} images...\n")
    
    success_count = 0
    for i, url in enumerate(urls, 1):
        print(f"Processing URL {i}/{len(urls)}: {url}")
        success, message = download_image(url)
        
        if success:
            print(f"✓ {message}")
            success_count += 1
        else:
            print(f"✗ {message}")
        
        print()  # Empty line for readability
    
    print(f"Downloaded {success_count} of {len(urls)} images successfully.")
    print("\nConnection strengthened. Community enriched.")

if __name__ == "__main__":
    main()