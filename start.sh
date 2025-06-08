#!/bin/bash
gunicorn whatsapp_bot.wsgi:application --bind 0.0.0.0:$PORT
