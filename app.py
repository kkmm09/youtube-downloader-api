from flask import Flask, request
import download
app = Flask(__name__)
@app.route('/', methods=['POST'])
def api(): return download.start(request.json)
