from Resources import app
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#TODO: Change this so it works alsoe within container
#context.load_cert_chain('/righten/cert.pem', '/righten/key.pem')
context.load_cert_chain('E:\Projects\Git\Righten\Sources\Web\cert.pem', 'E:\Projects\Git\Righten\Sources\Web\key.pem')

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, ssl_context=context)
    #app.run(ssl_context=context)