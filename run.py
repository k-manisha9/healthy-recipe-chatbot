from app import create_app

print("Loading config...")
app = create_app()

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True,use_reloader=False)