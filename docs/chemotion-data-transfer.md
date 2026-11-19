# Data transfer with Shuttle (draft for the Chemotion docs)

Draft for `https://chemotion.net/docs/eln/devices/configurations/data_transfer`. Written for lab staff. Covers Shuttle 1.14.

Shuttle is a small program on a lab PC. It watches a folder and uploads new data to an intermediate storage (a WebDAV or SFTP server) from where Chemotion collects it. Alternatively it can upload to a ChemAssistentManager job (see section 8). You get a ready-made Shuttle for your lab from ShuttleBuilder.

## 1. Get your Shuttle

1. Log in to ShuttleBuilder with your Chemotion password and abbreviation.
2. In the Shuttle list create a new instance (source folder, destination server, user, password, transfer type, security options) and download it.
3. Depending on the options you get a single file or a zip. Every zip contains `INSTALL.txt` with the steps for exactly your instance (without any secrets).

## 2. Install

Installing needs administrative rights.

### Windows (64 bit and 32 bit)

1. Create the folder `C:\Program Files\Shuttle`.
2. Copy `shuttle.exe` into it (from a zip: all files except `INSTALL.txt`).
3. Download `shuttle_task.vbs` from ShuttleBuilder and copy it into the startup folder (press **Windows key + R**, type `shell:startup`, press Enter).
4. Restart the PC, or double-click `shuttle_task.vbs` once.

### Windows XP with SFTP

1. Create the folder `C:\Program Files\Shuttle`.
2. Unzip `shuttle_sftp_winxp.zip` and copy **all** files (`shuttle.exe`, `WinSCP.exe`, `WinSCP.com`, `license.txt`) into `C:\Program Files\Shuttle`. WinSCP must stay next to `shuttle.exe`.
3. Copy `shuttle_task.vbs` into the startup folder as above and restart.

SFTP on a real Windows XP machine has not been tested yet. Please test it before you rely on it.

### Linux

1. Ask your administrator to set the *Linux user* in the instance (the user whose home folder holds the working folder).
2. Create `/opt/Shuttle`, copy `shuttle` into it (from a zip: all files except `INSTALL.txt`) and make it executable (`chmod +x /opt/Shuttle/shuttle`).
3. In the Shuttle list click the **systemd unit** button of your instance and save the file as `/etc/systemd/system/shuttle.service`. If it contains `User=CHANGE_ME`, replace `CHANGE_ME` with the Linux user.
4. Run:
   ```bash
   systemctl daemon-reload
   systemctl enable --now shuttle.service
   ```

## 3. What Shuttle does

- It creates a working folder `~/shuttle/shuttle_<name>/` (Windows: `%USERPROFILE%\shuttle\shuttle_<name>\`). There you find the log `shuttle_log.txt`, the list of sent files `sent_register.json` and, for SFTP, `known_hosts`.
- **On the first start it sends every file in the source folder that is already stable (unchanged for the configured duration) once.** Expect a larger upload at first.
- Afterwards it sends new and changed files. If one file of a folder changes, the whole folder is sent again (folder, zip and tar transfer types).
- If the server cannot be reached, for example when the PC starts before the network is up, Shuttle logs the problem and tries again with increasing waits. Nothing is deleted from its working folders before the server confirmed the upload.
- **To send everything again:** stop Shuttle, delete `sent_register.json`, start Shuttle.
- If something does not work, read `shuttle_log.txt` first.

## 4. Security options

- **Self-signed WebDAV or ChemAssistent server:** enter the server certificate (PEM) in the instance. It is delivered as `server.crt` next to the executable; keep it there. If you add the certificate later, download the zip again and replace the files.
- **SFTP host key:** enter the server's fingerprint (`SHA256:...`, from WinSCP under *Session > Server/Protocol Information*, or with `ssh-keyscan -p <port> <host> | ssh-keygen -lf -`) to make Shuttle connect only to that server. Without a host key Shuttle trusts the key it sees on the first connection and stores it in `known_hosts`. If the server key changes later, Shuttle refuses to connect and logs it; if the change is intended, delete the server's line from `known_hosts` or enter the new host key.
- **Disable verification (insecure):** switches off TLS and host key checks. For tests only. The instance list marks such instances with a red badge.

## 5. Windows XP

- WebDAV and ChemAssistent: XP can only verify the server when the certificate (`server.crt`) is set; without it Shuttle does not verify and logs a warning.
- SFTP: the server's host key is required (unless verification is disabled). WinSCP must be next to `shuttle.exe`.
- ChemAssistent: XP speaks at most TLS 1.2, so the server must offer TLS 1.2, and it verifies the server only when a server certificate is given (as for WebDAV). No WinSCP is needed.

## 6. Update Shuttle

Download your Shuttle again from ShuttleBuilder, stop the running `shuttle.exe` (Linux: `systemctl stop shuttle.service`), replace the files, and start it again (restart the PC or double-click `shuttle_task.vbs`; Linux: `systemctl start shuttle.service`). Shuttle keeps its list of sent files (`sent_register.json`) across updates, so files are not sent again, except when you update from Shuttle 1.12 or older: then the first start sends every stable file in the source folder once.

## 7. Preprocess scripts

Scripts in `~/shuttle/scripts` (Windows: `%USERPROFILE%\shuttle\scripts`) run before each file is sent and get the absolute file path as their only argument. On Windows only `.exe` files run, on Linux every executable file. Hidden files and folders are ignored. If a script fails, this is logged and the file is sent anyway.

## 8. Upload to ChemAssistentManager

The transfer type *ChemAssistent job (HTTP upload)* sends each file (or each folder) to a ChemAssistentManager job by HTTP POST. **Every upload starts one run** of the job's AI agent, which gets the files as input.

1. In ChemAssistentManager create a job with the trigger **"HTTP file upload (API key)"** and create an **API key** for it. The key is shown only once, so copy it right away.
2. In ShuttleBuilder create the instance with the transfer type *ChemAssistent job (HTTP upload)*. Enter the server URL as destination and the key (starts with `cam_`) as *API key*. User, SSH host key and converter are not used.
3. Download and install the Shuttle as in section 2. Without a server certificate the download is a single executable; with a certificate it is a zip with `server.crt` and `INSTALL.txt` (no WinSCP).

How it behaves:

- **Destination:** `http://` or `https://` with a host. Without a path (or with `/`) `/api/jobs/trigger` is appended; any other path is used as the full trigger URL.
- **One run per upload:** transfer types `file` and `flat_tar` start one run per file, `zip` and `tar` one run per archive, `folder` one run per folder with all its files. Folder paths are flattened into the file names (`A/B/x.csv` becomes `A__B__x.csv`).
- **Size:** uploads larger than 100 MB are not attempted and stay local.
- **Deleting:** a file is deleted locally only after the server confirmed the upload (`202`).
- **Revoked key or disabled job:** the files stay in the working folder and the problem is logged. When the key was revoked, enter a new key in the instance, download the Shuttle again and replace the files; then the waiting files are sent.
- **Security:** `server.crt` and *insecure* work as for WebDAV. The API key is not written to the log or to `INSTALL.txt`.
