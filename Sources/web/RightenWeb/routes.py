from RightenWeb import app

@app.route("/")
def index():
    return """
    <h1> Righten WEB </h1>
    
    <p>This is a new beginning</p>
    """