-- For MySQL / MariaDB
-- Sets data retention for session data to 90 days

SET GLOBAL event_scheduler = ON;

CREATE EVENT session_retention ON SCHEDULE EVERY 1 DAY ENABLE 
  DO 
  DELETE FROM ife_client_tokens WHERE `created_timedate` < UNIX_TIMESTAMP() - 7776000;
  



CREATE EVENT session_oauth2_token ON SCHEDULE EVERY 1 DAY ENABLE 
  DO 
  DELETE FROM oauth2_token WHERE `issued_at` < UNIX_TIMESTAMP() - 7776000;