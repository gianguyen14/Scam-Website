import math
import re
import urllib.parse

SUSPICIOUS_TLDS = {'.xyz', '.top', '.club', '.stream', '.gq', '.ml', '.cf', '.tk', '.ga', '.zip', '.mov'}
SUSPICIOUS_KEYWORDS = {'login', 'verify', 'secure', 'account', 'wallet', 'bank', 'update', 'auth', 'support'}

def string_entropy(s: str) -> float:
    if not s:
        return 0.0
    p = dict()
    for c in s:
        p[c] = p.get(c, 0) + 1
    entropy = 0.0
    for count in p.values():
        freq = count / len(s)
        entropy -= freq * math.log2(freq)
    return entropy

def extract_url_features(url: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    
    # Handle cases where protocol might be missing
    if not parsed.netloc:
        if '://' not in url:
            url = 'http://' + url
            parsed = urllib.parse.urlparse(url)

    hostname = parsed.hostname or ''
    path = parsed.path or ''
    query = parsed.query or ''
    
    subdomains = hostname.split('.')[:-2] if len(hostname.split('.')) > 2 else []
    
    features = {
        'url_length': len(url),
        'hostname_length': len(hostname),
        'path_length': len(path),
        'num_dots': url.count('.'),
        'num_subdomains': len(subdomains),
        'num_digits': sum(c.isdigit() for c in url),
        'is_ip_address': 1 if re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', hostname) else 0,
        'has_punycode': 1 if 'xn--' in hostname else 0,
        'has_https': 1 if parsed.scheme == 'https' else 0,
        'has_explicit_port': 1 if parsed.port else 0,
        'has_shortener': 1 if hostname in {'bit.ly', 'goo.gl', 't.co', 'tinyurl.com'} else 0,
    }
    
    features['digit_ratio'] = features['num_digits'] / len(url) if len(url) > 0 else 0
    features['special_char_ratio'] = sum(not c.isalnum() for c in url) / len(url) if len(url) > 0 else 0
    features['entropy'] = string_entropy(url)
    
    features['suspicious_tld'] = 1 if any(hostname.endswith(tld) for tld in SUSPICIOUS_TLDS) else 0
    
    # Keyword features
    for kw in SUSPICIOUS_KEYWORDS:
        features[f'has_kw_{kw}'] = 1 if kw in url.lower() else 0
        
    return features
