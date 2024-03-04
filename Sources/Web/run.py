import ssl

from Resources import app


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(
    app.config["CERT_FILE"],
    app.config["KEY_FILE"]
    )

if __name__=="__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=context)