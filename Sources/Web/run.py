from Resources import app, version
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
if version=="debug_local":
    context.load_cert_chain('E:\Projects\Git\Righten\Sources\Web\cert.pem', 'E:\Projects\Git\Righten\Sources\Web\key.pem') #Local project for debugging
else:
    context.load_cert_chain('/righten/cert.pem', '/righten/key.pem') #Dockerized project without debugger


if __name__=="__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=context)