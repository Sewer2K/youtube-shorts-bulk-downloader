import json

def convert_json_to_netscape(json_file, output_file):
    with open(json_file, 'r') as f:
        cookies = json.load(f)

    with open(output_file, 'w') as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies:
            f.write("\t".join([
                cookie.get('domain', ''),
                'TRUE' if not cookie.get('hostOnly', False) else 'FALSE',
                cookie.get('path', '/'),
                'TRUE' if cookie.get('secure', False) else 'FALSE',
                str(int(cookie.get('expirationDate', 0))),
                cookie.get('name', ''),
                cookie.get('value', '')
            ]) + "\n")

    print(f"Cookies converted and saved to {output_file}")

# Save the JSON cookies in 'cookies.json'
# Run the script to convert them to 'cookies.txt'
convert_json_to_netscape('cookies.json', 'cookies.txt')
