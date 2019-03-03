import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,'var/www/flaskApp/website-icu-bouwwerken/')

from project import app as application
application.secret_key = "asgenikskuntmoeteniksdoen"
