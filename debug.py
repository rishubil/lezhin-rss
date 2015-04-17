# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=50080, debug=True)
