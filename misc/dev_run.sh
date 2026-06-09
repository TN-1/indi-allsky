#!/bin/bash

# Lightweight UI Dev Server Setup
VENV_DIR=".venv_ui"
CONF_FILE="local_dev.json"
DB_FILE="local_dev.db"

# 0. Cleanup old dev files for a fresh start
echo "Cleaning up old dev environment..."
rm -f "$CONF_FILE" "$DB_FILE"

# 0.5. Start Tailwind CSS Watcher
echo "Checking frontend dependencies..."

if [ ! -d "node_modules/tailwindcss" ]; then
    echo "Installing frontend dependencies (this may take a moment)..."
    npm install tailwindcss daisyui @tailwindcss/cli
fi

# Add a small buffer check: Wait until the tailwind package is actually present
until [ -d "node_modules/tailwindcss" ]; do
  echo "Waiting for npm installation to finalize..."
  sleep 1
done

echo "Render Tailwind CSS"
npx @tailwindcss/cli -i ./indi_allsky/flask/static/css/app.css -o ./indi_allsky/flask/static/css/dist.css
echo "Starting Tailwind CSS watcher..."
npx @tailwindcss/cli -i ./indi_allsky/flask/static/css/app.css -o ./indi_allsky/flask/static/css/dist.css --watch > /dev/null 2>&1 &
TAILWIND_PID=$!

trap "kill $TAILWIND_PID" EXIT
# 1. Create virtual environment
if [ ! -f "$VENV_DIR/bin/activate" ] || ! grep -q "include-system-site-packages = true" "$VENV_DIR/pyvenv.cfg"; then
    echo "Creating (or updating) virtual environment..."
    rm -rf "$VENV_DIR"
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip

pip install \
    Flask Flask-SQLAlchemy Flask-Migrate Flask-WTF Flask-Login \
    Flask-SocketIO cryptography bcrypt requests pytz \
    passlib[argon2] prettytable simple-websocket is-safe-url psutil inotify

# 2. Create local dev config
if [ ! -f "$CONF_FILE" ]; then
    echo "Creating $CONF_FILE..."
    cat <<EOF > "$CONF_FILE"
{
    "SQLALCHEMY_DATABASE_URI" : "sqlite:///$(pwd)/local_dev.db",
    "MIGRATION_FOLDER" : "$(pwd)/migrations",
    "SECRET_KEY" : "dev-secret",
    "PASSWORD_KEY" : "dev-pass",
    "INDI_ALLSKY_DOCROOT" : "$(pwd)/html",
    "INDI_ALLSKY_IMAGE_FOLDER" : "$(pwd)/html/images",
    "LOGIN_DISABLED" : true,
    "TEMPLATES_AUTO_RELOAD" : true,
    "INDI_ALLSKY_AUTH_ALL_VIEWS" : false,
    "INDI_ALLSKY_AUTH_MEDIA_VIEWS" : false
}
EOF
fi

export INDI_ALLSKY_FLASK_CONFIG=$(pwd)/$CONF_FILE
export FLASK_APP=misc/dev_run_wrapper.py
export FLASK_ENV=development

# 3. Initialize dummy database
if [ ! -f "local_dev.db" ]; then
    echo "Initializing local dummy database..."
    python3 misc/init_dev_db.py
fi

# 4. Run the server
echo "Starting UI Dev Server on http://localhost:5000/indi-allsky/"
echo "Tailwind CSS is watching for changes..."
python3 -m flask run --host=0.0.0.0 --port=5000
