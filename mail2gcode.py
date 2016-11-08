#!/usr/bin/python3

import email, getpass, imaplib, os, time ,subprocess, re
import configFile

myfile = ""
mypath = configFile.download_location

def get_timestamp():
    global myfile, mypath
    timestamp = str(time.time())
    myfile= timestamp[:timestamp.find('.')]
    mypath = mypath + myfile + '/'

def check_mail():
    # connecting to the gmail imap server
    m = imaplib.IMAP4_SSL(configFile.imap_server, configFile.imap_port)
    m.login(configFile.user,configFile.pwd)
    # m.select("[Gmail]/All Mail") # here you a can choose a mail box like INBOX instead
    m.select()
    # use m.list() to get all the mailboxes

    resp, items = m.search(None, '(UNSEEN SUBJECT "' + configFile.inbound_subject + '")')
    items = items[0].split() # getting the mails id

    return items, m

def get_attachments(m, emailid):
    if not os.path.exists(mypath):
        os.mkdir(mypath)
    resp, data = m.fetch(emailid, "(RFC822)") # fetching the mail, "`(RFC822)`" means "get the whole stuff", but you can ask for headers only, etc
    email_body = data[0][1] # getting the mail content
    mail = email.message_from_bytes(email_body) # parsing the mail content to get a mail object

    #Check if any attachments at all
    if mail.get_content_maintype() != 'multipart':
        os.rmdir(mypath)
        return ""

    if str(mail["Subject"]).strip() != configFile.inbound_subject:
        m.store(emailid, '-FLAGS','\\SEEN')
        os.rmdir(mypath)
        return ""

    toaddrs = str(mail["From"])
    toaddrs = toaddrs[toaddrs.find('<')+1:toaddrs.find('>')]

    # we use walk to create a generator so we can iterate on the parts and forget about the recursive headach
    for part in mail.walk():
        # multipart are just containers, so we skip them
        if part.get_content_maintype() == 'multipart':
            continue

        # future feature, parse settings from body
        # if part.get_content_type() == "text/plain":
        #     body = part.get_payload(decode=True)

        # is this part an attachment ?
        if part.get('Content-Disposition') is None:
            continue

        filename = part.get_filename()
        if email.header.decode_header(filename)[0][1] is not None:
            filename = email.header.decode_header(filename)[0][0].decode(email.header.decode_header(filename)[0][1])
        counter = 1

        # if there is no filename, we create one with a counter to avoid duplicates
        if not filename:
            filename = 'part-%03d%s' % (counter, 'bin')
            counter += 1

        att_path = os.path.join(mypath, filename)

        #Check if its already there
        if not os.path.isfile(att_path) :
            # finally write the stuff
            fp = open(att_path, 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()

    return toaddrs

def process_attachments():

    regex_back = re.compile("(.*B\.Cu\.gbr|.*\.btl|.*\.gbl)$")
    regex_edge = re.compile("(.*Edge\.Cuts\.gbr|.*\.dm|.*\.gml|.*\.gm1)")
    regex_front = re.compile("(.*F\.Cu\.gbr|.*\.gtl)")
    regex_drill = re.compile("(.*\.drl|.*drill\.txt)")

    front = False
    back = False
    drill = False
    edge = False
    params = [configFile.location, '--output-dir='+ mypath, '--dpi=1000', '--metric=true', '--metricoutput=true', '--mirror-absolute=false', '--optimise=true', '--tile-x=1', '--tile-y=1', '--zchange=15.0000', '--zero-start=true', '--zsafe=5.0000', '--extra-passes=0', '--mill-feed=900', '--mill-speed=10000', '--offset=15.0000', '--zwork=-0.0100', '--drill-feed=1000', '--drill-side=back', '--drill-speed=10000', '--milldrill=false', '--nog81=false', '--onedrill=false', '--zdrill=-3.0000', '--bridges=2.0000', '--bridgesnum=2', '--cut-feed=450', '--cut-infeed=10.0000', '--cut-side=back', '--cut-speed=10000', '--cutter-diameter=3.0000', '--fill-outline=true', '--outline-width=0.2000', '--zbridges=-0.6000', '--zcut=-2.0000']

    onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    for archivo in onlyfiles:
        if(regex_back.match(archivo)):
            if(not back):
                back = True
                params.append("--back="+mypath+"/"+archivo)
            continue
        if(regex_edge.match(archivo)):
            if(not edge):
                edge = True
                params.append("--outline="+mypath+"/"+archivo)
            continue
        if(regex_drill.match(archivo)):
            if(not drill):
                drill = True
                params.append("--drill="+mypath+"/"+archivo)
            continue
        if(regex_front.match(archivo)):
            if(not front):
                front = True
                params.append("--front="+mypath+"/"+archivo)
            continue

    f = open(str(mypath)+'/salida.txt','w')

    subprocess.call(params, stdout = f, stderr = f)
    f.close()

def zip_files():
    zipping =["zip","-j"]
    zipping.append(str(mypath)+"/"+str(myfile)+".zip")
    onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    for archivo in onlyfiles:
        if ((".ngc" in archivo)or(".nc" in archivo)):
            zipping.append(str(mypath)+"/"+archivo)
    subprocess.call(zipping, stdout = None)

def send_mail_attachments(toaddrs):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase

    archivo = str(mypath)+"/"+str(myfile)+".zip"
    fromaddr = configFile.user
    msg = MIMEMultipart()
    msg['Subject'] = configFile.outbound_subject
    msg['From'] = fromaddr
    msg['To'] = toaddrs
    texto = configFile.message
    for linea in open(mypath+"/salida.txt",'r').readlines():
        texto = texto + linea
    texto = texto + configFile.signature
    texto = MIMEText(texto,'plain')
    msg.attach(texto)
    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(archivo, "rb").read())
    email.encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename='+archivo[archivo.rfind('/')+1:])
    msg.attach(part)

    server = smtplib.SMTP(configFile.smtp_server, configFile.smtp_port)
    server.starttls()
    server.login(configFile.user,configFile.pwd)
    server.sendmail(fromaddr, toaddrs, msg.as_string())

    server.quit()

def disconnect(m):
    m.close()
    m.logout()

def clean():
    subprocess.call(["rm","-r",str(mypath)])

def main():
    try:
        indices, m = check_mail()
        for indice in indices:
            get_timestamp()
            toaddrs = get_attachments(m, indice)
            if len(toaddrs)>0:
                process_attachments()
                zip_files()
                send_mail_attachments(toaddrs)
        disconnect(m)
    except imaplib.socket.gaierror:
        print("Error connecting to the IMAP server! It appears either you or the server are offline.")

def check_config():
    if len(configFile.user)==0:
        return False
    if len(str(configFile.imap_port))==0:
        return False
    if len(configFile.imap_server)==0:
        return False
    if len(configFile.pwd)==0:
        return False
    if len(str(configFile.smtp_port))==0:
        return False
    if len(configFile.smtp_server)==0:
        return False
    if len(configFile.inbound_subject)==0:
        return False
    if len(configFile.location)==0:
        return False
    return True

if not mypath[-1] =="/":
    mypath += "/"
if(check_config()):
    main()
else:
    print("You need to configure 'configFile.py' before using the script")
