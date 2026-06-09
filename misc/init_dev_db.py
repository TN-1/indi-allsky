import os
import sys

# Ensure the root directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mock_heavy_libs
from indi_allsky.flask import create_app, db
from indi_allsky.flask.models import IndiAllSkyDbCameraTable, IndiAllSkyDbConfigTable
from indi_allsky.config import IndiAllSkyConfig

def init_db():
    app = create_app()
    with app.app_context():
        print("Creating all tables...")
        db.create_all()
        
        # Add a dummy camera if none exists
        if not IndiAllSkyDbCameraTable.query.first():
            print("Adding dummy camera...")
            cam = IndiAllSkyDbCameraTable(
                name="Dummy Camera",
                friendlyName="Bubbles Test Camera",
                uuid="dummy-uuid",
                driver="indi_simulator_ccd",
                latitude=33.0,
                longitude=-84.0,
                elevation=300,
                nightSunAlt=-6.0,
                utc_offset=0,
                daytime_capture=True,
                daytime_capture_save=True,
                capture_pause=False,
                web_nonlocal_images=False,
                web_local_images_admin=False
            )
            db.session.add(cam)
        
        # Add a dummy config if none exists
        if not IndiAllSkyDbConfigTable.query.first():
            print("Adding dummy config...")
            from indi_allsky.config import IndiAllSkyConfigBase
            base_config = IndiAllSkyConfigBase().base_config.copy()
            
            # Application requires these to not be None for math calculations
            base_config.update({
                "LOCATION_LONGITUDE": -84.0,
                "LOCATION_LATITUDE": 33.0,
                "LOCATION_NAME": "Dev Environment",
                "TIMEZONE": "UTC"
            })
            
            conf = IndiAllSkyDbConfigTable(
                level="system",
                note="Initial dev config",
                data=base_config
            )
            db.session.add(conf)
            db.session.flush()  # Get the ID for CONFIG_ID state
            
        # Add required state entries
        from indi_allsky.flask.models import IndiAllSkyDbStateTable
        import time
        
        if not IndiAllSkyDbStateTable.query.filter_by(key="CONFIG_ID").first():
            config_entry = IndiAllSkyDbConfigTable.query.first()
            if config_entry:
                print("Adding CONFIG_ID state...")
                db.session.add(IndiAllSkyDbStateTable(key="CONFIG_ID", value=str(config_entry.id)))
        
        if not IndiAllSkyDbStateTable.query.filter_by(key="WATCHDOG").first():
            print("Adding WATCHDOG state...")
            db.session.add(IndiAllSkyDbStateTable(key="WATCHDOG", value=str(int(time.time()))))
            
        if not IndiAllSkyDbStateTable.query.filter_by(key="STATUS").first():
            print("Adding STATUS state...")
            db.session.add(IndiAllSkyDbStateTable(key="STATUS", value="1")) # 1 = Running/Idle?
            
        db.session.commit()
        print("Database initialized.")

if __name__ == "__main__":
    init_db()
