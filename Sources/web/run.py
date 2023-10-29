from RightenWeb import app
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('E:\Projects\Git\Righten\Sources\web\cert.pem', 'E:\Projects\Git\Righten\Sources\web\key.pem')

if __name__=="__main__":
    app.run(ssl_context=context)