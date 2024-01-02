from Resources import app
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#context.load_cert_chain('/righten/cert.pem', '/righten/key.pem') #Dockerized project without debugger
context.load_cert_chain('E:\Projects\Git\Righten\Sources\Web\cert.pem', 'E:\Projects\Git\Righten\Sources\Web\key.pem') #Local project for debugging

if __name__=="__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=context)