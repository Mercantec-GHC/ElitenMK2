from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from ldap3 import Server, Connection, ALL, SUBTREE, SIMPLE, AUTO_BIND_NO_TLS
from ldap3.core.exceptions import LDAPException
import socket
import platform
import psutil
import subprocess
import json
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = 'eliten-secret-key-change-in-prod'

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Log ind for at se denne side.'


class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    return User(username)


LDAP_SERVER = '127.0.0.1'
LDAP_PORT = 389
LDAP_USER = 'svc-web@eliten.local'
LDAP_PASSWORD = 'Eliten1234!'
BASE_DN = 'DC=eliten,DC=local'
USERS_OU = 'OU=Brugere,OU=Eliten,DC=eliten,DC=local'
GROUPS_OU = 'OU=Grupper,OU=Eliten,DC=eliten,DC=local'


def filetime_to_str(ft):
    if not ft or ft == 0:
        return '-'
    unix_ts = (int(ft) - 116444736000000000) / 10000000
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).strftime('%d-%m-%Y %H:%M')


def get_connection():
    srv = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL)
    conn = Connection(srv, LDAP_USER, LDAP_PASSWORD, auto_bind=True)
    return conn


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        upn = f'{username}@eliten.local'
        try:
            srv = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL)
            conn = Connection(srv, upn, password, auto_bind=True)
            conn.unbind()
            login_user(User(username))
            return redirect(url_for('index'))
        except LDAPException:
            flash('Forkert brugernavn eller adgangskode.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/brugere')
@login_required
def brugere():
    conn = get_connection()
    conn.search(
        search_base=USERS_OU,
        search_filter='(objectClass=user)',
        search_scope=SUBTREE,
        attributes=['cn', 'sAMAccountName', 'department', 'userAccountControl', 'lastLogonTimestamp']
    )
    users = []
    for entry in conn.entries:
        aktiv = (int(entry.userAccountControl.value) & 2) == 0
        last_logon = filetime_to_str(entry.lastLogonTimestamp.value) if entry.lastLogonTimestamp else '-'
        users.append({
            'navn': str(entry.cn),
            'brugernavn': str(entry.sAMAccountName),
            'afdeling': str(entry.department) if entry.department else '-',
            'aktiv': aktiv,
            'sidst_logget_ind': last_logon
        })
    conn.unbind()
    return render_template('brugere.html', users=users)


@app.route('/bruger/<username>')
@login_required
def bruger_detail(username):
    conn = get_connection()
    conn.search(
        search_base=USERS_OU,
        search_filter=f'(sAMAccountName={username})',
        search_scope=SUBTREE,
        attributes=['cn', 'sAMAccountName', 'department', 'mail', 'memberOf', 'userAccountControl']
    )
    if not conn.entries:
        conn.unbind()
        return 'Bruger ikke fundet', 404
    entry = conn.entries[0]
    aktiv = (int(entry.userAccountControl.value) & 2) == 0
    groups = []
    if entry.memberOf:
        for dn in entry.memberOf.values:
            cn = dn.split(',')[0].replace('CN=', '')
            groups.append(cn)
    user = {
        'navn': str(entry.cn),
        'brugernavn': str(entry.sAMAccountName),
        'afdeling': str(entry.department) if entry.department else '-',
        'mail': str(entry.mail) if entry.mail else '-',
        'aktiv': aktiv,
        'grupper': groups
    }
    conn.unbind()
    return render_template('bruger.html', user=user)


@app.route('/grupper')
@login_required
def grupper():
    conn = get_connection()
    conn.search(
        search_base=GROUPS_OU,
        search_filter='(objectClass=group)',
        search_scope=SUBTREE,
        attributes=['cn', 'description', 'member']
    )
    groups = []
    for entry in conn.entries:
        members = []
        if entry.member:
            for m in entry.member.values:
                cn = m.split(',')[0].replace('CN=', '')
                members.append(cn)
        groups.append({
            'navn': str(entry.cn),
            'beskrivelse': str(entry.description) if entry.description else '-',
            'medlemmer': members
        })
    conn.unbind()
    return render_template('grupper.html', groups=groups)


def get_docker_containers():
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{json .}}'],
            capture_output=True, text=True, timeout=5
        )
        containers = []
        for line in result.stdout.strip().splitlines():
            if line:
                c = json.loads(line)
                containers.append({
                    'navn': c.get('Names', '-'),
                    'image': c.get('Image', '-'),
                    'status': c.get('Status', '-'),
                    'porte': c.get('Ports', '-')
                })
        return containers
    except Exception:
        return []


@app.route('/server')
@login_required
def server():
    boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    uptime_secs = int((now - boot_time).total_seconds())
    uptime_str = f'{uptime_secs // 3600}t {(uptime_secs % 3600) // 60}m'

    disk = psutil.disk_usage('/')
    info = {
        'hostname': socket.gethostname(),
        'ip': socket.gethostbyname(socket.gethostname()),
        'os': platform.system() + ' ' + platform.release(),
        'version': platform.version(),
        'cpu': psutil.cpu_percent(interval=1),
        'ram_brugt': round(psutil.virtual_memory().used / 1024 ** 3, 1),
        'ram_total': round(psutil.virtual_memory().total / 1024 ** 3, 1),
        'ram_pct': psutil.virtual_memory().percent,
        'disk_brugt': round(disk.used / 1024 ** 3, 1),
        'disk_total': round(disk.total / 1024 ** 3, 1),
        'disk_pct': disk.percent,
        'uptime': uptime_str,
        'docker': get_docker_containers()
    }
    return render_template('server.html', info=info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)