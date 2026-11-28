"""AFROEURO Daily Hub local prototype server. Python 3.10+; no pip installs."""
import base64, hashlib, hmac, html, json, os, secrets, sqlite3, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('AFROEURO_DB',str(ROOT/'afroeuro.sqlite3')))
HOST=os.environ.get('HOST','127.0.0.1'); PORT=int(os.environ.get('PORT','8080'))
CATEGORIES={'football','jobs','headlines','sponsors'}

def connect():
    db=sqlite3.connect(DB,timeout=10)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, email TEXT UNIQUE, salt TEXT, digest TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS sessions (tokenhash TEXT PRIMARY KEY, expires INTEGER, csrf TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, description TEXT, url TEXT, created INTEGER)')
    db.commit(); return db

def pwd(password,salt): return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
def setup(email):
    import getpass
    with connect() as db:
        if db.execute('SELECT COUNT(*) FROM admins').fetchone()[0]:
            print('Admin already exists. Setup disabled.');return
        p=getpass.getpass('Choose admin password (at least 12 characters): ')
        if len(p)<12: print('Password too short.');return
        q=getpass.getpass('Confirm password: ')
        if p!=q: print('Passwords do not match.');return
        salt=secrets.token_hex(16)
        db.execute('INSERT INTO admins(email,salt,digest) VALUES (?,?,?)',(email.lower().strip(),salt,pwd(p,salt)))
        print('Admin created. Start with: python server.py')

class Handler(BaseHTTPRequestHandler):
    server_version='AfroEuroPrototype/1.0'
    def response_headers(self,status=200,kind='text/html; charset=utf-8',cookie=None):
        self.send_response(status);self.send_header('Content-Type',kind)
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data: https://a.espncdn.com https://*.supabase.co; media-src 'self' blob: https://*.supabase.co; connect-src 'self' https://api.frankfurter.dev https://open.er-api.com https://*.supabase.co wss://*.supabase.co; base-uri 'none'; form-action 'self'")
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers()
    def send(self,body,status=200,kind='text/html; charset=utf-8',cookie=None):
        self.response_headers(status,kind,cookie)
        if self.command != 'HEAD':
            self.wfile.write(body.encode() if isinstance(body,str) else body)

    def json(self,obj,status=200):self.send(json.dumps(obj),status,'application/json; charset=utf-8')
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>15000:raise ValueError('Request too large')
        return json.loads(self.rfile.read(n) or '{}')
    def session(self):
        cookie=SimpleCookie()
        try:cookie.load(self.headers.get('Cookie',''))
        except Exception:return None
        if 'afroeuro_session' not in cookie:return None
        token=cookie['afroeuro_session'].value
        if len(token)!=64:return None
        with connect() as db:
            row=db.execute('SELECT * FROM sessions WHERE tokenhash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
            return dict(row) if row else None
    def authorized(self,data):
        s=self.session()
        return bool(s and hmac.compare_digest(str(data.get('csrf','')),s['csrf']))
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path=urlparse(self.path).path

        static_files = {
            '/data.json': ('data.json', 'application/json; charset=utf-8'),
            '/community.js': ('community.js', 'application/javascript; charset=utf-8'),
            '/sitemap.xml': ('sitemap.xml', 'application/xml; charset=utf-8'),
            '/robots.txt': ('robots.txt', 'text/plain; charset=utf-8'),
                    '/favicon.PNG': ('favicon.PNG', 'image/png'),
            '/favicon.png': ('favicon.PNG', 'image/png'),
        }


        if path in static_files:
            filename, content_type = static_files[path]
            file_path = ROOT / filename
            if file_path.is_file():
                self.send(file_path.read_bytes(), 200, content_type)
            else:
                self.json({'error': 'File not found'}, 404)
            return

        if path in ('/','/index.html'):
            self.send((ROOT/'index.html').read_bytes());return
        if path=='/admin':
            self.send((ROOT/'admin.html').read_bytes());return
        if path=='/api/content':
            with connect() as db:
                entries=[dict(r) for r in db.execute('SELECT id,category,title,description,url,created FROM entries ORDER BY created DESC,id DESC LIMIT 100')]
            self.json({'entries':entries,'demo':True});return
        if path=='/api/me':
            s=self.session();self.json({'authenticated':bool(s),'csrf':s['csrf'] if s else None});return
        self.json({'error':'Not found'},404)
    def do_POST(self):
        path=urlparse(self.path).path
        try:data=self.body()
        except (ValueError,json.JSONDecodeError):self.json({'error':'Invalid request'},400);return
        if path=='/api/login':
            email=str(data.get('email','')).lower().strip();password=str(data.get('password',''))
            with connect() as db:
                row=db.execute('SELECT * FROM admins WHERE email=?',(email,)).fetchone()
                # Always perform a password hash to limit user enumeration timing.
                salt=row['salt'] if row else '00'*16
                digest=pwd(password,salt)
                if not row or not hmac.compare_digest(digest,row['digest']):
                    self.json({'error':'Invalid email or password'},401);return
                token=secrets.token_hex(32);csrf=secrets.token_hex(24)
                db.execute('INSERT INTO sessions VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),int(time.time())+8*3600,csrf))
            secure='; Secure' if self.headers.get('X-Forwarded-Proto','').lower()=='https' else ''
            self.send(json.dumps({'ok':True,'csrf':csrf}),200,'application/json',f'afroeuro_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}');return
        if path=='/api/logout':
            s=self.session()
            if s and self.authorized(data):
                with connect() as db:db.execute('DELETE FROM sessions WHERE tokenhash=?',(s['tokenhash'],))
            self.send('{"ok":true}',200,'application/json','afroeuro_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');return
        if path=='/api/entry':
            if not self.authorized(data):self.json({'error':'Unauthorized'},403);return
            category=str(data.get('category',''))
            title=str(data.get('title','')).strip()[:140]
            description=str(data.get('description','')).strip()[:500]
            url=str(data.get('url','')).strip()[:400]
            if category not in CATEGORIES or not title or len(title)<3 or (url and not url.startswith(('https://','http://'))):
                self.json({'error':'Check category, title and URL'},400);return
            with connect() as db:
                db.execute('INSERT INTO entries(category,title,description,url,created) VALUES (?,?,?,?,?)',(category,title,description,url,int(time.time())))
            self.json({'ok':True});return
        if path=='/api/delete':
            if not self.authorized(data):self.json({'error':'Unauthorized'},403);return
            try:item_id=int(data.get('id'))
            except (TypeError,ValueError):self.json({'error':'Invalid ID'},400);return
            with connect() as db:db.execute('DELETE FROM entries WHERE id=?',(item_id,))
            self.json({'ok':True});return
        self.json({'error':'Not found'},404)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='setup':setup(sys.argv[2]);sys.exit()
    with connect() as db:count=db.execute('SELECT COUNT(*) FROM admins').fetchone()[0]
    print(f'AFROEURO running at http://{HOST}:{PORT} | Admin: http://{HOST}:{PORT}/admin')
    if not count:print('FIRST: python server.py setup you@example.com (in another terminal after stopping server)')
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
