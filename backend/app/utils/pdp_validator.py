import re

def validate_and_clean_pdp_url(url: str, platform: str = "") -> dict:
    """
    Validates if a URL is a direct Product Detail Page (PDP)
    and strips search queries or malformed paths.
    """
    if not url or not isinstance(url, str):
        return {"is_pdp": False, "url": ""}
        
    zepto_pdp_pattern = r"^https?:\/\/(www\.)?zepto\.com\/pn\/[a-zA-Z0-9\-]+\/pvid\/[a-zA-Z0-9\-]+"
    blinkit_pdp_pattern = r"^https?:\/\/(www\.)?blinkit\.com\/prn\/[a-zA-Z0-9\-]+\/prid\/[0-9]+"

    if "zepto.com" in url:
        match = re.search(r"(https?:\/\/(?:www\.)?zepto\.com\/pn\/[^\s\?]+)", url)
        if match and re.match(zepto_pdp_pattern, match.group(1)):
            return {"is_pdp": True, "url": match.group(1)}
            
    if "blinkit.com" in url:
        match = re.search(r"(https?:\/\/(?:www\.)?blinkit\.com\/prn\/[^\s\?]+)", url)
        if match and re.match(blinkit_pdp_pattern, match.group(1)):
            return {"is_pdp": True, "url": match.group(1)}

    return {"is_pdp": False, "url": url}
