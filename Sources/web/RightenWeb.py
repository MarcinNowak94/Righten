#Preparation:
#pip3 install flask

#To run application run python <thisfilepath> command in terminal




from flask import Flask
debugmode=True



app=Flask(__name__)
@app.route("/")
def index():
    return """
    <h1> Righten WEB </h1>
    
    <p>This is a new beginning</p>
    """


if __name__=="__main__":
    app.run(debug=debugmode)