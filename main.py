from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "سرور Flask روی پورت 5110 اجرا شده است!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
