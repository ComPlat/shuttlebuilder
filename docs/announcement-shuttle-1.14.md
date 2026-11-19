Subject: Shuttle 1.14: what changes when you update

Hello,

we are about to roll out Shuttle 1.14 (the changes started with 1.13). Please read this before you update a lab PC.

**1. Everything is uploaded once more on the first start.**
Labs that update from Shuttle 1.12 or older: on its first start the new Shuttle sends every stable file that is already in the source folder, once. Plan for the extra traffic, and expect duplicates on the server for data that was transferred before. After that only new and changed files are sent. If a file in a folder changes, the whole folder is sent again.

**2. Self-signed WebDAV servers need the certificate.**
Shuttle now verifies the server certificate. If your WebDAV server uses a self-signed or private certificate, add the certificate to your instance in ShuttleBuilder and download the zip again. It contains `server.crt`, which must stay next to the executable. Without it, uploads fail until it is set (the files wait and are sent afterwards).

**3. SFTP host keys.**
Without a host key, Shuttle trusts the server key it sees on the first connection and remembers it. If you prefer to pin the key, enter the fingerprint in the instance. If the server key changes later, Shuttle refuses to connect until you remove the old entry from `known_hosts` or enter the new host key. For Windows XP with SFTP the host key is required.

**4. Windows XP with SFTP is untested on real hardware.**
It has not been run on a real Windows XP machine yet. Please try it on one PC first and tell us the result.

**How to update**
1. In ShuttleBuilder download your Shuttle again (a zip with `INSTALL.txt`).
2. Stop the running Shuttle (Windows: end `shuttle.exe` in the Task Manager; Linux: `systemctl stop shuttle.service`).
3. Replace the files in `C:\Program Files\Shuttle` (Linux: `/opt/Shuttle`) with the new ones. Keep WinSCP and `server.crt` next to the executable.
4. Start Shuttle again (restart the PC or double-click `shuttle_task.vbs`; Linux: `systemctl start shuttle.service`).
5. Check `shuttle_log.txt` in `~/shuttle/shuttle_<name>/` (Windows: `%USERPROFILE%\shuttle\shuttle_<name>\`).

To send everything again later, stop Shuttle, delete `sent_register.json` in that folder and start Shuttle.

Best regards,
<name>
