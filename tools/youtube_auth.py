"""À lancer UNE fois sur ton ordinateur pour obtenir le YT_REFRESH_TOKEN.
Usage : python youtube_auth.py <client_id> <client_secret>
Ouvre un lien Google, connecte-toi avec le compte de la chaîne AVILY, accepte, et le jeton s'affiche."""
import http.server, json, sys, urllib.parse, urllib.request, webbrowser

cid, secret = sys.argv[1], sys.argv[2]
PORT = 8765
REDIRECT = f"http://localhost:{PORT}"
SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPE,
    "access_type": "offline", "prompt": "consent"})
code = {}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code["v"] = q.get("code", [None])[0]
        self.send_response(200); self.end_headers()
        self.wfile.write("C'est bon, tu peux fermer cet onglet.".encode())

    def log_message(self, *a):
        pass


print("Ouvre ce lien si le navigateur ne s'ouvre pas :\n", url)
webbrowser.open(url)
http.server.HTTPServer(("localhost", PORT), H).handle_request()
data = urllib.parse.urlencode({"code": code["v"], "client_id": cid, "client_secret": secret,
                               "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
print("\nYT_REFRESH_TOKEN =", tok["refresh_token"])
