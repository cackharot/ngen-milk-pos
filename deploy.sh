#!/bin/bash
(python setup.py bdist_wheel;scp dist/mpos-1.0.0-py2-none-any.whl pi@pi:~/mpos.zip; ssh pi@pi 'unzip -uoq mpos.zip'; ssh pi@pi 'chmod +x ~/mpos/web/runprod.sh'; ssh pi@pi '~/mpos/web/runprod.sh';)
