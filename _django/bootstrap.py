#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = '_django.settings'
django.setup()
