import sys
from unittest.mock import MagicMock

# This script mocks heavy scientific libraries that are not needed for UI development
# This allows the Flask app to start without having to compile/install these libraries

class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

MOCK_MODULES = [
    'astroalign', 'sep', 'cv2', 'astropy', 'astropy.io', 'astropy.wcs',
    'photutils', 'ccdproc', 'skimage', 'skimage.io', 'skimage.filters',
    'skimage.measure', 'skimage.transform', 'shapely', 'shapely.geometry',
    'simplejpeg', 'bottleneck', 'ephem', 'skyfield', 'pycurl', 'astroalign'
]

for mod_name in MOCK_MODULES:
    try:
        # Check if it already exists (e.g. from system-site-packages)
        __import__(mod_name)
    except ImportError:
        # If not found, mock it
        sys.modules[mod_name] = Mock()
