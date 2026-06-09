@echo off
REM Called by Inno Setup after file extraction.
REM Creates the PostgreSQL database, user, and .env file.

SET APP_DIR=%~1
SET PGBIN=C:\Program Files\PostgreSQL\17\bin
SET DB_NAME=armsregister_db
SET DB_USER=armsregister_user
SET DB_PASS=ArmsR3g1st3r!

REM Create DB and user
"%PGBIN%\psql.exe" -U postgres -c "CREATE DATABASE %DB_NAME%;" 2>nul
"%PGBIN%\psql.exe" -U postgres -c "CREATE USER %DB_USER% WITH PASSWORD '%DB_PASS%';" 2>nul
"%PGBIN%\psql.exe" -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE %DB_NAME% TO %DB_USER%;" 2>nul
"%PGBIN%\psql.exe" -U postgres -d %DB_NAME% -c "GRANT ALL ON SCHEMA public TO %DB_USER%;" 2>nul

REM Write .env
(
  echo DATABASE_URL=postgresql+psycopg://%DB_USER%:%DB_PASS%@localhost:5432/%DB_NAME%
  echo SECRET_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%
  echo ALGORITHM=HS256
  echo ACCESS_TOKEN_EXPIRE_MINUTES=480
  echo TWILIO_ACCOUNT_SID=
  echo TWILIO_AUTH_TOKEN=
  echo TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
  echo PDF_STORAGE_PATH=%APP_DIR%\permits\
  echo ENVIRONMENT=production
  echo CORS_ORIGINS=http://localhost
) > "%APP_DIR%\backend\.env"

echo Database setup complete.
