from flask import Flask, render_template
from ldap3 import Server, Connection, ALL, SUBTREE
import socket
import platform

app = Flask(__name__)

LDAP_SERVER = '127.0.0.1'
LDAP_PORT = 389
LDAP_USER = 'svc-web@eliten.local'
LDAP_PASSWORD = 'Eliten1234!'
BASE_DN = 'DC=eliten,DC=local'
USERS_OU = 'OU=Brugere,OU=Eliten,DC=eliten,DC=local'
GROUPS_OU = 'OU=Grupper,OU=Eliten,DC=eliten,DC=local'


def get_connection():
    srv = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL)
    conn = Connection(srv, LDAP_USER, LDAP_PASSWORD, auto_bind=True)
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/brugere')
def brugere():
    conn = get_connection()
    conn.search(
        search_base=USERS_OU,
        search_filter='(objectClass=user)',
        search_scope=SUBTREE,
        attributes=['cn', 'sAMAccountName', 'department', 'userAccountControl']
    )
    users = []
    for entry in conn.entries:
        aktiv = (int(entry.userAccountControl.value) & 2) == 0
        users.append({
            'navn': str(entry.cn),
            'brugernavn': str(entry.sAMAccountName),
            'afdeling': str(entry.department) if entry.department else '-',
            'aktiv': aktiv
        })
    conn.unbind()
    return render_template('brugere.html', users=users)


@app.route('/grupper')
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


@app.route('/server')
def server():
    info = {
        'hostname': socket.gethostname(),
        'ip': socket.gethostbyname(socket.gethostname()),
        'os': platform.system() + ' ' + platform.release(),
        'version': platform.version()
    }
    return render_template('server.html', info=info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)