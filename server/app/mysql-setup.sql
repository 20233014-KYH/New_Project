-- MySQL에 이 서버용 DB와 계정을 한 번 만든다. (root로 실행)
--   "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < mysql-setup.sql
-- 아래 '여기에_비밀번호' 를 원하는 비밀번호로 바꾼 뒤 실행하고, 그 비밀번호는 커밋하지 마세요(이 파일을 되돌려 두기).
CREATE DATABASE IF NOT EXISTS inventory DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'inventory'@'localhost' IDENTIFIED BY '여기에_비밀번호';
GRANT ALL PRIVILEGES ON inventory.* TO 'inventory'@'localhost';
FLUSH PRIVILEGES;
