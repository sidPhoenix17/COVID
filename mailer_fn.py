import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email import encoders
import os
import sys, traceback
import cred_config as cc
from settings import server_type,error_mailing_list


def send_exception_mail(to_list=[], cc_list=[], bcc_list=[], subject=None, message=None, mailServer=None, attach=None, from_user=None,
               reply_to=None, attach_multi=None, log=None, image=None, image_multi=None): 
    exc = sys.exc_info() 
    print('error came up')
    text_message = str(exc[0]) + str(exc[1]) + '<br><br>'+ ''.join(traceback.format_tb(exc[2])) 
    print(text_message)
    subject = 'COVIDSOS: Error in '+str(server_type)
    to_list = error_mailing_list
    mimetype_parts_dict={'html':text_message}
    if(server_type=='local'):
        print(text_message)
    else:
        send_email(to_list, cc_list, bcc_list, subject, mimetype_parts_dict, mailServer=None, attach=None, from_user=None,
                   reply_to=None, attach_multi=None, log=None, image=None, image_multi=None)
    return None
    

def send_email(to_list, cc_list, bcc_list, subject, mimetype_parts_dict, mailServer=None, attach=None, from_user=None,
               reply_to=None, attach_multi=None, log=None, image=None, image_multi=None):
    msg = MIMEMultipart()
    from_user = cc.credentials['gmail']
    msg['From'] = from_user['user']
    password = from_user['password']
    gmail_server = from_user['server']
    port = from_user['port']

    if reply_to is not None:
        msg['reply-to'] = reply_to
    msg['To'] = ",".join(to_list)
    msg['CC'] = ",".join(cc_list)
    msg['Subject'] = subject
    if mailServer is None:
        print('Non init mailServer')
        mailServer = init_mailServer(gmail_server, password, msg, port)
    'Attaching different parts of Message (eg, text, plain, html etc)'
    for parts in mimetype_parts_dict:
        attaching_part = MIMEText(mimetype_parts_dict[parts], parts)
        msg.attach(attaching_part)
    'Attaching images'
    if image is not None:
        try:
            part = MIMEImage(open(image, 'rb').read())
            part.add_header('Content-ID', '<%s>' % os.path.basename(image))
            msg.attach(part)
        except:
            pass
    'For Multiple Images'
    if image_multi is not None and len(image_multi) > 0:
        for image in image_multi:
            try:
                part = MIMEImage(open(image, 'rb').read())
                part.add_header('Content-ID', '<%s>' % os.path.basename(image))
                msg.attach(part)
                print('done')
            except:
                pass
    'Attaching the attachment'
    if attach is not None:
        try:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attach, 'rb').read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' %
                            os.path.basename(attach))
            msg.attach(part)
        except:
            pass
    'For Multiple attachments'
    if attach_multi is not None and len(attach_multi) > 0:
        for attach in attach_multi:
            try:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(open(attach, 'rb').read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"' %
                                os.path.basename(attach))
                msg.attach(part)
            except:
                pass
    '''Entire list of addresses'''
    toaddrs = to_list + cc_list + bcc_list
    try:
        mailServer.sendmail(from_user['user'], toaddrs, msg.as_string())
        print('mail send done-' + from_user['user'])
    except:
        raise
    mailServer.quit()


def init_mailServer(gmail_server,password, msg, port):
    mailServer = smtplib.SMTP(gmail_server, port)
    mailServer.starttls()
    try:
        mailServer.login(msg['From'], password)
        print('connection established')
    except Exception as e:
        print(e)
        exit(-1)
    return mailServer

    # send_email(['sanjay.garg@shadowfax.in'],[],[],'test mail',mimetype_parts_dict={'plain':'Hi this is a test mail'})
