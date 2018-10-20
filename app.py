from flask import Flask, redirect, request, url_for, render_template
import configparser
import os
# from os import path
# from pathlib import Path
import subprocess
import re
import random
from decimal import Decimal
from guldlib import *

configParser = configparser.RawConfigParser()
configFilePath = './config.ini'
configParser.read(configFilePath)
app = Flask(__name__)


userhome = str(Path.home()).replace('BLOCKTREE', 'home')

if 'GULD_HOME' in os.environ:
    GULD_HOME = os.environ['GULD_HOME']
else:
    GULD_HOME = userhome + "/"

def tigoRender(path, kwargs=None):
    if kwargs is None:
        kwargs = {}
    kwargs['prices'] = {'USD': 0, 'BTC': 0, 'DASH': 0, 'GULD': 0}
    try:
        # Assets Worth
        worthUSD = get_price('XCM')
        worthGULD = round(worthUSD / get_price('GULD'), 3)
        worthBTC = round(worthUSD / get_price('BTC'), 8)
        worthDASH = round(worthUSD / get_price('DASH'), 8)
        kwargs['prices'] = {'USD': worthUSD, 'BTC': worthBTC, 'DASH': worthDASH, 'GULD': worthGULD}
        username = kwargs['username']
        if username:
            # User Balance
            assets = get_assets_liabs(username, in_commodity="XCM")
            if assets:
                assets = assets.split()
                balXCM = Decimal(assets[0][3:])
                balGULD = balXCM * worthGULD
                balUSD = balXCM * worthUSD
                balBTC = balXCM * worthBTC
                balDASH = balXCM * worthDASH
                kwargs['bal'] = {'XCM': balXCM, 'GULD': balGULD, 'USD': balUSD, 'BTC': balBTC, 'DASH': balDASH}
            else: 
                kwargs['bal'] = {'XCM': 0, 'GULD': 0, 'USD': 0, 'BTC': 0, 'DASH': 0}
    except Exception as e:
        print(e)
    return render_template(path, **kwargs)

@app.route('/')
def index():
    return tigoRender('index.html')

@app.route('/id/')
def identify():
    return tigoRender('identify.html')

def getAssets(commodity, address):
    # Read Balance
    ledgerBals = subprocess.check_output([
        '/usr/bin/ledger',
        '-f',
        '%sledger/%s/%s/included.dat' % (GULD_HOME, commodity, address), 
        'bal'
    ])
    if (ledgerBals):
        ledgerBals = ledgerBals.decode("utf-8").split('\n')
    for line in ledgerBals:
        if re.search(' (Assets|Payable):{0,1}\w*$', line):
            return line.replace('Assets', '').replace(commodity, '').replace(' ', '').replace('Payable', '')
    return 0

def getGuldAssets(username):
    ledgerBals = subprocess.check_output([
        '/usr/bin/ledger',
        '-f',
        '%sledger/guld/%s/included.dat' % (GULD_HOME, username),
        'bal'
    ])
    if (ledgerBals):
        ledgerBals = ledgerBals.split('\n')
    user = ''
    tigos = 0
    users = 0
    for line in ledgerBals:
        if 'tigoctm' in line:
            user = 'tigoctm'
        elif username in line:
            user = username
        if re.search(' (Assets|Payable):{0,1}\w*$', line):
            amount = Decimal(line.replace('Assets', '').replace('guld', '').replace(' ', '').replace('Payable', ''))
            if user == 'tigoctm':
                tigos = amount
            elif user == username:
                users = amount
    return tigos, users

def getAddresses(username, side='deposit'):
    # Check transfer side
    if side == 'deposit':
        search = ';tigoctm:%s' % username
    else:
        search = ';%s:tigoctm' % username
    grep = ""
    try:
        # Find user addresses
        grep = subprocess.check_output([
            'grep',
            '-r',
            search,
            '%sledger/' % GULD_HOME
        ])
    except subprocess.CalledProcessError as cpe:
        print(cpe)
    if (grep):
        grep = grep.decode("utf-8").split('\n')
    addys = {}
    for line in grep:
        if len(line) == 0:
            break
        # Break addresses
        line = line.replace('%sledger/' % GULD_HOME, '').split('/')
        assets = Decimal(getAssets(line[0], line[1]))
        if (line[0] in addys):
            addys[line[0]][line[1]] = assets
            addys[line[0]]['sub-total'] = addys[line[0]]['sub-total'] + assets
        else:
            addys[line[0]] = {line[1]: assets, 'sub-total': assets}
#    if os.path.exists('%sledger/guld/%s' % (GULD_HOME, username)):
#        gassets = getGuldAssets(username)
#        if side == 'deposit':
#            addys['guld'] = { username: gassets[0] }
#        else:
#            addys['guld'] = { username: gassets[1] }

    return addys

def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == os.errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

@app.route('/id/<username>')
def identity(username=None):
    if (username):
        depAddys = getAddresses(username)
        withAddys = getAddresses(username, 'withdraw')
        return tigoRender('identity.html', {'username':username, 'depositAddresses':depAddys, 'withdrawAddresses':withAddys})
    return tigoRender('identify.html')

@app.route('/id/<username>/<faddress>')
def register(username, faddress):
    mkdirp('%speople/%s/' % (GULD_HOME, username))
    if re.match('-----BEGIN PGP PUBLIC KEY BLOCK-----[a-zA-Z1-9 :]*-----END PGP PUBLIC KEY BLOCK-----', faddress):
        imp = subprocess.Popen([
            'gpg2',
            '--import',
        ], stdin=subprocess.PIPE)
        if (imp == 0):
            imp = subprocess.check_output([
                'gpg2',
                '--fingerprint',
                '--with-colons'
            ])
            for line in imp.split('\n'):
                if line.startsWith('fpr'):
                    mkdirp('%skeys/pgp/%s/' % (GULD_HOME, username))
                    imp = subprocess.Popen([
                        'gpg2',
                        '--export',
                        '-a',
                        '>',
                        '%skeys/pgp/%s/%s.asc' % (GULD_HOME, username, re.search('\w{4,41}', line).group(0))
                    ])
    elif re.match('0x\w{10,40}', faddress):
        if not os.path.exists('%sledger/XCM/%s/included.dat' % (GULD_HOME, faddress)):
            mkdirp('%sledger/XCM/%s/' % (GULD_HOME, faddress))
            ledger = open('%sledger/XCM/%s/included.dat' % (GULD_HOME, faddress), 'w')
            ledger.write(";%s:tigoctm" % username)
            ledger.close()
    return redirect(url_for('identity', username=username))

####################################################################################
# Generate address                                                                 #
#                                                                                  #
# Pick a empty address and mark it as taked                                        #
#                                                                                  #
# Asumming:                                                                        #
# - ~/ledger/<commodity>/<address>/included.data structure                         #
# - included.data file length 0 is free, ';tigoctm:<username>' content is taken    #
####################################################################################
@app.route('/address/generate/<commodity>/<username>')
def genaddress(commodity, username):
    # Getting current addresess 
    addys = getAddresses(username)
    # Check if user dont have more than 3 assigned yet of that commodity
    if commodity not in addys or len(addys[commodity]) < 3:
        # Find a free address
        imp = str(subprocess.check_output([
            'find',
            '%sledger/%s/' % (GULD_HOME, commodity),
            '-size',
            '0',
            '-name',
            'included.dat'
        ])).split('included.dat')

        print(imp)

        addysNumber = len(imp) - 1
        print(addysNumber)
        if addysNumber > 0:
            # Choose a random address
            chosen = random.randint(0, addysNumber - 1)
            imp[chosen] = imp[chosen].encode().decode().replace('%sledger/%s' % (GULD_HOME, commodity), '')
            imp[chosen] = imp[chosen].replace('\\n', '')
            imp[chosen] = imp[chosen].replace('\'', '')
            print(imp[chosen])
            found = re.search('[^/]\w*[^/]', imp[chosen]).group(0)
            print(found)
            # Mark as taken
            f = open('%sledger/%s/%s/included.dat' % (GULD_HOME, commodity, found), 'w')
            f.write(';tigoctm:%s' % username)
            f.close()
        else:
            print('No address left for %s' % commodity)
            
    return redirect(url_for('identity', username=username))

@app.route('/price/<commodity>')
def price(commodity):
    return tigoRender('price.html')

@app.route('/address/<address>')
def address(address):
    return tigoRender('address.html', {'address': address})

if __name__ == '__main__':
    app.run()
